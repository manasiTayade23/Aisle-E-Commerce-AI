"use client";

import { useState } from "react";
import { X, Minus, Plus, ShoppingBag, Trash2, CreditCard, ArrowLeft } from "lucide-react";
import { CartItem } from "@/lib/types";
import { cn } from "@/lib/cn";

interface CartDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  items: CartItem[];
  onUpdateQuantity: (productId: number, quantity: number) => void;
  onRemoveItem: (productId: number) => void;
}

export function CartDrawer({ isOpen, onClose, items, onUpdateQuantity, onRemoveItem }: CartDrawerProps) {
  const [view, setView] = useState<"cart" | "checkout">("cart");

  const subtotal = items.reduce((sum, item) => sum + item.item_total, 0);
  const tax = subtotal * 0.08;
  const total = subtotal + tax;
  const totalQuantity = items.reduce((sum, item) => sum + item.quantity, 0);

  const handleClose = () => {
    setView("cart");
    onClose();
  };

  return (
    <>
      {/* Overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/20 backdrop-blur-sm z-50"
          onClick={handleClose}
        />
      )}

      {/* Drawer */}
      <div
        className={cn(
          "fixed top-0 right-0 h-full w-full sm:w-96 z-50 flex flex-col transition-transform duration-300 ease-out",
          "glass-strong shadow-2xl shadow-peach-200/30",
          isOpen ? "translate-x-0" : "translate-x-full"
        )}
      >
        {view === "cart" ? (
          <>
            {/* Header */}
            <div className="flex items-center justify-between px-5 py-4 border-b border-peach-100/50">
              <div className="flex items-center gap-2.5">
                <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-slate-100">
                  <ShoppingBag className="h-4.5 w-4.5 text-slate-600" />
                </div>
                <div>
                  <h2 className="text-[15px] font-bold text-gray-900">Shopping Cart</h2>
                  <p className="text-[11px] text-gray-400 font-medium">{totalQuantity} item{totalQuantity !== 1 ? "s" : ""}</p>
                </div>
              </div>
              <button
                onClick={handleClose}
                className="flex h-8 w-8 items-center justify-center rounded-xl hover:bg-peach-50 transition-colors"
              >
                <X className="h-4 w-4 text-gray-400" />
              </button>
            </div>

            {/* Items */}
            <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3">
          {items.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-peach-50 mb-4">
                <ShoppingBag className="h-8 w-8 text-peach-300" />
              </div>
              <p className="text-sm font-medium text-gray-500">Your cart is empty</p>
              <p className="text-xs text-gray-400 mt-1">Ask me to add products to your cart!</p>
            </div>
          ) : (
            items.map((item) => (
              <div
                key={item.product_id}
                className="flex gap-3 rounded-2xl bg-white/70 border border-peach-100/40 p-3 animate-fade-in shadow-sm"
              >
                <div className="h-16 w-16 flex-shrink-0 overflow-hidden rounded-xl bg-white p-1.5">
                  <img
                    src={item.image}
                    alt={item.title}
                    className="h-full w-full object-contain"
                  />
                </div>
                <div className="flex-1 min-w-0">
                  <h4 className="text-[13px] font-semibold text-gray-900 line-clamp-1 tracking-tight">
                    {item.title}
                  </h4>
                  <p className="text-[13px] font-bold text-gradient mt-0.5">
                    ${item.price.toFixed(2)}
                  </p>

                  <div className="flex items-center justify-between mt-2">
                    {/* Quantity controls */}
                    <div className="flex items-center gap-1.5">
                      <button
                        onClick={() => onUpdateQuantity(item.product_id, Math.max(0, item.quantity - 1))}
                        className="flex h-7 w-7 items-center justify-center rounded-lg bg-peach-50 hover:bg-peach-100 transition-colors"
                      >
                        <Minus className="h-3 w-3 text-peach-500" />
                      </button>
                      <span className="w-8 text-center text-sm font-semibold text-gray-900">{item.quantity}</span>
                      <button
                        onClick={() => onUpdateQuantity(item.product_id, item.quantity + 1)}
                        className="flex h-7 w-7 items-center justify-center rounded-lg bg-peach-50 hover:bg-peach-100 transition-colors"
                      >
                        <Plus className="h-3 w-3 text-peach-500" />
                      </button>
                    </div>

                    <div className="flex items-center gap-2">
                      <span className="text-[13px] font-bold text-gray-900">${item.item_total.toFixed(2)}</span>
                      <button
                        onClick={() => onRemoveItem(item.product_id)}
                        className="flex h-7 w-7 items-center justify-center rounded-lg hover:bg-red-50 transition-colors"
                      >
                        <Trash2 className="h-3.5 w-3.5 text-red-400" />
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>

            {/* Footer with totals */}
            {items.length > 0 && (
              <div className="border-t border-peach-100/50 px-5 py-4 space-y-3">
                <div className="space-y-1.5">
                  <div className="flex justify-between text-[13px]">
                    <span className="text-gray-500">Subtotal</span>
                    <span className="font-medium text-gray-700">${subtotal.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between text-[13px]">
                    <span className="text-gray-500">Tax (8%)</span>
                    <span className="font-medium text-gray-700">${tax.toFixed(2)}</span>
                  </div>
                  <div className="h-px bg-peach-100/50 my-1" />
                  <div className="flex justify-between">
                    <span className="text-sm font-bold text-gray-900">Total</span>
                    <span className="text-lg font-bold text-gradient">${total.toFixed(2)}</span>
                  </div>
                </div>
                <button
                  onClick={() => setView("checkout")}
                  className="w-full btn-gradient rounded-2xl py-3 text-sm font-bold"
                >
                  Checkout
                </button>
              </div>
            )}
          </>
        ) : (
          /* Checkout / Payment view */
          <>
            <div className="flex items-center justify-between px-5 py-4 border-b border-peach-100/50">
              <button
                onClick={() => setView("cart")}
                className="flex items-center gap-2 text-sm font-semibold text-gray-700 hover:text-peach-600"
              >
                <ArrowLeft className="h-4 w-4" />
                Back to cart
              </button>
              <button
                onClick={handleClose}
                className="flex h-8 w-8 items-center justify-center rounded-xl hover:bg-peach-50"
              >
                <X className="h-4 w-4 text-gray-400" />
              </button>
            </div>
            <div className="flex-1 overflow-y-auto px-5 py-5 space-y-5">
              <h2 className="text-lg font-bold text-gray-900">Checkout</h2>
              <div className="rounded-2xl border border-peach-100/50 bg-white/80 p-4 space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Order total ({totalQuantity} items)</span>
                  <span className="font-bold text-gray-900">${total.toFixed(2)}</span>
                </div>
              </div>
              <div className="space-y-3">
                <h3 className="text-sm font-bold text-gray-800 flex items-center gap-2">
                  <CreditCard className="h-4 w-4" />
                  Payment
                </h3>
                <div className="space-y-3">
                  <div>
                    <label className="block text-xs font-semibold text-gray-600 mb-1">Card number</label>
                    <input
                      type="text"
                      placeholder="4242 4242 4242 4242"
                      className="w-full rounded-xl border border-peach-200/50 px-3 py-2.5 text-sm placeholder:text-gray-400"
                      readOnly
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-xs font-semibold text-gray-600 mb-1">Expiry</label>
                      <input
                        type="text"
                        placeholder="MM/YY"
                        className="w-full rounded-xl border border-peach-200/50 px-3 py-2.5 text-sm placeholder:text-gray-400"
                        readOnly
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-semibold text-gray-600 mb-1">CVC</label>
                      <input
                        type="text"
                        placeholder="123"
                        className="w-full rounded-xl border border-peach-200/50 px-3 py-2.5 text-sm placeholder:text-gray-400"
                        readOnly
                      />
                    </div>
                  </div>
                </div>
                <p className="text-xs text-gray-500 font-medium">
                  Payment integration is not connected. This is a demo checkout screen.
                </p>
              </div>
            </div>
            <div className="border-t border-peach-100/50 px-5 py-4">
              <button
                className="w-full rounded-2xl py-3 text-sm font-bold bg-gray-200 text-gray-500 cursor-not-allowed"
                disabled
              >
                Place order (demo)
              </button>
            </div>
          </>
        )}
      </div>
    </>
  );
}
