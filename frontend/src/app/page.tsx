'use client';

import { useState, useEffect, useRef } from 'react';

interface Message {
  role: 'client' | 'consultant';
  message: string;
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setInput('');
    const newMessages: Message[] = [...messages, { role: 'client', message: userMessage }];
    setMessages(newMessages);
    setIsLoading(true);

    try {
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL;
      if (!backendUrl) {
        throw new Error("Backend URL is not defined. Please restart your dev server.");
      }
      console.log('Sending request to:', `${backendUrl}/generate-reply`);

      const response = await fetch(`${backendUrl}/generate-reply`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          clientSequence: userMessage,
          chatHistory: messages
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      if (data.aiReply) {
        setMessages([...newMessages, { role: 'consultant', message: data.aiReply }]);
      }
    } catch (error) {
      console.error('Fetch Error:', error);
      alert(`Connection Error: ${error instanceof Error ? error.message : String(error)}`);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="flex min-h-screen flex-col bg-black text-white font-sans">
      {/* Header */}
      <header className="border-b border-white/10 p-6 flex justify-between items-center backdrop-blur-md sticky top-0 z-10 bg-black/50">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-brand-amber-light to-brand-amber-dark flex items-center justify-center shadow-lg shadow-brand-amber-dark/20">
            <span className="font-bold text-black text-xl">D</span>
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight">DTV Assistant <span className="text-brand-amber-light text-xs font-normal border border-brand-amber-light/30 px-1.5 py-0.5 rounded ml-2 uppercase">Beta</span></h1>
            <p className="text-xs text-neutral-400">Thailand Visa Consulting • Powered by AI</p>
          </div>
        </div>
      </header>

      {/* Chat Area */}
      <div className="flex-1 overflow-y-auto p-4 md:p-8 space-y-6 max-w-4xl mx-auto w-full custom-scrollbar">
        {messages.length === 0 && (
          <div className="h-full flex flex-col items-center justify-center text-center space-y-4 py-20 animate-in fade-in slide-in-from-bottom-4 duration-1000">
            <div className="w-20 h-20 rounded-full bg-brand-amber-light/10 flex items-center justify-center mb-4">
              <svg className="w-10 h-10 text-brand-amber-light" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
            </div>
            <h2 className="text-3xl font-bold text-white">How can we help you today?</h2>
            <p className="text-neutral-400 max-w-md mx-auto">
              Ask any questions about the Destination Thailand Visa (DTV),
              requirements, or the application process.
            </p>
            <div className="flex flex-wrap gap-2 justify-center mt-6">
              {['What is DTV?', 'Requirements for Remote Workers', 'How long is processing?'].map((suggestion) => (
                <button
                  key={suggestion}
                  onClick={() => setInput(suggestion)}
                  className="px-4 py-2 rounded-full border border-white/10 hover:border-brand-amber-light/50 hover:bg-brand-amber-light/5 transition-all text-sm text-neutral-300"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex ${msg.role === 'client' ? 'justify-end' : 'justify-start'} animate-in fade-in slide-in-from-bottom-2 duration-300`}
          >
            <div
              className={`max-w-[85%] rounded-2xl p-4 shadow-sm ${msg.role === 'client'
                ? 'bg-neutral-800 text-neutral-100 rounded-tr-none'
                : 'bg-white text-black rounded-tl-none border-l-4 border-brand-amber-light font-medium leading-relaxed'
                }`}
            >
              <div className="text-xs mb-1 opacity-50 uppercase tracking-widest font-bold">
                {msg.role === 'client' ? 'You' : 'Consultant'}
              </div>
              <div className="whitespace-pre-wrap">{msg.message}</div>
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="flex justify-start animate-pulse">
            <div className="bg-neutral-900 rounded-2xl p-4 text-neutral-400 italic text-sm">
              Assistant is typing...
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <footer className="p-4 md:p-8 bg-black border-t border-white/10">
        <form onSubmit={handleSend} className="max-w-4xl mx-auto relative group">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your question about Thailand DTV..."
            disabled={isLoading}
            className="w-full bg-neutral-900 border border-white/10 rounded-2xl py-4 pl-6 pr-16 focus:outline-none focus:ring-2 focus:ring-brand-amber-light/50 transition-all text-white placeholder:text-neutral-500"
          />
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="absolute right-2 top-2 bottom-2 px-6 bg-brand-amber-light hover:bg-brand-amber-dark disabled:bg-neutral-800 disabled:text-neutral-600 rounded-xl text-black font-bold transition-all flex items-center gap-2 group-focus-within:shadow-lg group-focus-within:shadow-brand-amber-light/20"
          >
            {isLoading ? (
              <div className="w-5 h-5 border-2 border-black/30 border-t-black rounded-full animate-spin" />
            ) : (
              <>
                <span>Send</span>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                </svg>
              </>
            )}
          </button>
        </form>
        <p className="text-center text-[10px] text-neutral-600 mt-4 uppercase tracking-[0.2em] font-medium">
          Confidential & Professional Thai Visa Consulting
        </p>
      </footer>

      <style jsx global>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 6px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: transparent;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: #333;
          border-radius: 10px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: #B45309;
        }
      `}</style>
    </main>
  );
}
