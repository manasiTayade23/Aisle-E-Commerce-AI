"use client";

import { useState, useEffect } from "react";

const STATUSES: { emoji: string; label: string }[] = [
  { emoji: "🔍", label: "Searching the catalog..." },
  { emoji: "📂", label: "Filtering results..." },
  { emoji: "🛒", label: "Browsing products..." },
  { emoji: "⚖️", label: "Comparing options..." },
  { emoji: "✨", label: "Finding the best match..." },
  { emoji: "📦", label: "Checking availability..." },
];

const ROTATE_MS = 2200;

export function ThinkingStatus() {
  const [index, setIndex] = useState(0);

  useEffect(() => {
    const id = setInterval(() => {
      setIndex((i) => (i + 1) % STATUSES.length);
    }, ROTATE_MS);
    return () => clearInterval(id);
  }, []);

  const { emoji, label } = STATUSES[index];

  return (
    <div className="inline-flex items-center gap-2.5 rounded-2xl bg-white/95 backdrop-blur-sm border-2 border-peach-200/60 px-4 py-2.5 shadow-md shadow-peach-200/20 rounded-tl-sm rounded-br-2xl ring-1 ring-peach-100/50">
      <span className="text-base animate-pulse" key={index}>
        {emoji}
      </span>
      <span className="text-[13px] font-medium text-gray-700">{label}</span>
      <span className="flex items-center gap-1 ml-1">
        <span className="h-1.5 w-1.5 rounded-full bg-peach-400 animate-pulse" style={{ animationDelay: "0ms" }} />
        <span className="h-1.5 w-1.5 rounded-full bg-peach-300 animate-pulse" style={{ animationDelay: "150ms" }} />
        <span className="h-1.5 w-1.5 rounded-full bg-peach-200 animate-pulse" style={{ animationDelay: "300ms" }} />
      </span>
    </div>
  );
}
