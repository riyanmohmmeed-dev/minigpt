"use client";

import { useCallback, useRef, useState } from "react";

type ChatInputProps = {
  onSend: (text: string) => void;
  disabled?: boolean;
  placeholder?: string;
};

const MIN_ROWS = 1;
const MAX_ROWS = 8;

export function ChatInput({
  onSend,
  disabled = false,
  placeholder = "Ask for code or an explanation... (Enter to send, Shift+Enter for new line)",
}: ChatInputProps) {
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const submit = useCallback(() => {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setValue("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  }, [value, disabled, onSend]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        submit();
      }
    },
    [submit]
  );

  const handleChange = useCallback((e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setValue(e.target.value);
    const el = e.target;
    el.style.height = "auto";
    el.style.height = `${Math.min(MAX_ROWS * 24, Math.max(MIN_ROWS * 24, el.scrollHeight))}px`;
  }, []);

  return (
    <div className="flex gap-2 items-end rounded-2xl border border-white/10 bg-white/5 backdrop-blur p-2 focus-within:ring-2 focus-within:ring-violet-500/50 focus-within:border-violet-500/50 transition">
      <textarea
        ref={textareaRef}
        value={value}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        disabled={disabled}
        rows={MIN_ROWS}
        className="flex-1 min-h-[2.5rem] max-h-[12rem] resize-none bg-transparent px-3 py-2 text-sm text-zinc-200 placeholder-zinc-500 outline-none disabled:opacity-50"
      />
      <button
        type="button"
        onClick={submit}
        disabled={disabled || !value.trim()}
        className="shrink-0 h-10 px-4 rounded-xl bg-violet-600 hover:bg-violet-500 disabled:opacity-40 disabled:pointer-events-none text-white font-medium text-sm transition"
      >
        Send
      </button>
    </div>
  );
}
