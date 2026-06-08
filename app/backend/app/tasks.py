"""Асинхронные задачи Celery (обработчик очереди).

Длительные операции — отправка уведомлений покупателю и обмен данными
с 1С:Предприятие — вынесены в фоновые задачи. Бэкенд бизнес-логики
помещает задание в очередь (Redis) вызовом .delay(), а обработчик
очереди (Celery worker) извлекает и выполняет его независимо от
основного запроса. При сбое внешней системы задача повторяется.
"""
import logging
from datetime import datetime, timezone

from app.celery_app import celery_app
from app.database_sync import SyncSessionLocal
from app.models.notification import Notification
from app.models.return_request import ReturnRequest
from app.models.action_history import ActionHistory
from app.services.notification_service import STATUS_MESSAGES

logger = logging.getLogger(__name__)


@celery_app.task(name="tasks.send_notification", bind=True, max_retries=3)
def send_notification_task(self, return_request_id: int, new_status: str):
    """Сформировать и отправить уведомление покупателю о смене статуса.

    Соответствует компоненту «Сервис уведомлений» на схеме архитектуры:
    обработчик очереди формирует сообщение и фиксирует факт отправки.
    """
    template = STATUS_MESSAGES.get(new_status)
    if not template:
        return {"skipped": True, "reason": "нет шаблона для статуса"}

    session = SyncSessionLocal()
    try:
        rr = session.get(ReturnRequest, return_request_id)
        if not rr:
            return {"error": "Заявка не найдена"}

        client = rr.client
        contact = ""
        channel = "email"
        if client:
            if client.phone:
                contact = client.phone
                channel = "sms"
            elif client.email:
                contact = client.email
                channel = "email"

        message = template.format(number=rr.number)
        notification = Notification(
            return_request_id=rr.id,
            recipient_type="client",
            recipient_contact=contact,
            channel=channel,
            message=message,
            is_sent=True,
            sent_at=datetime.now(timezone.utc),
        )
        session.add(notification)
        session.commit()
        logger.info(f"Уведомление по заявке {rr.number} отправлено ({channel})")
        return {"sent": True, "channel": channel, "contact": contact}
    except Exception as exc:
        session.rollback()
        logger.error(f"Ошибка отправки уведомления: {exc}")
        raise self.retry(exc=exc)
    finally:
        session.close()


@celery_app.task(name="tasks.sync_with_onec", bind=True, max_retries=3)
def sync_with_onec_task(self, return_request_id: int):
    """Передать данные о возврате в 1С:Предприятие.

    Соответствует компоненту «1С:Предприятие сервер API» на схеме:
    обработчик очереди создаёт документ «Возврат товаров от покупателя»
    и обновляет складские остатки. При недоступности 1С задача
    повторяется (задержка задаётся в конфигурации Celery).
    """
    import asyncio
    from app.services.onec_service import onec_service

    session = SyncSessionLocal()
    try:
        rr = session.get(ReturnRequest, return_request_id)
        if not rr:
            return {"error": "Заявка не найдена"}

        items = [
            {"product_name": it.product_name, "article": it.article,
             "quantity": it.quantity, "price": it.price}
            for it in rr.items
        ]
        client_name = rr.client.name if rr.client else ""
        warehouse_name = rr.warehouse.name if rr.warehouse else ""
        total = float(rr.total_amount or 0)

        # Адрес и токен 1С берём из настроек (задаются администратором в интерфейсе),
        # с откатом на значение по умолчанию из конфигурации
        from app.models.setting import AppSetting
        url_row = session.get(AppSetting, "onec_api_url")
        token_row = session.get(AppSetting, "onec_api_token")
        if url_row and url_row.value:
            onec_service.base_url = url_row.value.rstrip("/")
        onec_service.headers = {}
        if token_row and token_row.value:
            onec_service.headers["Authorization"] = f"Bearer {token_row.value}"

        # onec_service использует httpx.AsyncClient — выполняем в петле событий
        loop = asyncio.new_event_loop()
        try:
            doc_result = loop.run_until_complete(
                onec_service.create_return_document(rr.number, client_name, items, total)
            )
            stock_result = loop.run_until_complete(
                onec_service.update_stock(items, warehouse_name)
            )
        finally:
            loop.close()

        session.add(ActionHistory(
            return_request_id=rr.id, user_id=None,
            action="Обработчик очереди: данные переданы в 1С:Предприятие",
            old_status=rr.status, new_status=rr.status,
        ))
        session.commit()
        logger.info(f"Заявка {rr.number}: обмен с 1С выполнен")
        return {"onec": True, "document": doc_result, "stock": stock_result}
    except Exception as exc:
        session.rollback()
        logger.error(f"Ошибка обмена с 1С: {exc}")
        raise self.retry(exc=exc)
    finally:
        session.close()
