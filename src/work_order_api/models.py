from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from work_order_api.database import Base


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    TECHNICIAN = "technician"
    MANAGER = "manager"


class AssetStatus(str, enum.Enum):
    ACTIVE = "active"
    OUT_OF_SERVICE = "out_of_service"
    RETIRED = "retired"


class WorkOrderPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class WorkOrderStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    full_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    role: Mapped[UserRole] = mapped_column(
        Enum(
            UserRole,
            name="user_role",
            native_enum=False,
            create_constraint=True,
        ),
        default=UserRole.TECHNICIAN,
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    assigned_work_orders: Mapped[list[WorkOrder]] = relationship(
        back_populates="assigned_user",
        foreign_keys="WorkOrder.assigned_to_id",
    )

    created_work_orders: Mapped[list[WorkOrder]] = relationship(
        back_populates="created_by",
        foreign_keys="WorkOrder.created_by_id",
    )

    notes: Mapped[list[WorkOrderNote]] = relationship(
        back_populates="author",
    )


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    asset_tag: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    manufacturer: Mapped[str | None] = mapped_column(
        String(150),
    )

    model: Mapped[str | None] = mapped_column(
        String(150),
    )

    serial_number: Mapped[str | None] = mapped_column(
        String(150),
        unique=True,
    )

    location: Mapped[str | None] = mapped_column(
        String(255),
    )

    status: Mapped[AssetStatus] = mapped_column(
        Enum(
            AssetStatus,
            name="asset_status",
            native_enum=False,
            create_constraint=True,
        ),
        default=AssetStatus.ACTIVE,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    work_orders: Mapped[list[WorkOrder]] = relationship(
        back_populates="asset",
        cascade="all, delete-orphan",
    )


class WorkOrder(Base):
    __tablename__ = "work_orders"

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    asset_id: Mapped[int] = mapped_column(
        ForeignKey(
            "assets.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    created_by_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    assigned_to_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    priority: Mapped[WorkOrderPriority] = mapped_column(
        Enum(
            WorkOrderPriority,
            name="work_order_priority",
            native_enum=False,
            create_constraint=True,
        ),
        default=WorkOrderPriority.MEDIUM,
        nullable=False,
        index=True,
    )

    status: Mapped[WorkOrderStatus] = mapped_column(
        Enum(
            WorkOrderStatus,
            name="work_order_status",
            native_enum=False,
            create_constraint=True,
        ),
        default=WorkOrderStatus.OPEN,
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )

    asset: Mapped[Asset] = relationship(
        back_populates="work_orders",
    )

    assigned_user: Mapped[User | None] = relationship(
        back_populates="assigned_work_orders",
        foreign_keys=[assigned_to_id],
    )

    created_by: Mapped[User] = relationship(
        back_populates="created_work_orders",
        foreign_keys=[created_by_id],
    )

    notes: Mapped[list[WorkOrderNote]] = relationship(
        back_populates="work_order",
        cascade="all, delete-orphan",
    )


class WorkOrderNote(Base):
    __tablename__ = "work_order_notes"

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    work_order_id: Mapped[int] = mapped_column(
        ForeignKey(
            "work_orders.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    author_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    work_order: Mapped[WorkOrder] = relationship(
        back_populates="notes",
    )

    author: Mapped[User] = relationship(
        back_populates="notes",
    )
