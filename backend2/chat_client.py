# chat_client.py
import requests
import json

def chat(user_id: str, session_id: str):
    base = "http://localhost:8000"
    print("API chat client. Type your messages (exit to quit).")
    while True:
        msg = input("> ")
        if msg.lower() in ("exit", "quit"):
            break
        resp = requests.post(
            f"{base}/chat/{user_id}/{session_id}",
            json={"message": msg}
        )
        if resp.status_code != 200:
            print("Error:", resp.text)
            continue
        data = resp.json()
        print(f"AI: {data['response']}\n(intervention: {data['intervention']})\n")

if __name__ == "__main__":
    import sys
    uid = sys.argv[1] if len(sys.argv) > 1 else "test-user-id"
    sid = sys.argv[2] if len(sys.argv) > 2 else "test-session-id"
    chat(uid, sid)
