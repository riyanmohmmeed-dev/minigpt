"use client";

import { useCallback, useState } from "react";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark } from "react-syntax-highlighter/dist/esm/styles/prism";

type MessageBubbleProps = {
  role: "user" | "assistant";
  content: string;
  isStreaming?: boolean;
};

function CodeBlock({ code, language }: { code: string; language: string }) {
  const [copied, setCopied] = useState(false);
  const copy = useCallback(() => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }, [code]);

  return (
    <div className="group relative mt-2 rounded-lg overflow-hidden border border-white/10 bg-black/30">
      <div className="flex items-center justify-between px-3 py-1.5 bg-white/5 border-b border-white/10">
        <span className="text-xs text-zinc-400 font-mono">{language || "code"}</span>
        <button
          type="button"
          onClick={copy}
          className="text-xs px-2 py-1 rounded bg-white/10 hover:bg-white/20 text-zinc-300 transition"
        >
          {copied ? "Copied" : "Copy"}
        </button>
      </div>
      <SyntaxHighlighter
        language={language || "text"}
        style={oneDark}
        customStyle={{
          margin: 0,
          padding: "0.75rem 1rem",
          background: "transparent",
          fontSize: "0.8125rem",
        }}
        codeTagProps={{ style: { fontFamily: "var(--font-geist-mono), ui-monospace, monospace" } }}
        showLineNumbers={false}
        PreTag="pre"
      >
        {code}
      </SyntaxHighlighter>
    </div>
  );
}

function parseContent(content: string): React.ReactNode[] {
  const parts: React.ReactNode[] = [];
  const re = /```(\w*)\n?([\s\S]*?)```/g;
  let lastIndex = 0;
  let match;
  while ((match = re.exec(content)) !== null) {
    if (match.index > lastIndex) {
      const text = content.slice(lastIndex, match.index);
      parts.push(<span key={`t-${lastIndex}`} className="whitespace-pre-wrap">{text}</span>);
    }
    parts.push(
      <CodeBlock key={`c-${match.index}`} code={match[2].trim()} language={match[1] || "text"} />
    );
    lastIndex = re.lastIndex;
  }
  if (lastIndex < content.length) {
    parts.push(
      <span key={`t-${lastIndex}`} className="whitespace-pre-wrap">
        {content.slice(lastIndex)}
      </span>
    );
  }
  return parts.length ? parts : [<span key="0" className="whitespace-pre-wrap">{content}</span>];
}

export function ChatMessage({ role, content, isStreaming }: MessageBubbleProps) {
  const isUser = role === "user";
  const parsed = parseContent(content);

  return (
    <div className={`flex w-full animate-fade-in ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`
          max-w-[85%] rounded-2xl px-4 py-3 shadow-lg
          ${isUser
            ? "bg-violet-600/90 text-white"
            : "bg-white/5 backdrop-blur border border-white/10 text-zinc-200"
          }
        `}
      >
        <div className="prose prose-invert prose-sm max-w-none prose-p:my-1 prose-pre:my-2 prose-code:bg-white/10 prose-code:px-1 prose-code:rounded">
          {parsed}
        </div>
        {isStreaming && (
          <span className="inline-block w-2 h-4 ml-0.5 bg-violet-400 animate-pulse-soft" />
        )}
      </div>
    </div>
  );
}
