"use client";

import Link from "next/link";
import { Store, Plus, MessageSquare, X, ShoppingCart, User } from "lucide-react";
import { Conversation } from "@/lib/types";
import { cn } from "@/lib/cn";

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
  conversations: Conversation[];
  activeConversationId: string | null;
  onNewChat: () => void;
  onSelectConversation: (id: string) => void;
  cartItemCount: number;
  onOpenCart: () => void;
  userName?: string | null;
}

export function Sidebar({
  isOpen,
  onClose,
  conversations,
  activeConversationId,
  onNewChat,
  onSelectConversation,
  cartItemCount,
  onOpenCart,
  userName = null,
}: SidebarProps) {
  return (
    <>
      {/* Overlay for mobile */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/20 backdrop-blur-sm z-40 lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          "fixed top-0 left-0 h-full w-72 z-50 flex flex-col transition-transform duration-300 ease-out",
          "glass-strong shadow-2xl shadow-peach-200/20",
          isOpen ? "translate-x-0" : "-translate-x-full",
          "lg:relative lg:translate-x-0",
          !isOpen && "lg:hidden"
        )}
      >
        {/* Brand header */}
        <div className="flex items-center justify-between px-5 py-5 border-b border-peach-100/50">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-slate-800 text-white shadow-lg">
              <Store className="h-5 w-5" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-gray-900 tracking-tight">Aisle</h1>
              <p className="text-[10px] font-semibold text-gray-500">Your shopping sidekick</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="lg:hidden flex h-8 w-8 items-center justify-center rounded-xl hover:bg-peach-50 transition-colors"
          >
            <X className="h-4 w-4 text-peach-400" />
          </button>
        </div>

        {/* New Chat Button */}
        <div className="px-4 py-4">
          <button
            onClick={onNewChat}
            className="w-full flex items-center gap-2.5 btn-gradient rounded-2xl px-4 py-3 text-sm font-semibold"
          >
            <Plus className="h-4 w-4" />
            New Chat
          </button>
        </div>

        {/* Conversations list */}
        <div className="flex-1 overflow-y-auto px-3 pb-3">
          <p className="px-2 py-2 text-[10px] font-bold text-gray-400 tracking-widest uppercase">
            Recent Chats
          </p>
          {conversations.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-10 text-center">
              <MessageSquare className="h-8 w-8 text-peach-200 mb-3" />
              <p className="text-xs text-peach-300 font-medium">No conversations yet</p>
              <p className="text-[10px] text-peach-300/60 mt-1">Start chatting to see history</p>
            </div>
          ) : (
            <div className="space-y-1">
              {conversations.map((conv) => (
                <button
                  key={conv.id}
                  onClick={() => onSelectConversation(conv.id)}
                  className={cn(
                    "w-full flex items-start gap-3 rounded-xl px-3 py-2.5 text-left transition-all duration-200",
                    activeConversationId === conv.id
                      ? "bg-gradient-to-r from-peach-50 to-rose-50 border border-peach-200/50 shadow-sm"
                      : "hover:bg-peach-50/50"
                  )}
                >
                  <MessageSquare className={cn(
                    "h-4 w-4 mt-0.5 flex-shrink-0",
                    activeConversationId === conv.id ? "text-peach-500" : "text-peach-300"
                  )} />
                  <div className="min-w-0">
                    <p className={cn(
                      "text-[13px] font-medium truncate",
                      activeConversationId === conv.id ? "text-gray-900" : "text-gray-600"
                    )}>
                      {conv.title}
                    </p>
                    <p className="text-[10px] text-gray-400 mt-0.5">
                      {conv.messageCount} messages
                    </p>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Bottom section */}
        <div className="border-t border-peach-100/50 p-4 space-y-2">
          {/* Cart button */}
          <button
            onClick={onOpenCart}
            className="w-full flex items-center gap-3 rounded-xl px-3 py-2.5 hover:bg-peach-50/50 transition-all group"
          >
            <div className="relative">
              <ShoppingCart className="h-4.5 w-4.5 text-peach-400 group-hover:text-peach-500 transition-colors" />
              {cartItemCount > 0 && (
                <span className="absolute -top-1.5 -right-1.5 flex h-4 w-4 items-center justify-center rounded-full bg-gradient-to-br from-peach-500 to-rose-500 text-[9px] font-bold text-white shadow-sm">
                  {cartItemCount}
                </span>
              )}
            </div>
            <span className="text-[13px] font-medium text-gray-600 group-hover:text-gray-800">Shopping Cart</span>
          </button>

          {/* User */}
          <div className="flex items-center gap-3 rounded-xl px-3 py-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-200 text-slate-600">
              <User className="h-4 w-4" />
            </div>
            <div className="min-w-0">
              <p className="text-[13px] font-semibold text-gray-800 truncate">
                {userName || "Guest"}
              </p>
              {!userName && (
                <Link href="/signin" className="text-[11px] font-medium text-peach-600 hover:underline">
                  Sign in
                </Link>
              )}
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}
