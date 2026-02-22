"use client";

import { Product } from "@/lib/types";
import { Star, ShoppingCart, DollarSign, Award, MessageSquare, Tag } from "lucide-react";
import { cn } from "@/lib/cn";

interface ProductComparisonProps {
  products: Product[];
  onAddToCart?: (productId: number) => void;
  onViewDetails?: (product: Product) => void;
}

type CriterionKey = "price" | "rating" | "reviews" | "category" | "description";

const CRITERIA: { key: CriterionKey; label: string; icon: React.ReactNode }[] = [
  { key: "price", label: "Price", icon: <DollarSign className="h-3.5 w-3.5" /> },
  { key: "rating", label: "Rating", icon: <Star className="h-3.5 w-3.5 fill-amber-400 text-amber-400" /> },
  { key: "reviews", label: "Reviews", icon: <MessageSquare className="h-3.5 w-3.5" /> },
  { key: "category", label: "Category", icon: <Tag className="h-3.5 w-3.5" /> },
  { key: "description", label: "Description", icon: <Award className="h-3.5 w-3.5" /> },
];

function getCellValue(product: Product, key: CriterionKey): string | number {
  switch (key) {
    case "price":
      return `$${product.price.toFixed(2)}`;
    case "rating":
      return product.rating ? product.rating.rate.toFixed(1) : "—";
    case "reviews":
      return product.rating ? product.rating.count : "—";
    case "category":
      return product.category ?? "—";
    case "description":
      return product.description ? product.description.slice(0, 80) + (product.description.length > 80 ? "…" : "") : "—";
    default:
      return "—";
  }
}

/** Index of the best product for this criterion (0-based). Lower price = better; higher rating/reviews = better. */
function getBestIndex(products: Product[], key: CriterionKey): number | null {
  if (key === "category" || key === "description") return null;
  if (products.length === 0) return null;
  if (key === "price") {
    let best = 0;
    for (let i = 1; i < products.length; i++) if (products[i].price < products[best].price) best = i;
    return best;
  }
  if (key === "rating") {
    let best = 0;
    const rate = (p: Product) => p.rating?.rate ?? 0;
    for (let i = 1; i < products.length; i++) if (rate(products[i]) > rate(products[best])) best = i;
    return best;
  }
  if (key === "reviews") {
    let best = 0;
    const count = (p: Product) => p.rating?.count ?? 0;
    for (let i = 1; i < products.length; i++) if (count(products[i]) > count(products[best])) best = i;
    return best;
  }
  return null;
}

function shortTitle(title: string, maxWords = 4) {
  return title.split(" ").slice(0, maxWords).join(" ") + (title.split(" ").length > maxWords ? "…" : "");
}

export function ProductComparison({ products, onAddToCart, onViewDetails }: ProductComparisonProps) {
  if (products.length < 2) return null;

  const cols = products.length;

  return (
    <div className="w-full animate-fade-in space-y-4">
      {/* Comparison basis */}
      <div className="rounded-xl border border-peach-200/50 bg-gradient-to-r from-peach-50/60 to-rose-50/40 px-4 py-2.5">
        <p className="text-[11px] font-bold text-peach-800 uppercase tracking-wider mb-1.5">
          Comparing on
        </p>
        <p className="text-[13px] font-medium text-gray-700">
          Price, Rating, Reviews, Category & Description
        </p>
      </div>

      {/* Tabular comparison - 2 or 3 columns */}
      <div className="rounded-2xl border border-peach-100/50 bg-white overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse" style={{ minWidth: cols * 180 }}>
            <thead>
              <tr className="border-b border-peach-100/50 bg-slate-50/80">
                <th className="py-3 px-4 text-[11px] font-bold text-gray-500 uppercase tracking-wider w-36">
                  Criteria
                </th>
                {products.map((p, idx) => (
                  <th key={p.id} className="py-3 px-4 text-[12px] font-bold text-gray-900 max-w-[200px]">
                    <span className="line-clamp-2">{shortTitle(p.title)}</span>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {CRITERIA.map(({ key, label, icon }) => {
                const bestIdx = getBestIndex(products, key);
                return (
                  <tr key={key} className="border-b border-peach-100/30 last:border-0">
                    <td className="py-2.5 px-4 text-[12px] font-semibold text-gray-700">
                      <span className="inline-flex items-center gap-2">
                        {icon}
                        {label}
                      </span>
                    </td>
                    {products.map((product, idx) => {
                      const val = getCellValue(product, key);
                      const isBest = bestIdx === idx;
                      return (
                        <td
                          key={product.id}
                          className={cn(
                            "py-2.5 px-4 text-[13px] text-gray-800",
                            isBest && "bg-emerald-50/80 font-semibold text-emerald-800"
                          )}
                        >
                          {typeof val === "string" && val.length > 60 ? (
                            <span title={val}>{val}</span>
                          ) : (
                            val
                          )}
                          {isBest && (
                            <span className="ml-1.5 text-[10px] font-bold text-emerald-600">Better</span>
                          )}
                        </td>
                      );
                    })}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Product cards for actions */}
      <p className="text-[12px] font-semibold text-gray-600">Choose one to add to cart or view details</p>
      <div className={cn("grid gap-3", cols === 2 ? "grid-cols-2" : "grid-cols-3")}>
        {products.map((product) => (
          <div
            key={product.id}
            className="rounded-2xl bg-white border border-peach-100/40 p-3 shadow-sm hover:shadow-md transition-shadow"
          >
            <div
              className="h-20 flex items-center justify-center bg-white rounded-xl p-2 mb-2 cursor-pointer"
              onClick={() => onViewDetails?.(product)}
            >
              <img
                src={product.image}
                alt={product.title}
                className="max-h-full object-contain"
              />
            </div>
            <h4 className="text-[11px] font-semibold text-gray-900 line-clamp-2 leading-tight mb-1">
              {product.title}
            </h4>
            <p className="text-[14px] font-bold text-gray-900 mb-2">${product.price.toFixed(2)}</p>
            {onAddToCart && (
              <button
                onClick={() => onAddToCart(product.id)}
                className="w-full flex items-center justify-center gap-1.5 rounded-xl bg-gradient-to-r from-peach-50 to-rose-50 border border-peach-200/50 py-2 text-[11px] font-semibold text-peach-600 hover:from-peach-100 hover:to-peach-100 transition-all"
              >
                <ShoppingCart className="h-3 w-3" />
                Add to Cart
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
