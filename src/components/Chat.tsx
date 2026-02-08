'use client';

import { useState, useRef, useEffect } from 'react';
import { ChatMessage, ChatProvider, ChatResponse } from '@/types';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const PROVIDER_MODELS: Record<ChatProvider, { id: string; name: string }[]> = {
  openai: [
    { id: 'gpt-4o-mini', name: 'GPT-4o Mini' },
    { id: 'gpt-4o', name: 'GPT-4o' },
  ],
  anthropic: [
    { id: 'claude-3-5-haiku-20241022', name: 'Claude 3.5 Haiku' },
    { id: 'claude-sonnet-4-20250514', name: 'Claude Sonnet 4' },
  ],
};

export default function Chat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [provider, setProvider] = useState<ChatProvider>('openai');
  const [model, setModel] = useState('gpt-4o-mini');
  const [developerMode, setDeveloperMode] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [debugInfo, setDebugInfo] = useState<ChatResponse['debug'] | null>(null);
  const [costInfo, setCostInfo] = useState<ChatResponse['cost'] | null>(null);
  const [totalCost, setTotalCost] = useState(0);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    // Reset model when provider changes
    const models = PROVIDER_MODELS[provider];
    setModel(models[0].id);
  }, [provider]);

  const handleSend = async () => {
    const trimmed = input.trim();
    if (!trimmed || isLoading) return;

    const userMsg: ChatMessage = { role: 'user', content: trimmed };
    const updatedMessages = [...messages, userMsg];
    setMessages(updatedMessages);
    setInput('');
    setIsLoading(true);
    setDebugInfo(null);

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: updatedMessages,
          provider,
          model,
          developerMode,
        }),
      });
      const data: ChatResponse = await res.json();

      if (data.success && data.content) {
        setMessages([
          ...updatedMessages,
          { role: 'assistant', content: data.content },
        ]);
        if (data.cost) {
          setCostInfo(data.cost);
          setTotalCost((prev) => prev + data.cost!.totalCost);
        }
        if (data.debug) {
          setDebugInfo(data.debug);
        }
      } else {
        setMessages([
          ...updatedMessages,
          { role: 'assistant', content: `Error: ${data.error || 'Unknown error'}` },
        ]);
      }
    } catch {
      setMessages([
        ...updatedMessages,
        { role: 'assistant', content: 'Error: Failed to reach the server.' },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="max-w-4xl mx-auto flex flex-col h-[calc(100vh-12rem)]">
      {/* Header controls */}
      <div className="bg-white rounded-t-lg shadow-md p-4 flex flex-wrap items-center gap-4 border-b">
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium text-gray-700">Provider</label>
          <select
            value={provider}
            onChange={(e) => setProvider(e.target.value as ChatProvider)}
            className="text-sm border rounded-md px-2 py-1 bg-white text-gray-900"
          >
            <option value="openai">OpenAI</option>
            <option value="anthropic">Anthropic</option>
          </select>
        </div>

        <div className="flex items-center gap-2">
          <label className="text-sm font-medium text-gray-700">Model</label>
          <select
            value={model}
            onChange={(e) => setModel(e.target.value)}
            className="text-sm border rounded-md px-2 py-1 bg-white text-gray-900"
          >
            {PROVIDER_MODELS[provider].map((m) => (
              <option key={m.id} value={m.id}>
                {m.name}
              </option>
            ))}
          </select>
        </div>

        <label className="flex items-center gap-1 text-sm cursor-pointer ml-auto">
          <input
            type="checkbox"
            checked={developerMode}
            onChange={(e) => setDeveloperMode(e.target.checked)}
            className="rounded"
          />
          <span className="font-medium text-gray-700">Developer Mode</span>
        </label>

        {totalCost > 0 && (
          <span className="text-xs text-gray-500">
            Session: ${totalCost.toFixed(4)}
          </span>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto bg-gray-50 p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-gray-400 mt-20">
            <p className="text-lg">Start a conversation</p>
            <p className="text-sm mt-1">Select a provider and model above, then type a message.</p>
          </div>
        )}
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[80%] rounded-lg px-4 py-2 ${
                msg.role === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-white border text-gray-900 shadow-sm'
              }`}
            >
              {msg.role === 'assistant' ? (
                <div className="prose prose-sm max-w-none">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {msg.content}
                  </ReactMarkdown>
                </div>
              ) : (
                <p className="whitespace-pre-wrap">{msg.content}</p>
              )}
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-white border rounded-lg px-4 py-2 shadow-sm text-gray-500">
              Thinking…
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Developer mode panel */}
      {developerMode && (debugInfo || costInfo) && (
        <div className="bg-gray-900 text-green-400 text-xs p-3 font-mono max-h-32 overflow-y-auto">
          {costInfo && (
            <div>
              Cost: base=${costInfo.baseCost.toFixed(6)}
              {' + margin=$'}{costInfo.margin.toFixed(6)}
              {' = $'}{costInfo.totalCost.toFixed(6)}
              {' '}{costInfo.currency}
            </div>
          )}
          {debugInfo && (
            <div>
              Provider: {debugInfo.provider} | Model: {debugInfo.model} | Latency: {debugInfo.latencyMs}ms
            </div>
          )}
        </div>
      )}

      {/* Input */}
      <div className="bg-white rounded-b-lg shadow-md p-4 border-t">
        <div className="flex gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type a message…"
            rows={1}
            className="flex-1 resize-none border rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900"
          />
          <button
            onClick={handleSend}
            disabled={isLoading || !input.trim()}
            className="bg-blue-600 text-white px-4 py-2 rounded-md text-sm hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
