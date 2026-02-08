import os
import json
import random
from typing import List, Dict
from flask import Flask, request, jsonify
from flask_cors import CORS
from groq import Groq
from supabase import create_client, Client
from dotenv import load_dotenv

# Import optimization logic
from optimization import run_editor_optimization, run_manual_optimization

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app) # Enable CORS for all routes

@app.route('/health')
def health():
    return jsonify({"status": "ok"})


# Initialize Groq client
client = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),
)

# Initialize Supabase client
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# Configuration
INITIAL_SYSTEM_PROMPT = """You are an AI chatbot representing a Thailand DTV (Destination Thailand Visa) immigration consulting service. Your role is to assist clients with their DTV visa applications in a professional, empathetic, and knowledgeable manner.

## Your Goal
Generate a helpful, conversational text response for the client. Even if you are providing requirements or fees, write them as part of a natural conversation.

## CRITICAL: Output Format
You MUST respond with a JSON object. The actual message for the user MUST be in the "reply" key.
Example:
{
  "reply": "Hello! For the DTV visa, you'll need an employment contract and proof of income. Would you like me to list the specific documents?"
}
"""

# Cache the prompt locally to avoid DB hits on every chat (optional, but good practice)
current_system_prompt = INITIAL_SYSTEM_PROMPT

def get_latest_prompt():
    try:
        response = supabase.table('prompts').select('*').eq('is_active', True).order('created_at', desc=True).limit(1).execute()
        if response.data:
            return response.data[0]['prompt_text']
    except Exception as e:
        print(f"Error fetching prompt: {e}")
    return INITIAL_SYSTEM_PROMPT

# Initialize prompt on startup
current_system_prompt = get_latest_prompt()

def format_history(history_data):
    """
    Formats history (list of dicts or strings) into Groq-compatible messages.
    User format: [{"role": "consultant", "message": "..."}]
    Groq format: [{"role": "assistant", "content": "..."}]
    """
    formatted_messages = []
    if not isinstance(history_data, list):
        return formatted_messages

    for msg in history_data:
        if isinstance(msg, dict):
            role = msg.get('role', 'user')
            content = msg.get('message', msg.get('content', ''))
            
            # Map role names
            if role == 'consultant':
                role = 'assistant'
            elif role == 'client':
                role = 'user'
            
            formatted_messages.append({"role": role, "content": content})
        elif isinstance(msg, str):
            # Fallback for raw strings if any
            formatted_messages.append({"role": "user", "content": msg})
            
    return formatted_messages

def generate_reply_logic(client_sequence, history):
    # Ensure we have the latest prompt
    prompt = get_latest_prompt()
    
    messages = [{"role": "system", "content": prompt}]
    
    # Add history
    messages.extend(format_history(history))
    
    # Add current message
    messages.append({"role": "user", "content": client_sequence})

    # CRITICAL: Ensure "json" is in messages for Groq API compliance
    messages.append({"role": "system", "content": "IMPORTANT: You must respond in JSON format."})

    completion = client.chat.completions.create(
        model=os.environ.get("MODEL_NAME", "llama-3.1-8b-instant"), 
        messages=messages,
        temperature=0.7,
        max_tokens=500, 
        response_format={"type": "json_object"}
    )
    
    response_content = completion.choices[0].message.content.strip()
    try:
        json_response = json.loads(response_content)
        # Try known keys
        for key in ["reply", "response", "aiReply", "message", "text"]:
            if key in json_response:
                return str(json_response[key])
        
        # If it's a JSON but no known key, it might be the data itself
        # Stringify it nicely for the user
        return json.dumps(json_response, indent=2)
    except:
        # Fallback for plain text or malformed JSON
        return response_content

@app.route('/generate-reply', methods=['POST'])
def generate_reply():
    """
    Request:
    {
      "clientSequence": "...",
      "chatHistory": [ { "role": "consultant", "message": "..." } ]
    }
    Response:
    {
      "aiReply": "..."
    }
    """
    data = request.json
    client_sequence = data.get('clientSequence')
    history = data.get('chatHistory', [])
    
    if not client_sequence:
        return jsonify({"error": "clientSequence is required"}), 400

    try:
        ai_reply = generate_reply_logic(client_sequence, history)
        return jsonify({"aiReply": ai_reply})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/improve-ai', methods=['POST'])
def improve_ai():
    """
    Request:
    {
      "clientSequence": "...",
      "chatHistory": [...],
      "consultantReply": "..."
    }
    Response:
    {
      "predictedReply": "...",
      "updatedPrompt": "..."
    }
    """
    data = request.json
    client_sequence = data.get('clientSequence')
    history = data.get('chatHistory', [])
    consultant_reply = data.get('consultantReply')
    
    if not client_sequence or not consultant_reply:
         return jsonify({"error": "clientSequence and consultantReply are required"}), 400
    
    try:
        # 1. Get current prediction
        predicted_reply = generate_reply_logic(client_sequence, history)
        
        # 2. Run Optimization
        # Prepare sample data
        sample_data = {
            'client_input': client_sequence,
            'history': history,
            'consultant_response': consultant_reply
        }
        
        current_prompt = get_latest_prompt()
        new_prompt = run_editor_optimization(client, current_prompt, sample_data, predicted_reply)
        
        # 3. Update Database
        if new_prompt and len(new_prompt) > 20:
             supabase.table('prompts').update({'is_active': False}).eq('is_active', True).execute()
             
             data_insert = {
                'prompt_text': new_prompt,
                'is_active': True,
                'version_notes': f"Auto-improved based on: {client_sequence[:20]}..."
             }
             supabase.table('prompts').insert(data_insert).execute()
             
             return jsonify({
                 "predictedReply": predicted_reply,
                 "updatedPrompt": new_prompt
             })
        else:
             return jsonify({"error": "Optimization failed to generate a valid prompt"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/improve-ai-manually', methods=['POST'])
def improve_ai_manually():
    """
    Request:
    {
      "instructions": "..."
    }
    Response:
    {
      "updatedPrompt": "..."
    }
    """
    data = request.json
    instructions = data.get('instructions')
    
    if not instructions:
        return jsonify({"error": "instructions are required"}), 400
        
    try:
        current_prompt = get_latest_prompt()
        new_prompt = run_manual_optimization(client, current_prompt, instructions)
        
        if new_prompt and len(new_prompt) > 20:
             supabase.table('prompts').update({'is_active': False}).eq('is_active', True).execute()
             
             data_insert = {
                'prompt_text': new_prompt,
                'is_active': True,
                'version_notes': f"Manual update: {instructions[:20]}..."
             }
             supabase.table('prompts').insert(data_insert).execute()
             
             return jsonify({
                 "updatedPrompt": new_prompt
             })
        else:
            return jsonify({"error": "Failed to generate prompt"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Legacy endpoint alias (optional, keeping for compatibility if needed)
@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    # Map legacy format to new function
    client_sequence = data.get('message')
    history = data.get('history', [])
    try:
        reply = generate_reply_logic(client_sequence, history)
        return jsonify({"response": reply})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
        
@app.route('/prompt', methods=['GET'])
def get_prompt():
    return jsonify({"system_prompt": get_latest_prompt()})

if __name__ == '__main__':
    # Use PORT from environment variable (Railway/Heroku/etc. standard)
    port = int(os.environ.get("PORT", 5000))
    # Listen on 0.0.0.0 to allow external connections in a containerized environment
    app.run(host='0.0.0.0', port=port, debug=False)

