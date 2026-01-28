import json
import sys
from pathlib import Path

def analyze_metadata(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error loading file: {e}")
        return

    count = len(data)
    print(f"Total records processed: {count}")

    if count == 0:
        print("Dataset is empty.")
        return

    # Check first item for structure
    sample = data[0]
    required_sections = ["basic", "face", "hair", "extra", "vibe"]
    
    missing_sections = []
    for section in required_sections:
        if section not in sample:
            missing_sections.append(section)
            
    if missing_sections:
        print(f"WARNING: Initial sample is missing sections: {missing_sections}")
    else:
        print("\nStructure Check (Sample):")
        for section in required_sections:
            print(f"  - {section}: {list(sample[section].keys())}")

    # Check completeness across all items
    incomplete_count = 0
    for item in data:
        if not all(k in item for k in required_sections):
            incomplete_count += 1
            
    if incomplete_count > 0:
        print(f"\nWARNING: {incomplete_count} items have missing sections.")
    else:
        print(f"\nAll {count} items have all top-level sections ({', '.join(required_sections)}).")

if __name__ == "__main__":
    analyze_metadata("data/wiki_1000_metadata.json")
