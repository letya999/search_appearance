import os
import json
import uuid
import argparse
from pathlib import Path
from pydantic import ValidationError
from mvp.annotator.client import VLMClient
from mvp.annotator.prompts import SYSTEM_PROMPT
from mvp.schema.models import PhotoProfile

def process_file(client: VLMClient, file_path: str) -> dict:
    json_str = client.analyze_image(file_path, SYSTEM_PROMPT)
    # Clean markdown if present
    json_str = json_str.replace("```json", "").replace("```", "").strip()
    
    data = json.loads(json_str)
    
    # Add IDs and Metadata
    profile_data = {
        "id": str(uuid.uuid4()),
        "image_path": str(Path(file_path).absolute()),
        **data
    }
    
    # Validate with Pydantic
    profile = PhotoProfile(**profile_data)
    return profile.model_dump()

def process_folder(folder_path: str, output_file: str, api_key: str = None):
    client = VLMClient(api_key=api_key)
    results = []
    
    # Load existing if available
    if os.path.exists(output_file):
        try:
            with open(output_file, 'r') as f:
                results = json.load(f)
        except:
            pass
            
    processed_paths = {r['image_path'] for r in results}
    
    files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
    print(f"Found {len(files)} images in {folder_path}")
    
    for filename in files:
        file_path = str(Path(os.path.join(folder_path, filename)).absolute())
        if file_path in processed_paths:
            print(f"Skipping already processed: {filename}")
            continue
            
        print(f"Processing: {filename}...")
        try:
            profile_dict = process_file(client, file_path)
            results.append(profile_dict)
            
            # Save incrementally
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
                
        except ValidationError as e:
            print(f"Validation Error for {filename}: {e}")
        except Exception as e:
            print(f"Error processing {filename}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--folder", required=True)
    parser.add_argument("--output", default="result_metadata.json")
    args = parser.parse_args()
    
    if not os.path.exists(args.folder):
        print(f"Error: Folder {args.folder} does not exist.")
        exit(1)
        
    process_folder(args.folder, args.output)
