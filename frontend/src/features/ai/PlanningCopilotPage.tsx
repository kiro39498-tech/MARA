import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { RefreshCw, Send } from 'lucide-react';

const authHeaders = () => ({
  'Authorization': `Bearer ${localStorage.getItem('access_token') || ''}`,
  'Content-Type': 'application/json',
});

export default function PlanningCopilotPage() {
  const [messages, setMessages] = useState<any[]>([
    { sender: 'assistant', text: 'Hello! I am the MARA Planning Copilot. Ask me about material status, production order shortages, or replenishment actions.' }
  ]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMsg = { sender: 'user', text: input };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setSending(true);

    try {
      const response = await fetch('http://localhost:8000/api/v1/planning/copilot', {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify({
          session_id: 'local_session',
          message: input
        })
      }).then(r => r.json());

      setMessages(prev => [...prev, { sender: 'assistant', text: response.response, evidence: response.evidence }]);
    } catch (err) {
      setMessages(prev => [...prev, { sender: 'assistant', text: 'Error communicating with orchestrator. Please try again.' }]);
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="flex flex-col gap-6 h-[calc(100vh-140px)]">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Planning Copilot</h1>
        <p className="text-muted-foreground">Ask questions grounded in deterministic planning computations.</p>
      </div>

      <div className="flex-1 flex flex-col border rounded-xl overflow-hidden bg-card/45 backdrop-blur-md">
        <div className="flex-1 p-4 overflow-y-auto flex flex-col gap-4">
          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`flex flex-col max-w-[80%] ${msg.sender === 'user' ? 'ml-auto items-end' : 'mr-auto items-start'}`}
            >
              <div
                className={`p-3 rounded-lg text-sm ${msg.sender === 'user' ? 'bg-primary text-primary-foreground' : 'bg-muted'}`}
              >
                <p className="whitespace-pre-line">{msg.text}</p>
              </div>
              {msg.evidence && Object.keys(msg.evidence).length > 0 && (
                <div className="mt-1 bg-muted/30 border text-[11px] p-2 rounded max-w-full overflow-x-auto text-muted-foreground font-mono">
                  <strong>Evidence Source:</strong> {JSON.stringify(msg.evidence, null, 2)}
                </div>
              )}
            </div>
          ))}
        </div>

        <div className="p-3 border-t bg-background flex gap-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Why is MAT-10001 critical? Show top recommendations..."
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            disabled={sending}
          />
          <Button onClick={handleSend} disabled={sending}>
            {sending ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
          </Button>
        </div>
      </div>
    </div>
  );
}
