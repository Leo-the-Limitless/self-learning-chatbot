import os
import json

def load_data():
    """
    Loads conversation data from backend/conversations.json.
    Returns a list of dictionary objects with keys: history, client_input, consultant_response.
    """
    # Assuming scripts/utils.py is the location, backend is one level up
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_file = os.path.join(base_dir, 'backend', 'conversations.json')
    
    if not os.path.exists(data_file):
        print(f"Data file not found: {data_file}")
        return []
        
    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            conversations = json.load(f)
    except Exception as e:
        print(f"Error reading data file: {e}")
        return []
    
    parsed_data = []
    for conv in conversations:
        messages = conv.get('conversation', [])
        history = []
        i = 0
        while i < len(messages):
            client_sequence = []
            while i < len(messages) and messages[i]['direction'] == 'in':
                client_sequence.append(messages[i]['text'])
                i += 1
            
            if client_sequence:
                consultant_sequence = []
                while i < len(messages) and messages[i]['direction'] == 'out':
                    consultant_sequence.append(messages[i]['text'])
                    i += 1
                
                if consultant_sequence:
                    parsed_data.append({
                        'history': history.copy(),
                        'client_input': "\n".join(client_sequence),
                        'consultant_response': "\n".join(consultant_sequence)
                    })
                    for msg in client_sequence:
                         history.append(f"Client: {msg}")
                    for msg in consultant_sequence:
                         history.append(f"Consultant: {msg}")
            else:
                 i += 1
    return parsed_data
