# DTV Assistant: Self-Learning Visa Consultant

A self-improving AI chatbot for Thailand DTV visa applications that learns through real-world interactions.

## Live Demo
The application is hosted on Vercel: https://self-learning-chatbot-one.vercel.app/

## Quick Start
1. **Backend**: Install dependencies with `pip install -r requirements.txt` and configure your `.env` with Supabase and Groq keys.
2. **Database**: Run `python scripts/reset_prompt.py` to initialize the system prompt.
3. **Training**: To improve the AI's logic based on conversations, run:
   ```powershell
   python scripts/train_agent.py
   ```
4. **Execution**: Start the backend with `python backend/app.py` and the frontend with `npm run dev` (inside `/frontend`).

## Key Features
- **Expert Consulting**: Specialized in Destination Thailand Visa (DTV) requirements.
- **Self-Learning**: Append-only scenario training based on real-world feedback.
- **Prompt Protection**: Core logic is shielded from accidental modification.
- **Modern UI**: Clean, dark-themed interface for professional consulting.

## Tech Stack
- Next.js (Frontend)
- Python Flask (Backend)
- Groq AI (Llama 3.1)
- Supabase (Database)

## License
MIT License.
