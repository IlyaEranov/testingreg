from pydantic import BaseModel


# ----- Reasons -----
class ReasonResponse(BaseModel):
    id: int
    name: str
    description: str | None
    is_active: bool

    class Config:
        from_attributes = True


class ReasonCreate(BaseModel):
    name: str
    description: str | None = None
    is_active: bool = True


# ----- Suppliers -----
class SupplierResponse(BaseModel):
    id: int
    name: str
    contact_person: str | None
    phone: str | None
    email: str | None
    address: str | None
    comment: str | None
    is_active: bool

    class Config:
        from_attributes = True


class SupplierCreate(BaseModel):
    name: str
    contact_person: str | None = None
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    comment: str | None = None


# ----- Warehouses -----
class WarehouseResponse(BaseModel):
    id: int
    name: str
    address: str | None
    is_active: bool

    class Config:
        from_attributes = True


class WarehouseCreate(BaseModel):
    name: str
    address: str | None = None
    is_active: bool = True


# ----- Users -----
class UserCreate(BaseModel):
    email: str
    password: str
    last_name: str
    first_name: str
    patronymic: str | None = None
    phone: str | None = None
    role_id: int


class UserUpdate(BaseModel):
    email: str | None = None
    last_name: str | None = None
    first_name: str | None = None
    patronymic: str | None = None
    phone: str | None = None
    role_id: int | None = None
    is_active: bool | None = None


class UserListResponse(BaseModel):
    id: int
    email: str
    last_name: str
    first_name: str
    patronymic: str | None
    phone: str | None
    role_name: str | None = None
    is_active: bool

    class Config:
        from_attributes = True
