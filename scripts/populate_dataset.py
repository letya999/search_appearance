import os
import sys
import tarfile
import urllib.request
import shutil
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path to import mvp modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables from .env if it exists
load_dotenv()

from mvp.annotator.batch_process import process_folder

DATA_URL = "https://data.vision.ee.ethz.ch/cvl/rrothe/imdb-wiki/static/wiki_crop.tar"
DATA_DIR = Path("data")
RAW_IMAGES_DIR = DATA_DIR / "raw_1000"
METADATA_FILE = DATA_DIR / "wiki_1000_metadata.json"

def download_and_extract_subset(target_count=1000):
    DATA_DIR.mkdir(exist_ok=True)
    RAW_IMAGES_DIR.mkdir(exist_ok=True)
    
    tar_path = DATA_DIR / "wiki_crop.tar"
    
    # 1. Download if not exists
    if not tar_path.exists():
        print(f"Downloading {DATA_URL}...")
        try:
            with urllib.request.urlopen(DATA_URL) as response, open(tar_path, 'wb') as out_file:
                shutil.copyfileobj(response, out_file)
            print("Download complete.")
        except Exception as e:
            print(f"Error downloading file: {e}")
            return False
    else:
        print("Archive already exists, skipping download.")

    # 2. Extract specific number of images
    existing_images = list(RAW_IMAGES_DIR.glob("*.jpg"))
    if len(existing_images) >= target_count:
        print(f"Found {len(existing_images)} existing images. Skipping extra extraction steps to save time.")
        return True

    print(f"Extracting up to {target_count} images...")
    count = len(existing_images)
    
    try:
        with tarfile.open(tar_path, 'r:') as tar:
            for member in tar:
                if count >= target_count:
                    break
                
                if member.isfile() and member.name.lower().endswith(('.jpg', '.jpeg', '.png')):
                    # Check if it looks like a face image (file size > 0)
                    if member.size > 0:
                        file_name = os.path.basename(member.name)
                        # Avoid duplicates if restarting
                        target_path = RAW_IMAGES_DIR / file_name
                        if not target_path.exists():
                            file_obj = tar.extractfile(member)
                            with open(target_path, 'wb') as f:
                                shutil.copyfileobj(file_obj, f)
                            count += 1
                            if count % 100 == 0:
                                print(f"Extracted {count}/{target_count}...")
    except Exception as e:
        print(f"Error during extraction: {e}")
        return False
        
    print(f"Extraction complete. {len(list(RAW_IMAGES_DIR.glob('*.jpg')))} images ready.")
    return True

def main():
    parser = argparse.ArgumentParser(description="Populate and annotate dataset.")
    parser.add_argument("--api-key", help="OpenRouter/OpenAI API Key for VLM")
    parser.add_argument("--limit", type=int, default=1000, help="Number of images to process")
    parser.add_argument("--skip-download", action="store_true", help="Skip download/extract phase")
    args = parser.parse_args()

    # 1. Resolve API Key
    api_key = args.api_key or os.environ.get("VLM_API_KEY") or os.environ.get("OPENAI_API_KEY")
    
    if not api_key:
        print("\n" + "="*60)
        print("ERROR: API Key is missing!")
        print("To annotate images, we need an API Key for the VLM (Visual Language Model).")
        print("You can provide it in two ways:")
        print("1. Pass it as an argument: python populate_dataset.py --api-key YOUR_KEY_HERE")
        print("2. Set env variable: $env:VLM_API_KEY='YOUR_KEY_HERE'")
        print("   (Or OPENAI_API_KEY)")
        print("="*60 + "\n")
        sys.exit(1)

    # 2. Data Preparation
    if not args.skip_download:
        success = download_and_extract_subset(args.limit)
        if not success:
            print("Failed to prepare data. Aborting.")
            sys.exit(1)
    
    # 3. Process with VLM
    print(f"Starting VLM annotation for {args.limit} images...")
    print(f"Metadata will be saved to: {METADATA_FILE}")
    
    try:
        process_folder(str(RAW_IMAGES_DIR), str(METADATA_FILE), api_key=api_key)
        print("\nProcessing complete!")
    except Exception as e:
        print(f"\nError during processing: {e}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
    except Exception as e:
        print(f"Fatal error: {e}")
