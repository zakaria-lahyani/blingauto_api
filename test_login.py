#!/usr/bin/env python
"""Simple login test script."""

import json
import urllib.request

url = "http://localhost:8000/api/v1/auth/login"
data = json.dumps({
    "email": "admin@blingauto.com",
    "password": "AdminDev123!"
}).encode('utf-8')

headers = {
    'Content-Type': 'application/json',
}

req = urllib.request.Request(url, data=data, headers=headers, method='POST')

try:
    with urllib.request.urlopen(req) as response:
        print(f"Status: {response.status}")
        result = json.loads(response.read().decode('utf-8'))
        print(json.dumps(result, indent=2))
except urllib.error.HTTPError as e:
    print(f"Error Status: {e.code}")
    print(e.read().decode('utf-8'))
