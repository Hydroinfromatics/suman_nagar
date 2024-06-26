import requests
import time

credentials = {
    "username": "Kamlesh123",
    "password": "1234567"
}

headers = {
        "Content-Type": "application/json"
    }

def generate_token(api_url):
    response = requests.post(api_url + "/get_token", json=credentials, headers=headers)
    
    if response.status_code == 200:
        token = response.json().get("token")
        # expiry_time = response.json().get("expiry_time")  # Assuming this field exists in the API response
        return token
    else:
        print(f"Failed to generate token: {response.content}")
        return None

def fetch_data_from_api(api_url):
    token = generate_token(api_url)  # Adjust the endpoint accordingly
    
    if not token:
        return None
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    response = requests.get(api_url + "/suman_nagar_data", headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch data: {response.content}")
        return None         
