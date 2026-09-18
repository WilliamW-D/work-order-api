from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
)

from work_order_api.models import (
    AssetStatus,
    UserRole,
    WorkOrderPriority,
    WorkOrderStatus,
)


class UserCreate(BaseModel):
    email: EmailStr

    full_name: str = Field(
        min_length=2,
        max_length=150,
    )

    password: str = Field(
        min_length=8,
        max_length=128,
    )


class UserRead(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class AssetCreate(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=150,
    )

    asset_tag: str = Field(
        min_length=1,
        max_length=100,
    )

    manufacturer: str | None = Field(
        default=None,
        max_length=150,
    )

    model: str | None = Field(
        default=None,
        max_length=150,
    )

    serial_number: str | None = Field(
        default=None,
        max_length=150,
    )

    location: str | None = Field(
        default=None,
        max_length=255,
    )
    @field_validator(
        "name",
        "asset_tag",
        "manufacturer",
        "model",
        "serial_number",
        "location",
    )
    @classmethod
    def strip_strings(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        value = value.strip()

        if not value:
            raise ValueError(
                "Value cannot be blank."
            )

        return value


class AssetUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=150,
    )

    asset_tag: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    manufacturer: str | None = Field(
        default=None,
        max_length=150,
    )

    model: str | None = Field(
        default=None,
        max_length=150,
    )

    serial_number: str | None = Field(
        default=None,
        max_length=150,
    )

    location: str | None = Field(
        default=None,
        max_length=255,
    )
    @field_validator(
        "name",
        "asset_tag",
        "manufacturer",
        "model",
        "serial_number",
        "location",
    )
    @classmethod
    def strip_strings(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        value = value.strip()

        if not value:
            raise ValueError(
                "Value cannot be blank."
            )

        return value

    status: AssetStatus | None = None


class AssetRead(BaseModel):
    id: int
    name: str
    asset_tag: str
    manufacturer: str | None
    model: str | None
    serial_number: str | None
    location: str | None
    status: AssetStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )

class WorkOrderCreate(BaseModel):
    asset_id: int

    title: str = Field(
        min_length=3,
        max_length=200,
    )

    description: str = Field(
        min_length=3,
    )

    priority: WorkOrderPriority = WorkOrderPriority.MEDIUM

    assigned_to_id: int | None = None
    @field_validator(
        "title",
        "description",
    )
    @classmethod
    def strip_strings(
        cls,
        value: str,
    ) -> str:
        value = value.strip()

        if not value:
            raise ValueError(
                "Value cannot be blank."
            )

        return value


class WorkOrderUpdate(BaseModel):
    title: str | None = Field(
        default=None,
        min_length=3,
        max_length=200,
    )

    description: str | None = Field(
        default=None,
        min_length=3,
    )

    priority: WorkOrderPriority | None = None

    status: WorkOrderStatus | None = None
    @field_validator(
        "title",
        "description",
    )
    @classmethod
    def strip_strings(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        value = value.strip()

        if not value:
            raise ValueError(
                "Value cannot be blank."
            )

        return value


class WorkOrderAssign(BaseModel):
    user_id: int


class WorkOrderRead(BaseModel):
    id: int
    asset_id: int
    created_by_id: int
    assigned_to_id: int | None

    title: str
    description: str

    priority: WorkOrderPriority
    status: WorkOrderStatus

    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None

    model_config = ConfigDict(
        from_attributes=True,
    )

class WorkOrderNoteCreate(BaseModel):
    content: str = Field(
        min_length=2,
        max_length=5000,
    )


class WorkOrderNoteRead(BaseModel):
    id: int
    work_order_id: int
    author_id: int
    content: str
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


class AssetHistoryItem(BaseModel):
    id: int
    title: str
    priority: WorkOrderPriority
    status: WorkOrderStatus
    assigned_to_id: int | None
    created_at: datetime
    completed_at: datetime | None
    notes: list[WorkOrderNoteRead]

    model_config = ConfigDict(
        from_attributes=True,
    )

class PaginationMeta(BaseModel):
    total: int
    limit: int
    offset: int


class AssetListResponse(BaseModel):
    items: list[AssetRead]
    pagination: PaginationMeta


class WorkOrderListResponse(BaseModel):
    items: list[WorkOrderRead]
    pagination: PaginationMeta


