"use client";

import { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Send, User, BrainCircuit, FileText } from "lucide-react";
import api from "@/lib/api";
import { motion, AnimatePresence } from "framer-motion";

export default function CopilotPage() {
  const [messages, setMessages] = useState<{role: string, content: string, citations?: any[]}[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const sendMessage = async () => {
    if (!input.trim()) return;
    
    const userMsg = input;
    setMessages(prev => [...prev, { role: "user", content: userMsg }]);
    setInput("");
    setLoading(true);

    try {
      const res = await api.post("/copilot/chat", { message: userMsg });
      setMessages(prev => [...prev, { 
        role: "assistant", 
        content: res.data.answer, 
        citations: res.data.sources 
      }]);
    } catch (err) {
      console.error(err);
      setMessages(prev => [...prev, { role: "assistant", content: "Sorry, I encountered an error." }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="h-full flex gap-6 max-w-7xl mx-auto mt-4">
      {/* Chat Area */}
      <Card className="flex-1 flex flex-col border-border/50 bg-card overflow-hidden h-[calc(100vh-100px)]">
        <div className="p-4 border-b border-border/50 flex items-center space-x-2">
          <BrainCircuit className="h-5 w-5 text-primary" />
          <h2 className="font-semibold">AI Copilot</h2>
        </div>
        
        <div className="flex-1 overflow-y-auto p-4 space-y-6">
          <AnimatePresence>
            {messages.map((msg, i) => (
              <motion.div 
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                key={i} 
                className={`flex gap-4 ${msg.role === "user" ? "flex-row-reverse" : ""}`}
              >
                <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${msg.role === "user" ? "bg-primary text-primary-foreground" : "bg-accent text-accent-foreground"}`}>
                  {msg.role === "user" ? <User className="h-4 w-4" /> : <BrainCircuit className="h-4 w-4" />}
                </div>
                <div className={`px-4 py-3 rounded-2xl max-w-[80%] ${msg.role === "user" ? "bg-primary text-primary-foreground" : "bg-accent/50 text-foreground"}`}>
                  <p className="text-sm leading-relaxed">{msg.content}</p>
                </div>
              </motion.div>
            ))}
            {loading && (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex gap-4">
                 <div className="w-8 h-8 rounded-full bg-accent flex items-center justify-center">
                   <BrainCircuit className="h-4 w-4 text-accent-foreground animate-pulse" />
                 </div>
                 <div className="px-4 py-3 rounded-2xl bg-accent/50 max-w-[80%]">
                   <p className="text-sm text-muted-foreground animate-pulse">Thinking...</p>
                 </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        <div className="p-4 border-t border-border/50 bg-card/50">
          <form onSubmit={e => { e.preventDefault(); sendMessage(); }} className="flex space-x-2">
            <Input 
              value={input} 
              onChange={e => setInput(e.target.value)} 
              placeholder="Ask about your industrial documents..." 
              className="flex-1 rounded-full bg-background border-border"
              disabled={loading}
            />
            <Button type="submit" size="icon" className="rounded-full" disabled={loading || !input.trim()}>
              <Send className="h-4 w-4" />
            </Button>
          </form>
        </div>
      </Card>

      {/* Citations Panel */}
      <Card className="w-80 border-border/50 bg-card hidden lg:flex flex-col h-[calc(100vh-100px)]">
        <div className="p-4 border-b border-border/50">
          <h2 className="font-semibold text-sm">References</h2>
        </div>
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages[messages.length - 1]?.citations?.map((cit: any, i: number) => (
            <div key={i} className="p-3 bg-accent/30 rounded-lg border border-border/50">
              <div className="flex items-start space-x-2 mb-2">
                <FileText className="h-4 w-4 text-primary mt-0.5 shrink-0" />
                <p className="text-xs font-medium text-foreground leading-tight">{cit.document_name} <span className="text-muted-foreground">(pg. {cit.page_number})</span></p>
              </div>
              <p className="text-xs text-muted-foreground leading-relaxed italic border-l-2 border-primary/50 pl-2">"{cit.text_snippet}"</p>
            </div>
          ))}
          {!messages[messages.length - 1]?.citations?.length && (
            <p className="text-xs text-muted-foreground text-center mt-10">Citations will appear here.</p>
          )}
        </div>
      </Card>
    </div>
  );
}
