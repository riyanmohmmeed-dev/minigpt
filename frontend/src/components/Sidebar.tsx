"use client";

type Session = { id: string; title?: string };

type SidebarProps = {
  sessions: Session[];
  currentId: string | null;
  onNewChat: () => void;
  onSelect: (id: string) => void;
};

export function Sidebar({ sessions, currentId, onNewChat, onSelect }: SidebarProps) {
  return (
    <aside className="w-64 shrink-0 flex flex-col border-r border-white/10 bg-black/20 backdrop-blur">
      <div className="p-3 border-b border-white/10">
        <button
          type="button"
          onClick={onNewChat}
          className="w-full flex items-center gap-2 px-3 py-2.5 rounded-xl bg-violet-600/80 hover:bg-violet-500 text-white text-sm font-medium transition"
        >
          <span className="text-lg">+</span>
          New chat
        </button>
      </div>
      <nav className="flex-1 overflow-y-auto p-2">
        {sessions.length === 0 && (
          <p className="px-3 py-2 text-zinc-500 text-sm">No chats yet</p>
        )}
        {sessions.map((s) => (
          <button
            key={s.id}
            type="button"
            onClick={() => onSelect(s.id)}
            className={`w-full text-left px-3 py-2.5 rounded-lg text-sm transition ${
              currentId === s.id
                ? "bg-white/10 text-white"
                : "text-zinc-400 hover:bg-white/5 hover:text-zinc-200"
            }`}
          >
            {s.title || `Chat ${s.id.slice(0, 8)}`}
          </button>
        ))}
      </nav>
      <div className="p-2 border-t border-white/10">
        <p className="px-3 py-1 text-xs text-zinc-500">Mini-ChatGPT Coding</p>
      </div>
    </aside>
  );
}
