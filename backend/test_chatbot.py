import requests

base_url = "http://localhost:8000"
email = "jean@example.com"
password = "YDAYS2026!"

def test():
    # Login
    resp = requests.post(f"{base_url}/api/auth/login", json={"email": email, "mots_de_passe": password})
    if resp.status_code != 200:
        print(f"Login failed: {resp.text}")
        return
    token = resp.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create conversation
    print("\nCreating Chatbot Conversation...")
    conv_resp = requests.post(f"{base_url}/api/chatbot/conversations", json={"title": "Test Bug Hunt"}, headers=headers)
    print(f"Status: {conv_resp.status_code}")
    print(f"Response: {conv_resp.text}")
    
    if conv_resp.status_code in [200, 201]:
        conv_id = conv_resp.json().get("id")
        # Send message
        print("\nSending Message...")
        msg_resp = requests.post(
            f"{base_url}/api/chatbot/conversations/{conv_id}/messages", 
            json={"message": "Bonjour, comment je pose un congé ?"}, 
            headers=headers
        )
        print(f"Status: {msg_resp.status_code}")
        print(f"Response: {msg_resp.text}")

if __name__ == "__main__":
    test()
