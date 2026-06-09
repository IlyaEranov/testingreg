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

    async def create_write_off(
        self, return_number: str, items: list[dict], reason: str
    ) -> dict:
        """POST /write-off — создать документ списания товара в 1С (брак).

        1С создаёт документ и возвращает его номер и печатную форму.
        """
        payload = {
            "documentType": "WriteOff",
            "returnNumber": return_number,
            "reason": reason,
            "items": [
                {
                    "article": item.get("article", ""),
                    "productName": item.get("product_name", ""),
                    "quantity": item["quantity"],
                    "price": float(item["price"]),
                }
                for item in items
            ],
        }
        return await self._post("/write-off", payload)

    async def create_correction(
        self, return_number: str, items: list[dict], warehouse: str
    ) -> dict:
        """POST /correction — корректировка и возврат товара в продажу в 1С
        (надлежащее качество / неактуальный заказ): остатки обновляются.

        1С создаёт документ корректировки и возвращает его номер и печатную форму.
        """
        payload = {
            "documentType": "Correction",
            "returnNumber": return_number,
            "warehouse": warehouse,
            "items": [
                {
                    "article": item.get("article", ""),
                    "productName": item.get("product_name", ""),
                    "quantity": item["quantity"],
                    "operation": "return_to_stock",
                }
                for item in items
            ],
        }
        return await self._post("/correction", payload)

    async def get_reconciliation_act(
        self, return_number: str, client_name: str
    ) -> dict:
        """POST /reconciliation-act — запросить акт сверки по контрагенту из 1С.

        Акт сверки формируется в 1С; АИС подтягивает его номер и печатную форму.
        """
        payload = {
            "documentType": "ReconciliationAct",
            "returnNumber": return_number,
            "client": client_name,
        }
        return await self._post("/reconciliation-act", payload)

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
