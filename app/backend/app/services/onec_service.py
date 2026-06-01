"""Integration service for 1C:Enterprise API."""
import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class OneCService:
    """Client for 1C:Enterprise REST API."""

    def __init__(self):
        self.base_url = settings.ONEC_API_URL
        self.headers = {}
        if settings.ONEC_API_TOKEN:
            self.headers["Authorization"] = f"Bearer {settings.ONEC_API_TOKEN}"

    async def create_return_document(
        self, return_number: str, client_name: str,
        items: list[dict], total_amount: float
    ) -> dict:
        """POST /api/returns — create 'Возврат товаров от покупателя' in 1C."""
        payload = {
            "documentType": "ReturnFromBuyer",
            "number": return_number,
            "client": client_name,
            "items": [
                {
                    "productName": item["product_name"],
                    "article": item.get("article", ""),
                    "quantity": item["quantity"],
                    "price": float(item["price"]),
                }
                for item in items
            ],
            "totalAmount": total_amount,
        }
        return await self._post("/returns", payload)

    async def update_stock(
        self, items: list[dict], warehouse: str
    ) -> dict:
        """PUT /api/stock — update warehouse stock levels in 1C."""
        payload = {
            "warehouse": warehouse,
            "items": [
                {
                    "article": item.get("article", ""),
                    "quantity": item["quantity"],
                    "operation": "return",
                }
                for item in items
            ],
        }
        return await self._put("/stock", payload)

    async def create_write_off(
        self, return_number: str, items: list[dict], reason: str
    ) -> dict:
        """POST /api/write-off — create write-off document in 1C."""
        payload = {
            "documentType": "WriteOff",
            "returnNumber": return_number,
            "reason": reason,
            "items": [
                {
                    "article": item.get("article", ""),
                    "quantity": item["quantity"],
                    "price": float(item["price"]),
                }
                for item in items
            ],
        }
        return await self._post("/write-off", payload)

    async def create_cash_refund(
        self, return_number: str, amount: float, client_name: str
    ) -> dict:
        """POST /api/refund — create cash refund order in 1C."""
        payload = {
            "documentType": "CashRefund",
            "returnNumber": return_number,
            "amount": amount,
            "client": client_name,
        }
        return await self._post("/refund", payload)

    async def _post(self, endpoint: str, payload: dict) -> dict:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}{endpoint}",
                    json=payload,
                    headers=self.headers,
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"1C API error (POST {endpoint}): {e}")
            return {"success": False, "error": str(e)}

    async def _put(self, endpoint: str, payload: dict) -> dict:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.put(
                    f"{self.base_url}{endpoint}",
                    json=payload,
                    headers=self.headers,
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"1C API error (PUT {endpoint}): {e}")
            return {"success": False, "error": str(e)}


onec_service = OneCService()
