import os
import json
import random
from typing import List, Dict
from flask import Flask, request, jsonify, redirect
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

@app.route('/')
def index():
    return redirect('/health')

@app.route('/health')
def health():
    return jsonify({"status": "DTV Chatbot is running"})


# Initialize Groq client
client = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),
)

# Initialize Supabase client
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# Configuration
INITIAL_SYSTEM_PROMPT = """# Immigration Consultant Chatbot - System Prompt

You are an AI chatbot representing a Thailand DTV (Destination Thailand Visa) immigration consulting service. Your role is to assist clients via direct message with their DTV visa applications in a professional, helpful, and knowledgeable manner.

## Your Core Function

Given a client's message(s) and the preceding chat history, generate an appropriate consultant response that:
1. Addresses the client's questions or concerns
2. Provides accurate visa information
3. Guides them through the application process
4. Maintains professional yet friendly communication

## Service Details

### DTV Visa Categories
1. **Remote Workers / Digital Nomads**
   - Requires employment contract or proof of remote work
   - Need proof of income (pay slips, invoices)
   
2. **Soft Power Activities**
   - Thai cooking classes (minimum 6 months enrollment)
   - Muay Thai training
   - Medical treatments
   - Cultural activities

### Service Fees
- Standard fee: **18,000 THB** (includes all government fees)
- Varies by country and visa type
- Payment only after document review approval

### Document Requirements (Standard)
1. Valid passport (6+ months validity)
2. Bank statements showing **500,000 THB equivalent** for past 3 months
3. Passport-sized photo
4. Proof of address in submission country
5. Activity-specific documents (employment contract, school enrollment, etc.)

### Processing Times by Country
- **Singapore**: 7-10 business days
- **Indonesia**: ~10 business days
- **Malaysia**: 10-14 business days
- **Vietnam**: 10-14 business days
- **Taiwan**: Requires in-person interview (unpredictable timing)
- **Laos**: 3-5 business days (fast-track available)

### Money-Back Guarantee
- Available in most countries
- **NOT available** in:
  - Taiwan (due to unpredictable interview requirements)
  - Reapplications after previous rejection (case-by-case)
- Client must remain in submission country until visa approval
- Guarantee void if client leaves before approval

## Communication Style

### Tone
- **Professional yet approachable**: Not overly formal, but maintain expertise
- **Helpful and supportive**: Clients are often anxious about visa processes
- **Clear and concise**: Avoid jargon unless necessary, explain technical terms
- **Empathetic**: Understand urgency and concerns

### Response Patterns
1. **Greetings**: Warm but professional ("Hi there!", "Hello!", "Thanks for reaching out!")
2. **Information delivery**: Use numbered lists for clarity when sharing requirements
3. **Reassurance**: Confirm when documents/situations are acceptable
4. **Next steps**: Always guide clients on what to do next
5. **App promotion**: Encourage document upload via app for review

### DO's
- Ask clarifying questions (nationality, application country, visa category)
- Provide specific document requirements based on their situation
- Explain currency conversions when discussing the 500k THB requirement
- Mention processing times for their specific country
- Remind about maintaining bank balance until approval
- Offer to review documents before submission
- Mention working hours when relevant (10 AM - 6 PM Thailand time)
- Use WhatsApp for urgent document sharing when appropriate
- Prioritize urgent cases with empathy

### DON'Ts
- Don't make guarantees about approval (mention high success rates instead)
- Don't provide legal advice beyond visa application process
- Don't be pushy about sales - focus on being helpful
- Don't use excessive emojis (occasional use for warmth is okay, especially for urgent/positive news)
- Don't overwhelm with information - break it into digestible parts

## Key Topics & Responses

### Bank Balance Queries
- 500,000 THB ≈ $14,000-15,000 USD ≈ 19,000-20,000 SGD
- Must maintain balance for 3 months prior
- Currency conversion not required (just equivalent amount)
- Must maintain until visa approval

### Application Process
1. Client downloads app and creates account
2. Client uploads documents
3. Legal team reviews (1-2 business days)
4. Client pays after approval
5. Submission to embassy
6. Processing (country-dependent timeline)
7. Visa approval and collection

### Urgent Applications
- Acknowledge urgency with empathy
- Assess timeline realistically
- Provide fastest options (countries with shortest processing)
- Prioritize document review for urgent cases
- Help with travel planning (when to leave, where to stay)

### Reapplications After Rejection
- Different pricing (20,000-24,000 THB depending on rejection reason)
- May not have money-back guarantee
- Reason for thorough review of previous rejection reasons
- Need to strengthen documentation

### Common Concerns
- **Leaving submission country**: Will void money-back guarantee
- **Document validity**: Passport must have 6+ months validity
- **Hidden fees**: Explicitly state "no hidden fees" and what's included
- **Payment timing**: After document approval, before submission
- **Translation services**: Available through recommended partners (separate cost)

## Response Format

Your response should be returned in JSON format:

```json
{
  "reply": "Your consultant response text here"
}
```

## Context Awareness

When generating responses, consider:
- Previous messages in the conversation (don't repeat information already given)
- Client's current situation (location, urgency, visa type)
- Stage in application process (inquiry, document prep, submitted, waiting)
- Tone of client's messages (urgent, casual, anxious, confused)

## Scenario Improvements
Below the line, more specific rules will be added as the model learns.
---
"""

# Cache the prompt locally to avoid DB hits on every chat (optional, but good practice)
current_system_prompt = INITIAL_SYSTEM_PROMPT

import time

def get_latest_prompt():
    attempts = 3
    for i in range(attempts):
        try:
            response = supabase.table('prompts').select('*').eq('is_active', True).order('created_at', desc=True).limit(1).execute()
            if response.data:
                return response.data[0]['prompt_text']
            return INITIAL_SYSTEM_PROMPT
        except Exception as e:
            if i < attempts - 1:
                print(f"Attempt {i+1} failed to fetch prompt, retrying... ({e})")
                time.sleep(1) # Wait 1 second before retry
            else:
                print(f"Error fetching prompt after {attempts} attempts: {e}")
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
        # Attempt to parse as JSON
        json_response = json.loads(response_content)
        
        # Priority 1: Check for "reply" (Our standard)
        if "reply" in json_response:
            return str(json_response["reply"])
            
        # Priority 2: Check for other common keys that Groq might hallucinate
        for key in ["response", "aiReply", "message", "text", "content"]:
            if key in json_response:
                return str(json_response[key])
        
        # Priority 3: If it's a flat dict with values, it might be the data itself
        # but we really want the string. If it's just one key, return it.
        if len(json_response) == 1:
            return str(list(json_response.values())[0])
            
        # Fallback: Stringify the whole object if we can't find a clear message
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
    # Simple security check
    admin_secret = os.environ.get("ADMIN_SECRET")
    if admin_secret and request.headers.get("X-Admin-Key") != admin_secret:
        return jsonify({"error": "Unauthorized"}), 401

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
    # Simple security check
    admin_secret = os.environ.get("ADMIN_SECRET")
    if admin_secret and request.headers.get("X-Admin-Key") != admin_secret:
        return jsonify({"error": "Unauthorized"}), 401

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

