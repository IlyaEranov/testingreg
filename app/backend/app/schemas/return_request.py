from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel


# ----- Items -----
class ReturnItemCreate(BaseModel):
    product_name: str
    article: str | None = None
    quantity: int
    unit: str = "шт."
    price: Decimal


class ReturnItemResponse(BaseModel):
    id: int
    product_name: str
    article: str | None
    quantity: int
    unit: str
    price: Decimal

    class Config:
        from_attributes = True


# ----- Warehouse check -----
class WarehouseCheckCreate(BaseModel):
    return_item_id: int
    quantity_fact: int
    packaging_condition: str
    defect_description: str | None = None


class WarehouseCheckResponse(BaseModel):
    id: int
    return_item_id: int
    quantity_fact: int
    packaging_condition: str
    defect_description: str | None
    inspector_name: str | None = None
    checked_at: datetime

    class Config:
        from_attributes = True


# ----- Supplier examination -----
class ExaminationCreate(BaseModel):
    supplier_id: int
    details: str | None = None


class ExaminationResultUpdate(BaseModel):
    conclusion: str  # "defect_confirmed" | "defect_not_confirmed"
    details: str | None = None


class ExaminationResponse(BaseModel):
    id: int
    supplier_id: int
    supplier_name: str | None = None
    transfer_date: datetime | None
    result_date: datetime | None
    conclusion: str | None
    details: str | None

    class Config:
        from_attributes = True


# ----- Document -----
class DocumentResponse(BaseModel):
    id: int
    document_type: str
    file_name: str
    file_path: str
    created_at: datetime

    class Config:
        from_attributes = True


# ----- Action history -----
class ActionHistoryResponse(BaseModel):
    id: int
    action: str
    old_status: str | None
    new_status: str | None
    details: str | None
    user_name: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


# ----- Return request -----
class ReturnRequestCreate(BaseModel):
    client_name: str
    client_phone: str | None = None
    client_email: str | None = None
    return_type: str
    reason_id: int
    warehouse_id: int
    comment: str | None = None
    items: list[ReturnItemCreate]


class ReturnRequestUpdate(BaseModel):
    comment: str | None = None


class StatusTransition(BaseModel):
    new_status: str
    comment: str | None = None


class ReturnRequestListResponse(BaseModel):
    id: int
    number: str
    client_name: str
    return_type: str
    reason_name: str | None = None
    status: str
    manager_name: str | None = None
    warehouse_name: str | None = None
    total_amount: Decimal
    created_at: datetime

    class Config:
        from_attributes = True


class ReturnRequestDetailResponse(BaseModel):
    id: int
    number: str
    client_name: str
    client_phone: str | None
    client_email: str | None
    return_type: str
    reason_name: str | None
    status: str
    manager_name: str | None
    warehouse_name: str | None
    comment: str | None
    total_amount: Decimal
    created_at: datetime
    updated_at: datetime
    items: list[ReturnItemResponse] = []
    checks: list[WarehouseCheckResponse] = []
    documents: list[DocumentResponse] = []
    history: list[ActionHistoryResponse] = []
    examination: ExaminationResponse | None = None

    class Config:
        from_attributes = True
