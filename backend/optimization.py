import os
import json
from groq import Groq

EDITOR_SYSTEM_PROMPT = """
# AI Chatbot Prompt Engineer - System Prompt

You are an expert prompt engineer specializing in training conversational AI through scenario-based learning. Your task is to analyze a specific interaction and generate a concise, powerful instruction to improve the AI's behavior in that specific scenario.

## YOUR TASK
1. **Analyze the gap**: Why did the AI fail to match the consultant's response?
2. **Generate a Concise Rule**: Create a short, straightforward instruction (max 1-2 sentences) that prevents this failure.
   - Example 1: "If a user asks about Bali, remind them that they must apply via the Jakarta embassy."
   - Example 2: "Always include a friendly emoji when confirming document approval."
   - Example 3: "When mentioning fees, explicitly state they are payable only after document approval."

## OUTPUT FORMAT
Return **ONLY** the new instruction line. Do NOT return the entire prompt. Do NOT include any preamble or explanation.
"""

def extract_prompt_from_markdown(content):
    # If LLM returned a code block, extract it
    import re
    match = re.search(r"```(?:markdown)?\s*(.*?)\s*```", content, re.DOTALL)
    if match:
        return match.group(1).strip()
    return content.strip()

def run_editor_optimization(client: Groq, current_prompt, sample_data, predicted_reply):
    """
    Runs the optimization loop and programmatically appends the result.
    """
    
    # Handle history formatting
    history_str = ""
    if isinstance(sample_data['history'], list):
        if len(sample_data['history']) > 0 and isinstance(sample_data['history'][0], dict):
             lines = []
             for msg in sample_data['history']:
                 role = msg.get('role', 'unknown').capitalize()
                 content = msg.get('message', msg.get('content', ''))
                 lines.append(f"{role}: {content}")
             history_str = "\n".join(lines)
        else:
            history_str = "\n".join(sample_data['history'])
            
    user_content = f"""
    Please analyze this interaction:
    
    1. **Client Message**: "{sample_data.get('client_input', sample_data.get('clientSequence', ''))}"
    2. **Chat History**: {history_str}
    3. **Real Consultant Reply**: "{sample_data.get('consultant_response', sample_data.get('consultantReply', ''))}"
    4. **Predicted AI Reply**: "{predicted_reply}"
    
    Generate ONE concise instruction to append to the prompt.
    """
    
    completion = client.chat.completions.create(
        model=os.environ.get("MODEL_NAME", "llama-3.1-8b-instant"),
        messages=[
            {"role": "system", "content": EDITOR_SYSTEM_PROMPT},
            {"role": "user", "content": user_content}
        ],
        temperature=0.2,
        max_tokens=500,
    )
    
    new_instruction = extract_prompt_from_markdown(completion.choices[0].message.content)
    
    # Programmatic Appending
    # Ensure there's a newline before the new instruction
    if not current_prompt.endswith("\n"):
        current_prompt += "\n"
    
    return f"{current_prompt}- {new_instruction}\n"

def run_manual_optimization(client: Groq, current_prompt, instructions):
    """
    Manually updates the prompt by appending instructions.
    """
    system_prompt = """
    You are a prompt engineer. Your task is to turn the user's instructions into a single, concise system message rule.
    Return ONLY the rule text.
    """
    
    completion = client.chat.completions.create(
        model=os.environ.get("MODEL_NAME", "llama-3.1-8b-instant"),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Convert this instruction into a concise system prompt rule: {instructions}"}
        ],
        temperature=0.2,
        max_tokens=500,
    )
    
    new_instruction = extract_prompt_from_markdown(completion.choices[0].message.content)

    # Programmatic Appending
    if not current_prompt.endswith("\n"):
        current_prompt += "\n"
    
    return f"{current_prompt}- {new_instruction}\n"
