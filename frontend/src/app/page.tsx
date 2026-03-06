"use client";

import { useCallback, useEffect, useState } from "react";
import { ChatInput } from "@/components/ChatInput";
import { ChatMessage } from "@/components/ChatMessage";
import { Sidebar } from "@/components/Sidebar";
import { Message, createSession, streamChat } from "@/lib/api";

type SessionItem = { id: string; title?: string };

export default function Home() {
  const [sessions, setSessions] = useState<SessionItem[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const startNewSession = useCallback(async () => {
    try {
      const { session_id } = await createSession();
      setSessions((prev) => [{ id: session_id, title: "New chat" }, ...prev]);
      setCurrentSessionId(session_id);
      setMessages([]);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to create session");
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    createSession()
      .then(({ session_id }) => {
        if (!cancelled) {
          setSessions([{ id: session_id, title: "New chat" }]);
          setCurrentSessionId(session_id);
        }
      })
      .catch((e) => {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : "Backend not available. Start it with: python3 -m uvicorn backend.app.main:app --port 8001");
        }
      });
    return () => { cancelled = true; };
  }, []);

  const handleSend = useCallback(
    (content: string) => {
      const userMessage: Message = { role: "user", content };
      setMessages((prev) => [...prev, userMessage]);
      setLoading(true);
      setError(null);

      const updatedMessages: Message[] = [...messages, userMessage];

      streamChat(
        updatedMessages,
        currentSessionId,
        (chunk) => {
          setMessages((prev) => {
            const next = [...prev];
            const last = next[next.length - 1];
            if (last?.role === "assistant") {
              next[next.length - 1] = { ...last, content: last.content + chunk };
            } else {
              next.push({ role: "assistant", content: chunk });
            }
            return next;
          });
        },
        () => setLoading(false),
        (err) => {
          setError(err.message);
          setLoading(false);
          setMessages((prev) => [
            ...prev,
            {
              role: "assistant",
              content: `I couldn't generate a response.\n\n${err.message}\n\nTo get real answers, you need vLLM running with a model. From a terminal (with a GPU):\n\n\`\`\`bash\npip install vllm\nvllm serve Qwen/Qwen2.5-Coder-7B-Instruct --dtype auto --port 8000\n\`\`\`\n\nThen ensure the backend's VLLM_BASE_URL is http://localhost:8000 and try again.`,
            },
          ]);
        }
      ).catch(() => {
        setLoading(false);
      });
    },
    [messages, currentSessionId]
  );

  const handleSelectSession = useCallback((id: string) => {
    setCurrentSessionId(id);
    setMessages([]);
    setError(null);
    // In a full app you'd load session messages from API here
  }, []);

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar
        sessions={sessions}
        currentId={currentSessionId}
        onNewChat={startNewSession}
        onSelect={handleSelectSession}
      />
      <main className="flex-1 flex flex-col min-w-0 bg-[var(--bg)]">
        <header className="shrink-0 border-b border-white/10 px-6 py-4">
          <h1 className="text-lg font-semibold text-zinc-200">Coding Assistant</h1>
          <p className="text-sm text-zinc-500">Streaming from your SLM</p>
        </header>

        <div className="flex-1 overflow-y-auto px-6 py-4">
          <div className="max-w-3xl mx-auto space-y-6">
            {messages.length === 0 && !loading && (
              <div className="rounded-2xl border border-dashed border-white/15 bg-white/5 p-12 text-center">
                <p className="text-zinc-400 text-sm">Send a message to start. Try:</p>
                <p className="mt-2 text-zinc-300 font-mono text-sm">
                  Write a Python function to reverse a string
                </p>
              </div>
            )}
            {messages.map((msg, i) => (
              <ChatMessage
                key={i}
                role={msg.role}
                content={msg.content}
                isStreaming={loading && i === messages.length - 1 && msg.role === "assistant"}
              />
            ))}
          </div>
        </div>

        {error && (
          <div className="shrink-0 px-6 py-2 bg-red-500/10 border-t border-red-500/20 text-red-400 text-sm">
            {error}
          </div>
        )}

        <div className="shrink-0 p-4 border-t border-white/10">
          <div className="max-w-3xl mx-auto">
            <ChatInput onSend={handleSend} disabled={loading} />
          </div>
        </div>
      </main>
    </div>
  );
}
