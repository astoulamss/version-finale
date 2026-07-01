import requests
import json

base_url = "http://localhost:8000"
email = "jean@example.com"
password = "YDAYS2026!"

def test():
    print(f"Logging in as {email}...")
    # Login
    resp = requests.post(f"{base_url}/api/auth/login", json={"email": email, "mots_de_passe": password})
    if resp.status_code != 200:
        print(f"Login failed: {resp.text}")
        return
    token = resp.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    print("Login successful.")

    # Test Chatbot
    print("\nTesting Chatbot API...")
    try:
        chat_resp = requests.post(
            f"{base_url}/api/chatbot/chat",
            json={"message": "Bonjour, je veux poser un congé", "conversation_id": None},
            headers=headers
        )
        print(f"Chatbot Status: {chat_resp.status_code}")
        print(f"Chatbot Response: {chat_resp.text}")
    except Exception as e:
        print(f"Chatbot Error: {e}")

    # Test GET Leaves
    print("\nTesting GET Leaves API...")
    try:
        leave_resp = requests.get(
            f"{base_url}/api/leaves/my",
            headers=headers
        )
        print(f"Leaves GET Status: {leave_resp.status_code}")
        print(f"Leaves GET Response: {leave_resp.text[:500]}...")
    except Exception as e:
        print(f"Leaves Error: {e}")
        
    # Test POST Leave
    print("\nTesting POST Leave API...")
    try:
        post_leave = requests.post(
            f"{base_url}/api/leaves/",
            json={"leave_type_id": 1, "start_date": "2026-07-01", "end_date": "2026-07-05", "reason": "Test bug hunt"},
            headers=headers
        )
        print(f"Leaves POST Status: {post_leave.status_code}")
        print(f"Leaves POST Response: {post_leave.text}")
    except Exception as e:
        print(f"Leaves POST Error: {e}")

if __name__ == "__main__":
    test()
