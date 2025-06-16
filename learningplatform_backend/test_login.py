#!/usr/bin/env python3
import json
import sys
import urllib.parse
import urllib.request


import pytest


def _test_endpoint(url, method="GET", data=None, headers=None):
    """Test any endpoint and return the response"""
    if headers is None:
        headers = {}
    print(f"Testing endpoint: {url} with method: {method}")
    if data and isinstance(data, dict):
        data = json.dumps(data).encode("utf-8")
        if "Content-Type" not in headers:
            headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as response:
            content = response.read().decode("utf-8")
            print(f"Success! Status: {response.status}")
            return content
    except urllib.error.HTTPError as e:
        print(f"Failed with status code: {e.code}")
        content = e.read().decode("utf-8")
        print(f"Response content: {content}")
        return None
    except urllib.error.URLError as e:
        print(f"Connection failed: {e.reason}")
        return None


@pytest.mark.parametrize(
    "username,password",
    [
        ("student", "student123"),
        ("instructor", "instructor123"),
    ],
)
def test_login(username, password):
    """Test login endpoints with known credentials and assert access token is returned."""
    credentials = {"username": username, "password": password}

    # Only test the valid login endpoint(s) as per OpenAPI and user feedback
    endpoints = [
        "http://localhost:8000/auth/login/",
        "http://localhost:8000/auth/token/refresh/",  # Not for login, but included for completeness
        "http://localhost:8000/auth/logout/",  # Not for login, but included for completeness
        "http://localhost:8000/auth/register/",  # Not for login, but included for completeness
        "http://localhost:8000/auth/validate-token/",  # Not for login, but included for completeness
    ]
    for endpoint in endpoints:
        print(f"\nAttempting login at: {endpoint}")
        if endpoint.endswith("/auth/login/"):
            response = _test_endpoint(endpoint, "POST", credentials)
        else:
            # Only /auth/login/ is a login endpoint; skip POST for others
            continue
        if response:
            try:
                result = json.loads(response)
                print("Login successful!")
                print(f"Response data: {json.dumps(result, indent=2)[:200]}...")
                if "access" in result:
                    print(f"Access token: {result.get('access', 'N/A')[:20]}...")
                    assert result["access"], "No access token returned"
                    return
                elif "token" in result:
                    print(f"Token: {result.get('token', 'N/A')[:20]}...")
                    assert result["token"], "No token returned"
                    return
            except json.JSONDecodeError:
                print("Received non-JSON response.")
    pytest.fail("Login failed for all endpoints with provided credentials")


def check_health():
    """Test the health endpoint"""
    print("\nChecking server health endpoint...")
    response = _test_endpoint("http://localhost:8000/health/")
    if response:
        try:
            result = json.loads(response)
            print(f"Health check successful: {json.dumps(result, indent=2)}")
            return True
        except json.JSONDecodeError:
            print("Received non-JSON response from health endpoint.")
    return False


def check_api_root():
    """Test the API root to discover available endpoints"""
    print("\nChecking API root...")
    response = _test_endpoint("http://localhost:8000/api/v1/")
    if response:
        try:
            result = json.loads(response)
            print(f"API root response: {json.dumps(result, indent=2)}")
            return True
        except json.JSONDecodeError:
            print("Received non-JSON response from API root.")
    return False


if __name__ == "__main__":
    username = "admin"
    password = "adminpassword"

    if len(sys.argv) > 2:
        username = sys.argv[1]
        password = sys.argv[2]

    print(f"Testing login with username: {username}, password: {password}")

    # First check health and API endpoints to confirm server is running
    check_health()
    check_api_root()

    # Try login
    test_login(username, password)
