import requests

def get_token():
    url = "http://localhost:3000/api/auth/login"
    data = {
        "username": "psalmprax",
        "password": "ettametta_admin"
    }
    try:
        # OAuth2PasswordRequestForm expects form data
        response = requests.post(url, data=data, timeout=10)
        print(response.json())
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    get_token()
