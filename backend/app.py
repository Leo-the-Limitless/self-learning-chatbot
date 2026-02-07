import os
import json
import random
from typing import List, Dict
from flask import Flask, request, jsonify
from groq import Groq
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Initialize Groq client
client = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),
)

# Initialize Supabase client
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# Configuration
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'conversations.json')
INITIAL_SYSTEM_PROMPT = """
# Immigration Consultant Chatbot - System Prompt

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
- Require thorough review of previous rejection reasons
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

# Load conversation data for training
def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        conversations = json.load(f)
    
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

training_data = load_data()

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message')
    history = data.get('history', [])

    # Ensure we have the latest prompt from the database
    current_system_prompt = get_latest_prompt()

    messages = [{"role": "system", "content": current_system_prompt}]
    
    # Add history
    for msg in history:
        messages.append(msg)
    
    messages.append({"role": "user", "content": user_message})

    # CRITICAL: Ensure "json" is in messages for Groq API compliance
    messages.append({"role": "system", "content": "IMPORTANT: You must respond in JSON format."})

    try:
        completion = client.chat.completions.create(
            model=os.environ.get("MODEL_NAME", "llama-3.1-8b-instant"), 
            messages=messages,
            temperature=0.7,
            max_tokens=500, # Increased for detailed responses
            top_p=1,
            stream=False,
            stop=None,
            response_format={"type": "json_object"} # Use Groq's JSON mode if supported, or just hope LLM follows prompt
        )
        response_content = completion.choices[0].message.content
        
        # Try to parse JSON to return just the reply text, or return the whole object if client wants it.
        # Assuming typical chat interface wants text.
        try:
            json_response = json.loads(response_content)
            # If the LLM returned {"reply": "..."}, extract the reply
            if "reply" in json_response:
                return jsonify({"response": json_response["reply"], "raw_json": json_response})
            else:
                return jsonify({"response": response_content}) # Fallback
        except json.JSONDecodeError:
            return jsonify({"response": response_content}) # Fallback logic

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/learn', methods=['POST'])
def learn():
    global current_system_prompt
    if not training_data:
        return jsonify({"error": "No training data available"}), 500

    # 1. Select a random sample
    sample = random.choice(training_data)
    
    history_str = "\n".join(sample['history'])
    client_input = sample['client_input']
    ground_truth = sample['consultant_response']

    # 2. Generate detailed critique and improved prompt
    meta_prompt = f"""
    You are an AI optimizer. 
    Current System Prompt: "{current_system_prompt}"
    
    Training Scenario:
    History: {history_str}
    Client Input: "{client_input}"
    Ideal Consultant Response (Ground Truth): "{ground_truth}"
    
    Task:
    Analyze the Ground Truth response. It has a specific tone, style, and information accuracy.
    The goal is to improve the System Prompt so that an AI using it would generate a response closer to the Ground Truth in style and substance.
    
    Propose a NEW, improved System Prompt.
    Return ONLY the new system prompt text. Do not add explanations.
    """
    
    try:
        completion = client.chat.completions.create(
            model=os.environ.get("MODEL_NAME", "llama-3.1-8b-instant"),
            messages=[{"role": "user", "content": meta_prompt}],
            temperature=0.7,
        )
        new_prompt = completion.choices[0].message.content.strip()
        
        if len(new_prompt) > 20: 
            # Deactivate old prompts
            try:
                # This could be done in a transaction or smarter way
                supabase.table('prompts').update({'is_active': False}).eq('is_active', True).execute()
                
                # Insert new prompt
                data = {
                    'prompt_text': new_prompt,
                    'is_active': True,
                    'version_notes': f'Improved based on sample interaction: {client_input[:20]}...'
                }
                supabase.table('prompts').insert(data).execute()
                
                current_system_prompt = new_prompt
                
                return jsonify({
                    "status": "improved",
                    "new_prompt": new_prompt,
                })
            except Exception as db_e:
                 return jsonify({"error": f"Database error: {str(db_e)}"}), 500
        else:
            return jsonify({"status": "failed", "reason": "Generated prompt too short"}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/prompt', methods=['GET'])
def get_prompt():
    return jsonify({"system_prompt": current_system_prompt})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
