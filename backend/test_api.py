import requests
import base64
import json

def test_registration_api():
    """Test the registration API endpoint"""
    
    # Create a simple test image (1x1 pixel)
    import io
    from PIL import Image
    
    # Create a test image
    img = Image.new('RGB', (100, 100), color='red')
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG')
    img_data = buffer.getvalue()
    img_base64 = base64.b64encode(img_data).decode('utf-8')
    
    # Test data
    test_data = {
        "name": "John Smith",
        "email": "john.smith@company.com",
        "phone": "555-1234",
        "department": "Engineering",
        "position": "Software Developer",
        "status": "active",
        "notes": "Test registration via API",
        "face_image": f"data:image/jpeg;base64,{img_base64}"
    }
    
    try:
        print("Testing registration API...")
        response = requests.post('http://localhost:5000/api/persons', json=test_data)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Registration successful!")
            print(f"Person ID: {data.get('id')}")
            print(f"Name: {data.get('name')}")
        else:
            print("❌ Registration failed!")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to backend server!")
        print("Make sure the Flask server is running on http://localhost:5000")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_persons_list():
    """Test getting list of persons"""
    try:
        print("\nTesting persons list API...")
        response = requests.get('http://localhost:5000/api/persons')
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Persons list retrieved!")
            print(f"Total persons: {len(data)}")
            for person in data:
                print(f"  - ID: {person['id']}, Name: {person['name']}, Email: {person['email']}")
        else:
            print("❌ Failed to get persons list!")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_persons_list()
    test_registration_api()
