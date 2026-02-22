"use client";

import { ShoppingBag, Laptop, Gem, Shirt, ArrowRight } from "lucide-react";

const SUGGESTIONS = [
  { text: "Show me electronics under $100", icon: Laptop, gradient: "from-blue-400 to-cyan-400" },
  { text: "What jewelry do you have?", icon: Gem, gradient: "from-peach-300 to-rose-400" },
  { text: "Find me a men's casual shirt", icon: Shirt, gradient: "from-emerald-400 to-teal-400" },
  { text: "What are your top-rated products?", icon: ShoppingBag, gradient: "from-peach-400 to-pink-400" },
];

export function SuggestedPrompts({ onSelect }: { onSelect: (text: string) => void }) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-lg mx-auto w-full">
      {SUGGESTIONS.map((s) => {
        const Icon = s.icon;
        return (
          <button
            key={s.text}
            onClick={() => onSelect(s.text)}
            className="group relative flex items-center gap-3 rounded-2xl bg-white/70 backdrop-blur-sm border border-peach-100/40 px-4 py-4 text-left text-[13px] font-medium text-gray-600 transition-all duration-300 hover:bg-white/90 hover:border-peach-200/60 hover:shadow-xl hover:shadow-peach-200/15 hover:-translate-y-0.5 active:scale-[0.97]"
          >
            <div className={`flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br ${s.gradient} shadow-sm flex-shrink-0 transition-transform duration-300 group-hover:scale-110`}>
              <Icon className="h-4 w-4 text-white" />
            </div>
            <span className="group-hover:text-gray-900 transition-colors">{s.text}</span>
            <ArrowRight className="h-3.5 w-3.5 text-peach-300 ml-auto opacity-0 group-hover:opacity-100 transition-all duration-300 -translate-x-2 group-hover:translate-x-0" />
          </button>
        );
      })}
    </div>
  );
}
