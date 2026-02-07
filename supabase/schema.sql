-- Create a table to store system prompts and their versions
CREATE TABLE IF NOT EXISTS prompts (
    id SERIAL PRIMARY KEY,
    prompt_text TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT FALSE,
    version_notes TEXT
);

-- Insert an initial prompt
INSERT INTO prompts (prompt_text, is_active, version_notes)
VALUES (
    'You are a helpful immigration consultant for Thailand. You assist with visa applications, specifically the Destination Thailand Visa (DTV). Be professional, friendly, and concise.',
    TRUE,
    'Initial baseline prompt'
);

-- Create a table to store conversation logs and feedback (for future use/references)
CREATE TABLE IF NOT EXISTS conversation_logs (
    id SERIAL PRIMARY KEY,
    client_message TEXT,
    bot_response TEXT,
    consultant_ground_truth TEXT, -- If available from training
    prompt_id INTEGER REFERENCES prompts(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    feedback_score INTEGER, -- 1-5 or similar
    feedback_text TEXT
);
