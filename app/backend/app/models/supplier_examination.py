import datetime
from sqlalchemy import String, ForeignKey, DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class SupplierExamination(Base):
    __tablename__ = "supplier_examinations"

    id: Mapped[int] = mapped_column(primary_key=True)
    return_request_id: Mapped[int] = mapped_column(
        ForeignKey("return_requests.id", ondelete="CASCADE")
    )
    supplier_id: Mapped[int] = mapped_column(ForeignKey("suppliers.id"))
    transfer_date: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True))
    result_date: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True))
    conclusion: Mapped[str | None] = mapped_column(String(100))
    details: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    supplier: Mapped["Supplier"] = relationship()


from app.models.directory import Supplier  # noqa: E402
