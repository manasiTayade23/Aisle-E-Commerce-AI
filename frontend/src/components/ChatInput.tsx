"use client";

import { useState, useRef, useCallback } from "react";
import { ArrowUp, Paperclip } from "lucide-react";
import { cn } from "@/lib/cn";

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled: boolean;
}

export function ChatInput({ onSend, disabled }: ChatInputProps) {
  const [input, setInput] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = useCallback(() => {
    const trimmed = input.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setInput("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  }, [input, disabled, onSend]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    const el = e.target;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 150) + "px";
  };

  return (
    <div className={cn(
      "flex items-end gap-2.5 rounded-2xl border-2 bg-white/90 backdrop-blur-xl px-4 py-3 transition-all duration-300",
      "border-peach-200/50 shadow-md shadow-peach-200/15",
      "hover:border-peach-300/70 hover:shadow-lg hover:shadow-peach-200/25",
      "focus-within:border-peach-400/80 focus-within:shadow-xl focus-within:shadow-peach-300/30 focus-within:ring-2 focus-within:ring-peach-200/50"
    )}>
      <textarea
        ref={textareaRef}
        value={input}
        onChange={handleInput}
        onKeyDown={handleKeyDown}
        placeholder="Ask about products, compare items, manage your cart..."
        disabled={disabled}
        rows={1}
        className="flex-1 resize-none bg-transparent text-[15px] text-gray-800 placeholder:text-gray-400 focus:outline-none disabled:opacity-50 leading-relaxed"
      />
      <button
        onClick={handleSubmit}
        disabled={disabled || !input.trim()}
        className={cn(
          "flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-xl transition-all duration-200",
          input.trim() && !disabled
            ? "btn-gradient !shadow-md !shadow-peach-200/40 active:scale-90"
            : "bg-peach-50 text-peach-300"
        )}
      >
        <ArrowUp className="h-4.5 w-4.5" strokeWidth={2.5} />
      </button>
    </div>
  );
}
