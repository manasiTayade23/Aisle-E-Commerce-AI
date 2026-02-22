"""In-memory cart storage for backward compatibility (anonymous users)."""

from __future__ import annotations

_carts: dict[str, dict[int, int]] = {}  # session_id -> {product_id: quantity}


def _get(session_id: str) -> dict[int, int]:
    return _carts.setdefault(session_id, {})


def add_item(session_id: str, product_id: int, quantity: int = 1) -> dict[int, int]:
    cart = _get(session_id)
    cart[product_id] = cart.get(product_id, 0) + quantity
    return cart


def remove_item(session_id: str, product_id: int) -> dict[int, int]:
    cart = _get(session_id)
    cart.pop(product_id, None)
    return cart


def get_cart(session_id: str) -> dict[int, int]:
    return dict(_get(session_id))


def clear_cart(session_id: str) -> dict[int, int]:
    _carts[session_id] = {}
    return {}


def update_quantity(session_id: str, product_id: int, quantity: int) -> dict[int, int]:
    cart = _get(session_id)
    if quantity <= 0:
        cart.pop(product_id, None)
    else:
        cart[product_id] = quantity
    return cart
