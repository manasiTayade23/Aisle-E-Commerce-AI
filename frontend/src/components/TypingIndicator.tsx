"use client";

export function TypingIndicator() {
  return (
    <div className="flex items-center gap-1.5 py-1 px-0.5">
      <div className="h-2 w-2 rounded-full bg-gradient-to-br from-peach-400 to-rose-400 animate-pulse-dot" style={{ animationDelay: "0ms" }} />
      <div className="h-2 w-2 rounded-full bg-gradient-to-br from-rose-400 to-peach-300 animate-pulse-dot" style={{ animationDelay: "200ms" }} />
      <div className="h-2 w-2 rounded-full bg-gradient-to-br from-peach-300 to-rose-400 animate-pulse-dot" style={{ animationDelay: "400ms" }} />
    </div>
  );
}
