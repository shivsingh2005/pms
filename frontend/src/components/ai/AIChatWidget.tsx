"use client";

import { useState } from "react";
import { usePathname } from "next/navigation";
import { MessageCircle, Send, Sparkles } from "lucide-react";
import { motion } from "framer-motion";
import { useAIStore } from "@/store/useAIStore";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export function AIChatWidget() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const [value, setValue] = useState("");
  const { messages, ask, loading, suggestedActions } = useAIStore();

  const submit = async () => {
    if (!value.trim()) return;
    const query = value;
    setValue("");
    await ask(query, pathname);
  };

  return (
    <div className="fixed bottom-6 right-6 z-50">
      {open && (
        <motion.div
          initial={{ opacity: 0, y: 18, scale: 0.98 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          transition={{ duration: 0.2, ease: "easeOut" }}
          className="mb-3 w-[360px] overflow-hidden rounded-2xl border border-border/75 bg-card shadow-floating"
        >
          <div className="flex items-center gap-2 bg-gradient-to-r from-primary via-indigo-500 to-secondary px-4 py-3 text-primary-foreground">
            <Sparkles className="h-4 w-4" />
            <div className="text-sm font-semibold">AI Assistant</div>
          </div>
          <div className="p-3.5">
          <div className="mb-3 h-64 space-y-2 overflow-y-auto rounded-xl border border-border/70 bg-surface/70 p-3">
            {messages.length === 0 && <div className="text-xs text-muted-foreground">Ask: What should I do next?</div>}
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`rounded-2xl px-3 py-2 text-sm leading-relaxed ${msg.role === "user" ? "ml-8 bg-primary text-primary-foreground" : "mr-8 border border-border/70 bg-card text-foreground"}`}
              >
                {msg.content}
              </div>
            ))}
            {loading && (
              <div className="inline-flex items-center gap-1 rounded-full bg-muted px-3 py-1 text-xs text-muted-foreground">
                <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-primary [animation-delay:-0.2s]" />
                <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-primary [animation-delay:-0.1s]" />
                <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-primary" />
              </div>
            )}
          </div>
          {suggestedActions.length > 0 && (
            <div className="mb-2 flex flex-wrap gap-2">
              {suggestedActions.slice(0, 3).map((action) => (
                <button
                  key={action}
                  className="rounded-full border border-border/70 px-2.5 py-1 text-xs text-muted-foreground transition hover:bg-muted/70"
                  onClick={() => setValue(action)}
                >
                  {action}
                </button>
              ))}
            </div>
          )}
          <div className="flex gap-2">
            <Input value={value} onChange={(e) => setValue(e.target.value)} placeholder="Ask about goals, ratings, next actions..." />
            <Button size="sm" onClick={submit} className="rounded-full" aria-label="Send AI message">
              <Send className="h-4 w-4" />
            </Button>
          </div>
          </div>
        </motion.div>
      )}
      <Button onClick={() => setOpen((v) => !v)} className="h-12 w-12 rounded-full p-0 shadow-floating" aria-label="Toggle AI assistant">
        <MessageCircle className="h-5 w-5" />
      </Button>
    </div>
  );
}

