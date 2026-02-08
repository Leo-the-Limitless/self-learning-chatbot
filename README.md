# DTV Assistant: Self-Learning Visa Consultant

A self-improving AI consultant for Thailand DTV visa applications.

## Key Features
- **Expert Consulting**: Specialized in Destination Thailand Visa (DTV) requirements.
- **Self-Learning**: Uses "Append-Only" scenario training to grow smarter over time.
- **Prompt Protection**: Ensures core consulting rules are never lost during optimization.
- **Premium UI**: Modern, dark-themed React frontend built for professional services.

## Quick Start
1. **Backend**: Install dependencies with `pip install -r requirements.txt` and configure your `.env` with Supabase and Groq keys.
2. **Database**: Run `python scripts/reset_prompt.py` to initialize the system prompt.
3. **Execution**: Start the backend with `python backend/app.py` and the frontend with `npm run dev` (inside `/frontend`).

## Project Flow
The system follows a feedback loop: the **Frontend** sends client queries to the **Backend**, which generates responses using a prompt stored in **Supabase**. Periodically, a **Training Script** analyzes AI performance against human expert data and appends concise, straightforward rules to the prompt to handle specific scenarios better.

## Tech Stack
- **Frontend**: Next.js, React, Tailwind CSS, Vercel
- **Backend**: Python (Flask), Groq AI (Llama 3.1)
- **Database**: Supabase (PostgreSQL)

## Usage Example
A user asks about the 500k THB requirement; the AI explains the 3-month bank statement rule and offers a currency conversion estimate. If the AI misses a specific country detail, the training loop appends a rule like: *"For Singapore applications, always mention the 7-10 day turnaround."*

## Contributing & License
Contributions are welcome via pull requests. This project is licensed under the MIT License.
