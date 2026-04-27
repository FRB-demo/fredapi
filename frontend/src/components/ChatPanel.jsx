import React, { useState, useRef, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import { Send, X, MessageSquare, Plus, Sparkles } from 'lucide-react'
import { sendChatMessage, fetchSeries } from '../services/api'

const QUICK_PROMPTS = [
  'What economic indicators should I watch?',
  'Tell me about current inflation trends',
  'What are the signs of a recession?',
  'Recommend housing market indicators',
  'Explain the yield curve',
];

export default function ChatPanel({ activeSeries, onAddSeries, onClose }) {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Hello! I\'m your economic research assistant. Ask me about any U.S. economic indicator, trends, or data analysis. I can also suggest series to add to your chart.',
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setLoading(true);

    try {
      // P-9: Send only summary stats instead of full data arrays
      const context = activeSeries.map(s => {
        const vals = s.values || [];
        const last50 = vals.slice(-50);
        const last50dates = (s.dates || []).slice(-50);
        return {
          series_id: s.series_id,
          title: s.title,
          values: last50,
          dates: last50dates,
          units: s.units || '',
        };
      });

      const result = await sendChatMessage(userMessage, context);

      setMessages(prev => [...prev, {
        role: 'assistant',
        content: result.response,
        suggestedSeries: result.suggested_series || [],
      }]);
    } catch (e) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Sorry, I encountered an error processing your request. Please try again.',
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleAddSuggested = async (series) => {
    try {
      const data = await fetchSeries(series.series_id);
      onAddSeries(data);
    } catch (e) {
      console.error('Failed to add series:', e);
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-100">
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-blue-500" />
          <h3 className="text-sm font-semibold text-slate-900">Research Assistant</h3>
        </div>
        <button onClick={onClose} className="text-slate-400 hover:text-slate-600">
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg, i) => (
          <div key={`msg-${i}-${msg.role}`} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[85%] rounded-xl px-3.5 py-2.5 text-sm ${
              msg.role === 'user'
                ? 'bg-blue-600 text-white'
                : 'bg-slate-100 text-slate-800'
            }`}>
              {msg.role === 'assistant' ? (
                <div className="chat-markdown">
                  <ReactMarkdown>{msg.content}</ReactMarkdown>
                </div>
              ) : (
                msg.content
              )}

              {/* Suggested series chips */}
              {msg.suggestedSeries && msg.suggestedSeries.length > 0 && (
                <div className="mt-2 pt-2 border-t border-slate-200 space-y-1">
                  <p className="text-xs text-slate-500 font-medium">Add to chart:</p>
                  <div className="flex flex-wrap gap-1">
                    {msg.suggestedSeries.map(s => (
                      <button
                        key={s.series_id}
                        onClick={() => handleAddSuggested(s)}
                        className="flex items-center gap-1 px-2 py-0.5 bg-white border border-slate-200 rounded-full text-xs text-slate-700 hover:bg-blue-50 hover:border-blue-200 hover:text-blue-700 transition-colors"
                      >
                        <Plus className="w-3 h-3" />
                        {s.series_id}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-slate-100 rounded-xl px-4 py-3">
              <div className="flex gap-1.5">
                <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Quick prompts */}
      {messages.length <= 2 && (
        <div className="px-4 pb-2">
          <div className="flex flex-wrap gap-1.5">
            {QUICK_PROMPTS.map((prompt, i) => (
              <button
                key={prompt}
                onClick={() => { setInput(prompt); }}
                className="px-2.5 py-1 bg-slate-50 border border-slate-200 rounded-full text-xs text-slate-600 hover:bg-blue-50 hover:border-blue-200 hover:text-blue-700 transition-colors"
              >
                {prompt}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input */}
      <div className="p-3 border-t border-slate-100">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleSend()}
            placeholder="Ask about economic data..."
            className="flex-1 px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || loading}
            className="px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
