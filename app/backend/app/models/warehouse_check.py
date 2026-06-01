import datetime
from sqlalchemy import String, ForeignKey, DateTime, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class WarehouseCheck(Base):
    __tablename__ = "warehouse_checks"

    id: Mapped[int] = mapped_column(primary_key=True)
    return_item_id: Mapped[int] = mapped_column(
        ForeignKey("return_items.id", ondelete="CASCADE")
    )
    quantity_fact: Mapped[int] = mapped_column(Integer)
    packaging_condition: Mapped[str] = mapped_column(String(255))
    defect_description: Mapped[str | None] = mapped_column(Text)
    photos: Mapped[str | None] = mapped_column(Text)  # JSON array of file paths
    inspector_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    checked_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    return_item: Mapped["ReturnItem"] = relationship(back_populates="warehouse_checks")
    inspector: Mapped["User"] = relationship()


from app.models.return_request import ReturnItem  # noqa: E402
from app.models.user import User  # noqa: E402
