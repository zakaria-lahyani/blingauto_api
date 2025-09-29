from tests.auth.user_data import test_users
import requests

data = test_users



def make_request( method: str, endpoint: str, headers, **kwargs) -> requests.Response:
    """Make HTTP request"""
    BASE_URL = "http://localhost:8000"

    url = f"{BASE_URL}{endpoint}"
    return requests.request(method, url, headers=headers, **kwargs)

for user_type, user_data in data.items():
    print(user_type)
    response = make_request("POST", "/auth/register", headers="", json=user_data)
    print(response)

    response = make_request("POST", "/auth/login", headers="", json={
                    "email": user_data["email"],
                    "password": user_data["password"]
                })
    print(response.json())
