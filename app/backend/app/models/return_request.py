import datetime
from decimal import Decimal
from sqlalchemy import String, ForeignKey, DateTime, Numeric, Integer, func, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ReturnRequest(Base):
    __tablename__ = "return_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    number: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"))
    return_type: Mapped[str] = mapped_column(String(100))
    # Ветка обработки: "defect" — претензия по качеству (через завод),
    #                  "quality" — надлежащее качество / неактуальный заказ (без завода)
    kind: Mapped[str] = mapped_column(String(20), default="defect")
    # Итог обработки: "write_off" — списание (брак),
    #                 "correction" — корректировка / возврат в продажу
    outcome: Mapped[str | None] = mapped_column(String(20))
    reason_id: Mapped[int] = mapped_column(ForeignKey("return_reasons.id"))
    status: Mapped[str] = mapped_column(String(50), default="created", index=True)
    manager_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id"))
    comment: Mapped[str | None] = mapped_column(Text)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    # Признак выполненного обмена с 1С (для идемпотентности — не дублировать документ)
    onec_synced: Mapped[bool] = mapped_column(default=False)
    onec_document_number: Mapped[str | None] = mapped_column(String(50))
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    client: Mapped["Client"] = relationship()
    reason: Mapped["ReturnReason"] = relationship()
    manager: Mapped["User"] = relationship()
    warehouse: Mapped["Warehouse"] = relationship()
    items: Mapped[list["ReturnItem"]] = relationship(
        back_populates="return_request", cascade="all, delete-orphan"
    )
    documents: Mapped[list["Document"]] = relationship(back_populates="return_request")
    history: Mapped[list["ActionHistory"]] = relationship(back_populates="return_request")


class ReturnItem(Base):
    __tablename__ = "return_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    return_request_id: Mapped[int] = mapped_column(
        ForeignKey("return_requests.id", ondelete="CASCADE")
    )
    product_name: Mapped[str] = mapped_column(String(500))
    article: Mapped[str | None] = mapped_column(String(100))
    quantity: Mapped[int] = mapped_column(Integer)
    unit: Mapped[str] = mapped_column(String(20), default="шт.")
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2))

    return_request: Mapped["ReturnRequest"] = relationship(back_populates="items")
    warehouse_checks: Mapped[list["WarehouseCheck"]] = relationship(
        back_populates="return_item"
    )


# Avoid circular imports
from app.models.client import Client  # noqa: E402
from app.models.directory import ReturnReason, Warehouse  # noqa: E402
from app.models.user import User  # noqa: E402
from app.models.document import Document  # noqa: E402
from app.models.action_history import ActionHistory  # noqa: E402
from app.models.warehouse_check import WarehouseCheck  # noqa: E402
