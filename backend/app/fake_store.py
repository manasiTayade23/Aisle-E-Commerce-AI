import httpx
from app.config import FAKE_STORE_BASE_URL

_client = httpx.AsyncClient(base_url=FAKE_STORE_BASE_URL, timeout=15.0)


async def get_all_products() -> list[dict]:
    resp = await _client.get("/products")
    resp.raise_for_status()
    return resp.json()


async def get_product(product_id: int) -> dict:
    resp = await _client.get(f"/products/{product_id}")
    resp.raise_for_status()
    return resp.json()


async def get_categories() -> list[str]:
    resp = await _client.get("/products/categories")
    resp.raise_for_status()
    return resp.json()


async def get_products_by_category(category: str) -> list[dict]:
    resp = await _client.get(f"/products/category/{category}")
    resp.raise_for_status()
    return resp.json()
