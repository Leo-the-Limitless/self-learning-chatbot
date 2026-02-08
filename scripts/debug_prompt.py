import os
import sys
from dotenv import load_dotenv

sys.path.append(os.path.join(os.getcwd(), 'backend'))
load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'))

from app import get_latest_prompt

with open('debug_prompt_output.txt', 'w', encoding='utf-8') as f:
    f.write(get_latest_prompt())
