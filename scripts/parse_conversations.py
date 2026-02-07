import json
import os
from typing import List, Dict, Any

# Define paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(BASE_DIR, 'backend', 'conversations.json')

def load_conversations(file_path: str) -> List[Dict[str, Any]]:
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def parse_conversations(conversations: List[Dict[str, Any]]):
    parsed_data = []

    for conv in conversations:
        messages = conv.get('conversation', [])
        history = []
        
        i = 0
        while i < len(messages):
            # Find a client sequence
            client_sequence = []
            while i < len(messages) and messages[i]['direction'] == 'in':
                client_sequence.append(messages[i]['text'])
                i += 1
            
            # If we found a client sequence, look for the following consultant sequence
            if client_sequence:
                consultant_sequence = []
                while i < len(messages) and messages[i]['direction'] == 'out':
                    consultant_sequence.append(messages[i]['text'])
                    i += 1
                
                if consultant_sequence:
                    # We have a complete interaction (Client -> Consultant)
                    # The 'history' is everything before this interaction
                    # But wait, history builds up.
                    
                    # Store this interaction
                    parsed_data.append({
                        'history': history.copy(), # All messages before this current client sequence
                        'client_input': "\n".join(client_sequence),
                        'consultant_response': "\n".join(consultant_sequence)
                    })
                    
                    # Update history for the NEXT interaction
                    # Add the client sequence and consultant sequence to history
                    for msg in client_sequence:
                         history.append(f"Client: {msg}")
                    for msg in consultant_sequence:
                         history.append(f"Consultant: {msg}")

            else:
                # If it's a consultant message without a preceding client message (e.g. start of chat initiated by consultant - rare in this dataset but possible)
                # Just add to history and move on
                 if i < len(messages) and messages[i]['direction'] == 'out':
                    # history.append(f"Consultant: {messages[i]['text']}") # Actually, usually we start with client. 
                    # Let's just skip "out" messages that don't follow "in" messages if any (shouldn't happen in this logic actually because of the inner while loop)
                    i += 1
                 elif i < len(messages): # Should be 'in' but the first loop didn't catch it?
                     i += 1 # Safety to avoid infinite loop
                     
    return parsed_data

def main():
    if not os.path.exists(DATA_FILE):
        print(f"Error: Data file not found at {DATA_FILE}")
        return

    conversations = load_conversations(DATA_FILE)
    parsed_data = parse_conversations(conversations)

    print(f"Total structured interactions found: {len(parsed_data)}")
    
    # Print a sample
    if parsed_data:
        sample = parsed_data[0]
        print("\n--- SAMPLE INTERACTION ---")
        print("HISTORY:")
        for h in sample['history']:
            print(h)
        print("\nCLIENT INPUT:")
        print(sample['client_input'])
        print("\nCONSULTANT RESPONSE (Ground Truth):")
        print(sample['consultant_response'])
        
        if len(parsed_data) > 1:
            print("\n--- SECOND SAMPLE (with history) ---")
            sample2 = parsed_data[1]
            print("HISTORY:")
            for h in sample2['history']:
                print(h)
            print("\nCLIENT INPUT:")
            print(sample2['client_input'])
            print("\nCONSULTANT RESPONSE:")
            print(sample2['consultant_response'])

if __name__ == "__main__":
    main()
