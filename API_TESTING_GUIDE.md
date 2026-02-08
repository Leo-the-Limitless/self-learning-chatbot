# API Testing Guide

This guide provides instructions on how to use the project's API endpoints using Postman and `curl`.

## Base URL
**Production:** `https://self-learning-chatbot-production.up.railway.app`
**Local:** `http://localhost:5000`

---

## 1. Postman Instructions

### A. Manual Improvement (`/improve-ai-manually`)
Refine the AI's behavior by providing specific instructions.

1.  **POST Request**: `{{BASE_URL}}/improve-ai-manually`
2.  **Body**: Select `raw` -> `JSON`.
3.  **JSON Payload**:
    ```json
    {
      "instructions": "Be more concise. Always mention appointment booking proactively."
    }
    ```
4.  **Send**.

### B. Self-Learning Improvement (`/improve-ai`)
Trigger the auto-optimization logic based on a specific scenario.

1.  **POST Request**: `{{BASE_URL}}/improve-ai`
2.  **Body**: Select `raw` -> `JSON`.
3.  **JSON Payload**:
    ```json
    {
       "clientSequence": "I am American and currently in Bali. Can I apply from Indonesia?",
       "chatHistory": [
         { "role": "consultant", "message": "Hi there! May I know your nationality?" }
       ],
       "consultantReply": "Yes, absolutely! You can apply at the Thai Embassy in Jakarta."
    }
    ```
4.  **Send**.

---

## 2. Curl Commands

> [!IMPORTANT]
> **Windows Users (PowerShell):** If you are using PowerShell, use the backtick (`` ` ``) instead of the backslash (`\`) for multi-line commands, or simply copy the single-line versions provided below.

### Health Check
```bash
curl -X GET {{BASE_URL}}/health
```

### Generate AI Reply (Single Line for Windows)
```powershell
curl -X POST {{BASE_URL}}/generate-reply -H "Content-Type: application/json" -d "{\`"clientSequence\`": \`"I am interested in the DTV visa. What are the requirements?\`", \`"chatHistory\`": []}"
```

### Improve AI (Single Line for Windows)
```powershell
curl -X POST {{BASE_URL}}/improve-ai -H "Content-Type: application/json" -d "{\`"clientSequence\`": \`"I am American and currently in Bali. Can I apply from Indonesia?\`", \`"chatHistory\`": [{\`"role\`": \`"consultant\`", \`"message\`": \`"Hi there!\`"}], \`"consultantReply\`": \`"Yes, you can apply in Jakarta.\`"}"
```

### Improve AI Manually (Single Line for Windows)
```powershell
curl -X POST {{BASE_URL}}/improve-ai-manually -H "Content-Type: application/json" -d "{\`"instructions\`": \`"Be more concise.\`"}"
```

---

## 3. Scripts

You can also use the Python scripts provided in the project to verify all endpoints at once:

```bash
python scripts/verify_endpoints.py
```
