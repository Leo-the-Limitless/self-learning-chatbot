import os
import sys
from dotenv import load_dotenv

# Ensure backend directory is in path for imports
sys.path.append(os.path.join(os.getcwd(), 'backend'))

# Load environment variables
load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'))

from app import get_latest_prompt

prompt = get_latest_prompt()
print("-" * 50)
print("LATEST PROMPT FROM DATABASE:")
print("-" * 50)
print(prompt)
print("-" * 50)
print(f"Total lines: {len(prompt.splitlines())}")
