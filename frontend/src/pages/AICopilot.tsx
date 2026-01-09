import { useState, useRef, useEffect } from 'react';
import MainLayout from '../components/layout/MainLayout';
import { Send, User, Bot, Loader2 } from 'lucide-react';
import { sendMessageToCopilot, type ChatMessage } from '../api/copilot';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export default function AICopilot() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    { role: 'assistant', content: '你好！我是你的投資助理。你可以問我關於資產分佈、風險指標或個股表現的問題。' }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: ChatMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const reply = await sendMessageToCopilot(input);
      setMessages(prev => [...prev, { role: 'assistant', content: reply }]);
    } catch (error) {
      setMessages(prev => [...prev, { role: 'assistant', content: '抱歉，系統暫時無法回應您的請求。' }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <MainLayout>
      <div className="flex flex-col h-[calc(100vh-8rem)]">
        <header className="mb-6">
          <h1 className="text-3xl font-bold tracking-tight text-white">AI Copilot</h1>
          <p className="text-slate-400 mt-2">您的智能投資決策夥伴。</p>
        </header>

        {/* Chat Area */}
        <div className="flex-1 bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden flex flex-col shadow-2xl">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-6 space-y-6 scrollbar-hide">
            {messages.map((msg, idx) => (
              <div 
                key={idx} 
                className={cn(
                  "flex items-start gap-4",
                  msg.role === 'user' ? "flex-row-reverse" : "flex-row"
                )}
              >
                <div className={cn(
                  "w-8 h-8 rounded-full flex items-center justify-center shrink-0 shadow-lg",
                  msg.role === 'user' ? "bg-blue-600" : "bg-slate-700"
                )}>
                  {msg.role === 'user' ? <User size={16} className="text-white" /> : <Bot size={16} className="text-white" />}
                </div>
                <div className={cn(
                  "max-w-[80%] px-4 py-3 rounded-2xl text-sm leading-relaxed shadow-sm",
                  msg.role === 'user' 
                    ? "bg-blue-600 text-white rounded-tr-none" 
                    : "bg-slate-800 text-slate-200 border border-slate-700 rounded-tl-none"
                )}>
                  {msg.content}
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="flex items-start gap-4">
                <div className="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center shrink-0">
                  <Bot size={16} className="text-white" />
                </div>
                <div className="bg-slate-800 text-slate-400 px-4 py-3 rounded-2xl rounded-tl-none border border-slate-700 flex items-center gap-2">
                  <Loader2 size={14} className="animate-spin" />
                  <span>AI 正在思考中...</span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="p-4 bg-slate-950/50 border-t border-slate-800">
            <div className="flex gap-4 max-w-4xl mx-auto">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSend()}
                placeholder="輸入您的投資問題..."
                className="flex-1 bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-600 transition-all placeholder:text-slate-600"
              />
              <button 
                onClick={handleSend}
                disabled={isLoading}
                className="bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white p-3 rounded-xl transition-all shadow-lg shadow-blue-600/20"
              >
                <Send size={20} />
              </button>
            </div>
          </div>
        </div>
      </div>
    </MainLayout>
  );
}
