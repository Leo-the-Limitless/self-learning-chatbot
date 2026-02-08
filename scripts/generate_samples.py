import os
import json
import random
import sys
from groq import Groq
from dotenv import load_dotenv

# Ensure backend directory is in path for imports
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend'))

# Load environment variables explicitly to ensure they are available for app imports
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend', '.env'))

try:
    from app import get_latest_prompt, INITIAL_SYSTEM_PROMPT
    from utils import load_data
except ImportError as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)

# Initialize Groq client
client = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),
)

def generate_ai_reply(history, client_input):
    # Fetch the latest prompt from DB (or fallback to initial if db fails/empty)
    # Using get_latest_prompt() is better than INITIAL_SYSTEM_PROMPT as it respects the user's request
    # to use the database-stored prompt.
    system_prompt = get_latest_prompt()
    
    messages = [{"role": "system", "content": system_prompt}]
    
    # Parse history strings into message objects
    # load_data returns history strings like "Client: ..." and "Consultant: ..."
    formatted_history = []
    
    # The 'history' argument passed here is a list of strings from parsed_data
    # e.g., ["Client: Hello", "Consultant: Hi", ...]
    
    for h in history:
        if h.startswith("Client: "):
            content = h[8:].strip() # Remove prefix
            formatted_history.append({"role": "user", "content": content})
        elif h.startswith("Consultant: "):
            content = h[12:].strip() # Remove prefix
            formatted_history.append({"role": "assistant", "content": content})
    
    # Add formatted history to messages
    messages.extend(formatted_history)
    
    # Add the current client input
    messages.append({"role": "user", "content": client_input})

    # CRITICAL: Groq/OpenAI API requires the word "json" to be present in messages 
    # when response_format is set to json_object.
    messages.append({"role": "system", "content": "IMPORTANT: You must respond in JSON format."})

    try:
        completion = client.chat.completions.create(
            model=os.environ.get("MODEL_NAME", "llama-3.1-8b-instant"),
            messages=messages,
            temperature=0.7,
            max_tokens=500,
            response_format={"type": "json_object"}
        )
        response_content = completion.choices[0].message.content
        
        # Try to parse JSON to return clean text if possible
        try:
            json_response = json.loads(response_content)
            if "reply" in json_response:
                return f"[JSON Parsed] {json_response['reply']}"
            else:
                return response_content
        except json.JSONDecodeError:
            return response_content

    except Exception as e:
        return f"Error: {str(e)}"

def main():
    print("Loading data...")
    data = load_data()
    if not data:
        print("No data found.")
        return

    print(f"Found {len(data)} interactions. Selecting 3 random samples...")
    samples = random.sample(data, min(3, len(data)))

    for i, sample in enumerate(samples):
        print(f"\n{'='*50}")
        print(f"SAMPLE {i+1}")
        print(f"{'='*50}")
        
        print("\n[HISTORY (Raw Strings)]")
        # Print only last 3 history items to save space
        history_preview = sample['history'][-3:] if len(sample['history']) > 3 else sample['history']
        if len(sample['history']) > 3:
            print("... (earlier history hidden) ...")
        for h in history_preview:
            print(h)
            
        print("\n[CLIENT INPUT]")
        print(sample['client_input'])
        
        print("\n[GROUND TRUTH (CONSULTANT)]")
        print(sample['consultant_response'])
        
        print("\n[AI REPLY (Generated)]")
        ai_reply = generate_ai_reply(sample['history'], sample['client_input'])
        print(ai_reply)

if __name__ == "__main__":
    main()
