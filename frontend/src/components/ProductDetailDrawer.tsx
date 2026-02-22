"use client";

import { X, Star, ShoppingCart, Minus, Plus, Check } from "lucide-react";
import { Product } from "@/lib/types";
import { cn } from "@/lib/cn";
import { useState } from "react";

interface ProductDetailDrawerProps {
  product: Product | null;
  isOpen: boolean;
  onClose: () => void;
  onAddToCart: (productId: number, quantity: number) => void;
}

export function ProductDetailDrawer({ product, isOpen, onClose, onAddToCart }: ProductDetailDrawerProps) {
  const [quantity, setQuantity] = useState(1);
  const [added, setAdded] = useState(false);

  if (!product) return null;

  const handleAdd = () => {
    onAddToCart(product.id, quantity);
    setQuantity(1);
    setAdded(true);
    setTimeout(() => {
      setAdded(false);
      onClose();
    }, 600);
  };

  return (
    <>
      {/* Strong blurred backdrop - no sidebar/cart UI, just this window */}
      <div
        className={cn(
          "fixed inset-0 z-40 transition-all duration-300 ease-out",
          isOpen ? "bg-black/55 backdrop-blur-lg" : "bg-transparent backdrop-blur-0 pointer-events-none"
        )}
        onClick={onClose}
        aria-hidden
      />

      {/* Centered modal - thick transparent gradient window */}
      <div
        className={cn(
          "fixed inset-0 z-50 flex items-center justify-center p-4 pointer-events-none",
          isOpen && "pointer-events-auto"
        )}
      >
        <div
          className={cn(
            "w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col rounded-3xl transition-all duration-300 ease-out",
            "bg-gradient-to-br from-white/95 via-white/90 to-peach-50/85 backdrop-blur-xl",
            "border-4 border-white/70 shadow-[0_0_0_1px_rgba(255,255,255,0.5),0_25px_50px_-12px_rgba(0,0,0,0.25)]",
            isOpen ? "opacity-100 scale-100" : "opacity-0 scale-95 pointer-events-none"
          )}
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex items-center justify-between px-4 sm:px-6 py-3 border-b border-white/50 flex-shrink-0 bg-white/30">
            <h2 className="text-[15px] font-bold text-gray-900">Product details</h2>
            <button
              onClick={onClose}
              className="flex h-9 w-9 items-center justify-center rounded-xl hover:bg-white/50 transition-colors"
            >
              <X className="h-5 w-5 text-gray-500" />
            </button>
          </div>

          {/* Scrollable content */}
          <div className="flex-1 overflow-y-auto overscroll-contain">
            <div className="flex flex-col sm:flex-row gap-6 p-4 sm:p-6">
              <div className="flex-shrink-0 w-full sm:w-72 h-64 sm:h-80 rounded-2xl flex items-center justify-center p-6 bg-gradient-to-br from-white/80 to-peach-50/50 border border-white/60">
                <img
                  src={product.image}
                  alt={product.title}
                  className="max-h-full object-contain animate-fade-in"
                />
              </div>

              <div className="flex-1 min-w-0 space-y-4">
                <div className="flex items-center justify-between flex-wrap gap-2">
                  <span className="text-[11px] font-bold text-peach-600 bg-peach-100/80 px-2.5 py-1 rounded-full uppercase tracking-wider">
                    {product.category}
                  </span>
                  {product.rating && (
                    <div className="flex items-center gap-1.5">
                      <div className="flex">
                        {[1, 2, 3, 4, 5].map((star) => (
                          <Star
                            key={star}
                            className={cn(
                              "h-3.5 w-3.5",
                              star <= Math.round(product.rating.rate)
                                ? "fill-amber-400 text-amber-400"
                                : "fill-gray-200 text-gray-200"
                            )}
                          />
                        ))}
                      </div>
                      <span className="text-[12px] font-medium text-gray-500">
                        ({product.rating.count} reviews)
                      </span>
                    </div>
                  )}
                </div>

                <h3 className="text-xl font-bold text-gray-900 tracking-tight leading-tight">
                  {product.title}
                </h3>

                <p className="text-2xl font-bold text-gradient">
                  ${product.price.toFixed(2)}
                </p>

                {product.description && (
                  <div>
                    <h4 className="text-[12px] font-bold text-gray-500 uppercase tracking-wider mb-2">Description</h4>
                    <p className="text-[14px] text-gray-600 leading-relaxed">
                      {product.description}
                    </p>
                  </div>
                )}

                <div>
                  <h4 className="text-[12px] font-bold text-gray-500 uppercase tracking-wider mb-2">Quantity</h4>
                  <div className="flex items-center gap-3">
                    <button
                      onClick={() => setQuantity(Math.max(1, quantity - 1))}
                      className="flex h-10 w-10 items-center justify-center rounded-xl bg-white/80 hover:bg-peach-100/80 border border-peach-100/50 transition-colors"
                    >
                      <Minus className="h-4 w-4 text-peach-500" />
                    </button>
                    <span className="w-12 text-center text-lg font-bold text-gray-900">{quantity}</span>
                    <button
                      onClick={() => setQuantity(quantity + 1)}
                      className="flex h-10 w-10 items-center justify-center rounded-xl bg-white/80 hover:bg-peach-100/80 border border-peach-100/50 transition-colors"
                    >
                      <Plus className="h-4 w-4 text-peach-500" />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="border-t border-white/50 px-4 sm:px-6 py-4 flex-shrink-0 bg-white/40">
            <button
              onClick={handleAdd}
              disabled={added}
              className={cn(
                "w-full rounded-2xl py-3.5 text-sm font-bold flex items-center justify-center gap-2 transition-all",
                added
                  ? "bg-emerald-500 text-white"
                  : "btn-gradient"
              )}
            >
              {added ? (
                <>
                  <Check className="h-4 w-4" />
                  Added to cart
                </>
              ) : (
                <>
                  <ShoppingCart className="h-4 w-4" />
                  Add to Cart — ${(product.price * quantity).toFixed(2)}
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
