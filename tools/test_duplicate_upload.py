import requests
import os
import sys

def test_duplicate_upload_in_same_request():
    # Use 8005 because docker-compose maps 8005 -> 8000
    base_url = "http://127.0.0.1:8005"
    
    # 1. Check connectivity
    try:
        r = requests.get(f"{base_url}/api/health")
        print(f"Health Check: {r.status_code} {r.text}")
    except Exception as e:
        print(f"Server not reachable: {e}")
        return

    url = f"{base_url}/api/search"
    
    # Use any valid image from the dataset
    image_path = "data/raw_1000/10049200_1891-09-16_1958.jpg"
    
    if not os.path.exists(image_path):
        print(f"Error: {image_path} does not exist.")
        return

    print("Attempting to upload the same photo twice in 'positives' list...")
    
    files = [
        ('positives', ('photo1.jpg', open(image_path, 'rb'), 'image/jpeg')),
        ('positives', ('photo2_duplicate.jpg', open(image_path, 'rb'), 'image/jpeg'))
    ]
    
    try:
        response = requests.post(url, files=files)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 400 and "Duplicate" in response.text:
            print("\n✅ SUCCESS: Duplicate detected and rejected as expected.")
        elif response.status_code == 200:
            print("\n❌ FAILED: Server accepted duplicates (Status 200).")
        else:
            print(f"\n⚠️ UNEXPECTED: Status {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("\n❌ FAILED: Could not connect to server.")

if __name__ == "__main__":
    test_duplicate_upload_in_same_request()
