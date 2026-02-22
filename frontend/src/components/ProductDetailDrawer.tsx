"use client";

import { X, Star, ShoppingCart, Minus, Plus } from "lucide-react";
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

  if (!product) return null;

  const handleAdd = () => {
    onAddToCart(product.id, quantity);
    setQuantity(1);
    onClose();
  };

  return (
    <>
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/20 backdrop-blur-sm z-50"
          onClick={onClose}
        />
      )}

      <div
        className={cn(
          "fixed top-0 right-0 h-full w-full sm:w-[28rem] z-50 flex flex-col transition-transform duration-300 ease-out",
          "glass-strong shadow-2xl shadow-peach-200/30",
          isOpen ? "translate-x-0" : "translate-x-full"
        )}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-peach-100/50">
          <h2 className="text-[15px] font-bold text-gray-900">Product Details</h2>
          <button
            onClick={onClose}
            className="flex h-8 w-8 items-center justify-center rounded-xl hover:bg-peach-50 transition-colors"
          >
            <X className="h-4 w-4 text-gray-400" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto">
          {/* Image */}
          <div className="relative bg-white p-8 flex items-center justify-center">
            <div className="absolute inset-0 bg-gradient-to-b from-peach-50/50 to-transparent" />
            <img
              src={product.image}
              alt={product.title}
              className="relative z-10 max-h-64 object-contain animate-fade-in"
            />
          </div>

          <div className="px-5 py-5 space-y-4">
            {/* Category & Rating */}
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold text-peach-500 bg-peach-50 px-2.5 py-1 rounded-full uppercase tracking-wider">
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
                    ({product.rating.count})
                  </span>
                </div>
              )}
            </div>

            {/* Title */}
            <h3 className="text-xl font-bold text-gray-900 tracking-tight leading-tight">
              {product.title}
            </h3>

            {/* Price */}
            <p className="text-2xl font-bold text-gradient">
              ${product.price.toFixed(2)}
            </p>

            {/* Description */}
            {product.description && (
              <div>
                <h4 className="text-[12px] font-bold text-gray-400 uppercase tracking-wider mb-2">Description</h4>
                <p className="text-[14px] text-gray-600 leading-relaxed">
                  {product.description}
                </p>
              </div>
            )}

            {/* Quantity selector */}
            <div>
              <h4 className="text-[12px] font-bold text-gray-400 uppercase tracking-wider mb-2">Quantity</h4>
              <div className="flex items-center gap-3">
                <button
                  onClick={() => setQuantity(Math.max(1, quantity - 1))}
                  className="flex h-10 w-10 items-center justify-center rounded-xl bg-peach-50 hover:bg-peach-100 transition-colors"
                >
                  <Minus className="h-4 w-4 text-peach-500" />
                </button>
                <span className="w-12 text-center text-lg font-bold text-gray-900">{quantity}</span>
                <button
                  onClick={() => setQuantity(quantity + 1)}
                  className="flex h-10 w-10 items-center justify-center rounded-xl bg-peach-50 hover:bg-peach-100 transition-colors"
                >
                  <Plus className="h-4 w-4 text-peach-500" />
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Add to Cart */}
        <div className="border-t border-peach-100/50 px-5 py-4">
          <button
            onClick={handleAdd}
            className="w-full btn-gradient rounded-2xl py-3.5 text-sm font-bold flex items-center justify-center gap-2"
          >
            <ShoppingCart className="h-4 w-4" />
            Add to Cart — ${(product.price * quantity).toFixed(2)}
          </button>
        </div>
      </div>
    </>
  );
}
