"""Database-backed cart storage."""

from __future__ import annotations
from typing import Optional
from sqlalchemy.orm import Session
from app.database import CartItem, User, SessionLocal


def _get_or_create_user(session_id: str, db: Session) -> Optional[User]:
    """Get or create user by session_id (for anonymous users)."""
    # For now, we'll use session_id as a temporary identifier
    # In production, this should be linked to authenticated users
    # For anonymous users, we can create a temporary user or use session_id directly
    return None  # Anonymous cart support


def add_item(session_id: str, product_id: int, quantity: int = 1, user_id: Optional[int] = None) -> dict[int, int]:
    """Add item to cart."""
    db = SessionLocal()
    try:
        if user_id:
            # Check if item already exists
            cart_item = db.query(CartItem).filter(
                CartItem.user_id == user_id,
                CartItem.product_id == product_id
            ).first()
            
            if cart_item:
                cart_item.quantity += quantity
            else:
                cart_item = CartItem(
                    user_id=user_id,
                    product_id=product_id,
                    quantity=quantity
                )
                db.add(cart_item)
            
            db.commit()
            
            # Return cart as dict
            cart_items = db.query(CartItem).filter(CartItem.user_id == user_id).all()
            return {item.product_id: item.quantity for item in cart_items}
        else:
            # Fallback to in-memory for anonymous users (backward compatibility)
            from app.cart_memory import add_item as memory_add_item
            return memory_add_item(session_id, product_id, quantity)
    finally:
        db.close()


def remove_item(session_id: str, product_id: int, user_id: Optional[int] = None) -> dict[int, int]:
    """Remove item from cart."""
    db = SessionLocal()
    try:
        if user_id:
            db.query(CartItem).filter(
                CartItem.user_id == user_id,
                CartItem.product_id == product_id
            ).delete()
            db.commit()
            
            # Return cart as dict
            cart_items = db.query(CartItem).filter(CartItem.user_id == user_id).all()
            return {item.product_id: item.quantity for item in cart_items}
        else:
            # Fallback to in-memory
            from app.cart_memory import remove_item as memory_remove_item
            return memory_remove_item(session_id, product_id)
    finally:
        db.close()


def get_cart(session_id: str, user_id: Optional[int] = None) -> dict[int, int]:
    """Get cart contents."""
    db = SessionLocal()
    try:
        if user_id:
            cart_items = db.query(CartItem).filter(CartItem.user_id == user_id).all()
            return {item.product_id: item.quantity for item in cart_items}
        else:
            # Fallback to in-memory
            from app.cart_memory import get_cart as memory_get_cart
            return memory_get_cart(session_id)
    finally:
        db.close()


def clear_cart(session_id: str, user_id: Optional[int] = None) -> dict[int, int]:
    """Clear cart."""
    db = SessionLocal()
    try:
        if user_id:
            db.query(CartItem).filter(CartItem.user_id == user_id).delete()
            db.commit()
            return {}
        else:
            # Fallback to in-memory
            from app.cart_memory import clear_cart as memory_clear_cart
            return memory_clear_cart(session_id)
    finally:
        db.close()


def update_quantity(session_id: str, product_id: int, quantity: int, user_id: Optional[int] = None) -> dict[int, int]:
    """Update item quantity."""
    db = SessionLocal()
    try:
        if user_id:
            if quantity <= 0:
                db.query(CartItem).filter(
                    CartItem.user_id == user_id,
                    CartItem.product_id == product_id
                ).delete()
            else:
                cart_item = db.query(CartItem).filter(
                    CartItem.user_id == user_id,
                    CartItem.product_id == product_id
                ).first()
                
                if cart_item:
                    cart_item.quantity = quantity
                else:
                    cart_item = CartItem(
                        user_id=user_id,
                        product_id=product_id,
                        quantity=quantity
                    )
                    db.add(cart_item)
            
            db.commit()
            
            # Return cart as dict
            cart_items = db.query(CartItem).filter(CartItem.user_id == user_id).all()
            return {item.product_id: item.quantity for item in cart_items}
        else:
            # Fallback to in-memory
            from app.cart_memory import update_quantity as memory_update_quantity
            return memory_update_quantity(session_id, product_id, quantity)
    finally:
        db.close()
