import urllib.request
import json
import time

BASE_URL = "https://self-learning-chatbot-production.up.railway.app"

def test_endpoint(endpoint, data):
    url = f"{BASE_URL}{endpoint}"
    headers = {'Content-Type': 'application/json'}
    json_data = json.dumps(data).encode('utf-8')
    
    req = urllib.request.Request(url, data=json_data, headers=headers, method='POST')
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            print(f"[SUCCESS] {endpoint}")
            # print(json.dumps(result, indent=2))
            return result
    except urllib.error.HTTPError as e:
        print(f"[ERROR] {endpoint}: {e.code} - {e.read().decode('utf-8')}")
    except Exception as e:
        print(f"[ERROR] {endpoint}: {e}")

def main():
    print("Testing endpoints...")
    time.sleep(2) # Wait for server to be fully ready

    # 1. Test /generate-reply
    print("\n--- Testing /generate-reply ---")
    payload_gen = {
        "clientSequence": "I'm American and currently in Bali. Can I apply from Indonesia?",
        "chatHistory": [
            { "role": "consultant", "message": "Hi there! Thank you for reaching out. The DTV is perfect for remote workers like yourself. May I know your nationality and which country you'd like to apply from?" },
            { "role": "client", "message": "Hello, I'm interested in the DTV visa for Thailand. I work remotely as a software developer for a US company." }
        ]
    }
    res_gen = test_endpoint("/generate-reply", payload_gen)
    if res_gen and "aiReply" in res_gen:
        print(f"aiReply: {res_gen['aiReply'][:50]}...")
    else:
        print("Failed to get aiReply")

    # 2. Test /improve-ai
    print("\n--- Testing /improve-ai ---")
    payload_improve = {
        "clientSequence": "I'm American and currently in Bali. Can I apply from Indonesia?",
        "chatHistory": [
             { "role": "consultant", "message": "Hi there! Thank you for reaching out..." }
        ],
        "consultantReply": "Yes, absolutely! You can apply at the Thai Embassy in Jakarta. I'd recommend scheduling an appointment soon as slots fill up quickly."
    }
    res_improve = test_endpoint("/improve-ai", payload_improve)
    if res_improve:
        if "updatedPrompt" in res_improve:
             print(f"updatedPrompt length: {len(res_improve['updatedPrompt'])}")
        elif "error" in res_improve:
             print(f"Error in improve-ai: {res_improve['error']}")
        else:
             print("Unknown response structure")

    # 3. Test /improve-ai-manually
    print("\n--- Testing /improve-ai-manually ---")
    payload_manual = {
        "instructions": "Be more concise. Always mention appointment booking proactively."
    }
    res_manual = test_endpoint("/improve-ai-manually", payload_manual)
    if res_manual and "updatedPrompt" in res_manual:
        print(f"updatedPrompt length: {len(res_manual['updatedPrompt'])}")
    else:
        print("Failed manual improvement")

if __name__ == "__main__":
    main()
