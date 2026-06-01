from fastapi import APIRouter

from app.api import (
    auth, returns, warehouse, documents, users,
    directories, reports, notifications, dashboard,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Авторизация"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Дашборд"])
api_router.include_router(returns.router, prefix="/returns", tags=["Заявки на возврат"])
api_router.include_router(warehouse.router, prefix="/warehouse", tags=["Складская проверка"])
api_router.include_router(documents.router, prefix="/documents", tags=["Документы"])
api_router.include_router(users.router, prefix="/users", tags=["Пользователи"])
api_router.include_router(directories.router, prefix="/directories", tags=["Справочники"])
api_router.include_router(reports.router, prefix="/reports", tags=["Отчёты"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["Уведомления"])
