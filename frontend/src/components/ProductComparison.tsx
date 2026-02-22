"use client";

import { Product } from "@/lib/types";
import { Star, TrendingDown, TrendingUp, ShoppingCart } from "lucide-react";
import { cn } from "@/lib/cn";

interface ProductComparisonProps {
  products: Product[];
  onAddToCart?: (productId: number) => void;
}

export function ProductComparison({ products, onAddToCart }: ProductComparisonProps) {
  if (products.length < 2) return null;

  const [a, b] = products;
  const cheaper = a.price <= b.price ? a : b;
  const priceDiff = Math.abs(a.price - b.price);
  const betterRated = (a.rating?.rate || 0) >= (b.rating?.rate || 0) ? a : b;

  return (
    <div className="w-full animate-fade-in">
      <div className="grid grid-cols-2 gap-3">
        {[a, b].map((product) => (
          <div
            key={product.id}
            className={cn(
              "relative rounded-2xl bg-white/70 border p-3.5 backdrop-blur-sm transition-all",
              product.id === cheaper.id
                ? "border-emerald-200/60 shadow-md shadow-emerald-100/30"
                : "border-peach-100/40"
            )}
          >
            {/* Best value badge */}
            {product.id === cheaper.id && (
              <div className="absolute -top-2.5 left-3 px-2.5 py-0.5 rounded-full bg-gradient-to-r from-emerald-400 to-teal-400 text-[9px] font-bold text-white uppercase tracking-wider shadow-sm">
                Best Value
              </div>
            )}

            {/* Image */}
            <div className="h-24 w-full flex items-center justify-center bg-white rounded-xl p-3 mb-3">
              <img
                src={product.image}
                alt={product.title}
                className="max-h-full object-contain"
              />
            </div>

            {/* Details */}
            <h4 className="text-[12px] font-semibold text-gray-900 line-clamp-2 leading-snug tracking-tight mb-2">
              {product.title}
            </h4>

            <p className="text-[10px] font-bold text-peach-600/70 capitalize tracking-widest uppercase mb-2">
              {product.category}
            </p>

            {/* Price */}
            <p className={cn(
              "text-lg font-bold tracking-tight",
              product.id === cheaper.id ? "text-emerald-600" : "text-gradient"
            )}>
              ${product.price.toFixed(2)}
            </p>

            {/* Rating */}
            {product.rating && (
              <div className="flex items-center gap-1 mt-1.5">
                <Star className="h-3 w-3 fill-amber-400 text-amber-400" />
                <span className="text-[11px] font-semibold text-gray-600">
                  {product.rating.rate}
                </span>
                <span className="text-[10px] text-gray-400">
                  ({product.rating.count} reviews)
                </span>
              </div>
            )}

            {/* Add to cart */}
            {onAddToCart && (
              <button
                onClick={() => onAddToCart(product.id)}
                className="mt-3 w-full flex items-center justify-center gap-1.5 rounded-xl bg-gradient-to-r from-peach-50 to-rose-50 border border-peach-200/50 py-2 text-[11px] font-semibold text-peach-600 hover:from-peach-100 hover:to-peach-100 transition-all active:scale-[0.97]"
              >
                <ShoppingCart className="h-3 w-3" />
                Add to Cart
              </button>
            )}
          </div>
        ))}
      </div>

      {/* Price difference */}
      <div className="flex items-center justify-center gap-2 mt-3 py-2 px-4 rounded-xl bg-gradient-to-r from-peach-50/80 to-rose-50/60 border border-peach-100/30">
        <TrendingDown className="h-3.5 w-3.5 text-emerald-500" />
        <span className="text-[12px] font-semibold text-gray-600">
          <span className="font-bold text-emerald-600">{cheaper.title.split(" ").slice(0, 3).join(" ")}...</span>
          {" "}is <span className="font-bold text-emerald-600">${priceDiff.toFixed(2)} cheaper</span>
        </span>
      </div>
    </div>
  );
}
