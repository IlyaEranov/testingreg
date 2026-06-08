"""Реальная отправка уведомлений: email (SMTP) и SMS (HTTP-шлюз).

Параметры берутся из системных настроек (таблица app_settings),
задаваемых администратором. Если канал не настроен — возвращается
статус "simulated" (прототип продолжает работать без внешних сервисов).
"""
import logging
import smtplib
from email.mime.text import MIMEText

import httpx

logger = logging.getLogger(__name__)


def send_email(cfg: dict, to: str, subject: str, body: str) -> str:
    """Отправить email через SMTP. Возвращает 'sent' | 'simulated' | 'failed'."""
    host = (cfg.get("smtp_host") or "").strip()
    port = cfg.get("smtp_port") or ""
    if not host or not port or not to:
        return "simulated"
    try:
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = cfg.get("smtp_from") or "no-reply@region-service.ru"
        msg["To"] = to
        with smtplib.SMTP(host, int(port), timeout=10) as s:
            user = (cfg.get("smtp_user") or "").strip()
            if user:  # боевой SMTP с авторизацией
                s.starttls()
                s.login(user, cfg.get("smtp_password") or "")
            s.send_message(msg)
        logger.info(f"Email отправлен на {to}")
        return "sent"
    except Exception as exc:
        logger.error(f"Ошибка отправки email на {to}: {exc}")
        return "failed"


def send_sms(cfg: dict, phone: str, text: str) -> str:
    """Отправить SMS через HTTP-шлюз. Возвращает 'sent' | 'simulated' | 'failed'."""
    url = (cfg.get("sms_api_url") or "").strip()
    if not url or not phone:
        return "simulated"
    try:
        payload = {
            "sender": cfg.get("sms_sender") or "RegionService",
            "phone": phone,
            "text": text,
            "api_key": cfg.get("sms_api_key") or "",
        }
        r = httpx.post(url, json=payload, timeout=10)
        r.raise_for_status()
        logger.info(f"SMS отправлено на {phone}")
        return "sent"
    except Exception as exc:
        logger.error(f"Ошибка отправки SMS на {phone}: {exc}")
        return "failed"
