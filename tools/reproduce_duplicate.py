
import requests
import os
import sys

URL = "http://localhost:8005/api/search"
FILE_1 = "images (24).jpg"
FILE_2 = "images (25).jpg"

def test():
    if not os.path.exists(FILE_1) or not os.path.exists(FILE_2):
        print("Error: Test files not found in current directory.")
        return

    print(f"Testing duplicate detection on {URL}...")
    print(f"Uploading:\n 1. {FILE_1}\n 2. {FILE_2}\n(These are the same person)")
    
    # We must open files in binary mode
    f1 = open(FILE_1, 'rb')
    f2 = open(FILE_2, 'rb')
    
    # Structure for FastAPI List[UploadFile]
    files = [
        ('positives', (FILE_1, f1, 'image/jpeg')),
        ('positives', (FILE_2, f2, 'image/jpeg'))
    ]
    
    try:
        print("Sending request...")
        response = requests.post(URL, files=files)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 400:
            print(f"Response Error: {response.json().get('detail')}")
            if "Same person" in str(response.text) or "Duplicate" in str(response.text):
                print("\n✅ SUCCESS: Duplicate person correctly rejected!")
                sys.exit(0)
            else:
                print("\n⚠️  Rejected (400), but message might differ from expected.")
        elif response.status_code == 200:
            print(f"Response: {response.json()}")
            print("\n❌ FAILURE: Server accepted both photos (Status 200).")
            print("This means the face verifier logic did not trigger or threshold wasn't met.")
            sys.exit(1)
        else:
            print(f"\n❓ UNEXPECTED: {response.status_code}")
            print(response.text)

    except Exception as e:
        print(f"Request failed: {e}")
    finally:
        f1.close()
        f2.close()

if __name__ == "__main__":
    test()
