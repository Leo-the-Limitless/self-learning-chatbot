import os
import json
import random
import sys
from groq import Groq
from dotenv import load_dotenv

# Ensure backend directory is in path for imports
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend'))

# Load environment variables explicitly
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend', '.env')
load_dotenv(env_path)

from app import get_latest_prompt, supabase, generate_reply_logic
from optimization import run_editor_optimization, extract_prompt_from_markdown
from utils import load_data

# Initialize Groq client
client = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),
)

def main():
    print("Loading data...")
    data = load_data()
    if not data:
        print("No training data found.")
        return

    # Select a random sample for training
    sample = random.choice(data)
    print(f"Selected sample interaction: {sample['client_input'][:50]}...")

    # 1. Get current prompt
    current_prompt = get_latest_prompt()
    print("Current prompt loaded.")

    # 2. Generate Prediction
    print("Generating AI prediction...")
    try:
        # generate_reply_logic expects history as list of dicts (Groq format) or strings
        # parsed data has 'history' as list of strings ["Client: ...", "Consultant: ..."]
        # generate_reply_logic handles list of strings via format_history fallback
        predicted_reply = generate_reply_logic(sample['client_input'], sample['history'])
        print(f"Prediction: {predicted_reply[:100]}...")
    except Exception as e:
        print(f"Error generating prediction: {e}")
        return

    # 3. Running Editor Optimization
    print("Running Editor Optimization...")
    try:
        optimization_result = run_editor_optimization(client, current_prompt, sample, predicted_reply)
        new_prompt = optimization_result
        
        if new_prompt and len(new_prompt) > 100:
            print("New prompt generated successfully.")
            
            # 4. Update Database
            print("Updating database...")
            # Deactivate old prompts
            supabase.table('prompts').update({'is_active': False}).eq('is_active', True).execute()
            
            # Insert new prompt
            data_insert = {
                'prompt_text': new_prompt,
                'is_active': True,
                'version_notes': f"Optimized based on sample: {sample['client_input'][:30]}..."
            }
            supabase.table('prompts').insert(data_insert).execute()
            print("Database updated!")
            
            # 5. Verify
            print("Verifying with new prompt...")
            # Calling generate_reply_logic again pulls the latest active prompt from DB
            new_prediction = generate_reply_logic(sample['client_input'], sample['history'])
            print(f"New Prediction: {new_prediction[:100]}...")
            
        else:
            print("Optimization failed to produce a valid prompt.")
            print("-" * 50)
            print(f"RAW LLM OUTPUT:\n{optimization_result}")
            print("-" * 50)

    except Exception as e:
        print(f"Error during optimization: {e}")

if __name__ == "__main__":
    main()
