from datetime import (
    datetime,
    timezone,
)
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
from sqlalchemy import select
from sqlalchemy.orm import (
    Session,
    selectinload,
)

from work_order_api.database import get_db
from work_order_api.dependencies import get_current_user
from work_order_api.models import (
    Asset,
    AssetStatus,
    User,
    UserRole,
    WorkOrder,
    WorkOrderNote,
    WorkOrderStatus,
)
from work_order_api.schemas import (
    WorkOrderAssign,
    WorkOrderCreate,
    WorkOrderNoteCreate,
    WorkOrderNoteRead,
    WorkOrderRead,
    WorkOrderUpdate,
)


router = APIRouter(
    prefix="/work-orders",
    tags=["Work Orders"],
)


def get_available_asset(
    database: Session,
    asset_id: int,
) -> Asset:
    asset = database.get(
        Asset,
        asset_id,
    )

    if asset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found.",
        )

    if asset.status == AssetStatus.RETIRED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot create work orders for a retired asset.",
        )

    return asset


def get_assignable_user(
    database: Session,
    user_id: int,
) -> User:
    user = database.get(
        User,
        user_id,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assigned user not found.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot assign work to an inactive user.",
        )

    if user.role != UserRole.TECHNICIAN:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Work orders can only be assigned to technicians.",
        )

    return user

VALID_STATUS_TRANSITIONS = {
    WorkOrderStatus.OPEN: {
        WorkOrderStatus.IN_PROGRESS,
        WorkOrderStatus.ON_HOLD,
        WorkOrderStatus.CANCELLED,
    },
    WorkOrderStatus.IN_PROGRESS: {
        WorkOrderStatus.ON_HOLD,
        WorkOrderStatus.CANCELLED,
    },
    WorkOrderStatus.ON_HOLD: {
        WorkOrderStatus.IN_PROGRESS,
        WorkOrderStatus.CANCELLED,
    },
    WorkOrderStatus.COMPLETED: set(),
    WorkOrderStatus.CANCELLED: set(),
}

def validate_status_transition(
    current_status: WorkOrderStatus,
    new_status: WorkOrderStatus,
) -> None:
    if current_status == new_status:
        return

    if new_status == WorkOrderStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Use the completion endpoint "
                "to complete a work order."
            ),
        )

    allowed = VALID_STATUS_TRANSITIONS[
        current_status
    ]

    if new_status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Cannot change status from "
                f"{current_status.value} to "
                f"{new_status.value}."
            ),
        )


@router.post(
    "",
    response_model=WorkOrderRead,
    status_code=status.HTTP_201_CREATED,
)
def create_work_order(
    work_order_data: WorkOrderCreate,
    database: Annotated[
        Session,
        Depends(get_db),
    ],
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
) -> WorkOrder:
    """Create a maintenance work order."""

    get_available_asset(
        database,
        work_order_data.asset_id,
    )

    assigned_to_id = None

    if work_order_data.assigned_to_id is not None:
        technician = get_assignable_user(
            database,
            work_order_data.assigned_to_id,
        )

        assigned_to_id = technician.id

    work_order = WorkOrder(
        asset_id=work_order_data.asset_id,
        created_by_id=current_user.id,
        assigned_to_id=assigned_to_id,
        title=work_order_data.title.strip(),
        description=work_order_data.description.strip(),
        priority=work_order_data.priority,
    )

    database.add(work_order)
    database.commit()
    database.refresh(work_order)

    return work_order


@router.get(
    "",
    response_model=list[WorkOrderRead],
)
def list_work_orders(
    database: Annotated[
        Session,
        Depends(get_db),
    ],
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    limit: Annotated[
        int,
        Query(
            ge=1,
            le=100,
        ),
    ] = 25,
    offset: Annotated[
        int,
        Query(
            ge=0,
        ),
    ] = 0,
) -> list[WorkOrder]:
    """Return a paginated list of work orders."""

    statement = (
        select(WorkOrder)
        .order_by(
            WorkOrder.created_at.desc()
        )
        .offset(offset)
        .limit(limit)
    )

    return list(
        database.scalars(statement).all()
    )

@router.get(
    "/{work_order_id}",
    response_model=WorkOrderRead,
)
def get_work_order(
    work_order_id: int,
    database: Annotated[
        Session,
        Depends(get_db),
    ],
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
) -> WorkOrder:
    work_order = database.get(
        WorkOrder,
        work_order_id,
    )

    if work_order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Work order not found.",
        )

    return work_order


@router.patch(
    "/{work_order_id}",
    response_model=WorkOrderRead,
)
def update_work_order(
    work_order_id: int,
    work_order_data: WorkOrderUpdate,
    database: Annotated[
        Session,
        Depends(get_db),
    ],
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
) -> WorkOrder:
    work_order = database.get(
        WorkOrder,
        work_order_id,
    )

    if work_order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Work order not found.",
        )

    if work_order.status in {
        WorkOrderStatus.COMPLETED,
        WorkOrderStatus.CANCELLED,
    }:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Completed or cancelled work orders "
                "cannot be modified."
            ),
        )

    updates = work_order_data.model_dump(
        exclude_unset=True,
    )

    if "status" in updates:
        validate_status_transition(
            work_order.status,
            updates["status"],
        )

    for field in (
        "title",
        "description",
    ):
        if field in updates:
            updates[field] = updates[field].strip()

    for field, value in updates.items():
        setattr(
            work_order,
            field,
            value,
        )

    database.commit()
    database.refresh(work_order)

    return work_order


@router.post(
    "/{work_order_id}/assign",
    response_model=WorkOrderRead,
)
def assign_work_order(
    work_order_id: int,
    assignment: WorkOrderAssign,
    database: Annotated[
        Session,
        Depends(get_db),
    ],
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
) -> WorkOrder:
    work_order = database.get(
        WorkOrder,
        work_order_id,
    )

    if work_order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Work order not found.",
        )

    if work_order.status in {
        WorkOrderStatus.COMPLETED,
        WorkOrderStatus.CANCELLED,
    }:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Completed or cancelled work orders "
                "cannot be reassigned."
            ),
        )

    technician = get_assignable_user(
        database,
        assignment.user_id,
    )

    work_order.assigned_to_id = technician.id

    database.commit()
    database.refresh(work_order)

    return work_order

@router.post(
    "/{work_order_id}/complete",
    response_model=WorkOrderRead,
)
def complete_work_order(
    work_order_id: int,
    database: Annotated[
        Session,
        Depends(get_db),
    ],
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
) -> WorkOrder:
    work_order = database.get(
        WorkOrder,
        work_order_id,
    )

    if work_order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Work order not found.",
        )

    if work_order.status == WorkOrderStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Work order is already completed.",
        )

    if work_order.status == WorkOrderStatus.CANCELLED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cancelled work orders cannot be completed.",
        )

    work_order.status = (
        WorkOrderStatus.COMPLETED
    )

    work_order.completed_at = (
        datetime.now(timezone.utc)
    )

    database.commit()
    database.refresh(work_order)

    return work_order

@router.post(
    "/{work_order_id}/notes",
    response_model=WorkOrderNoteRead,
    status_code=status.HTTP_201_CREATED,
)
def add_work_order_note(
    work_order_id: int,
    note_data: WorkOrderNoteCreate,
    database: Annotated[
        Session,
        Depends(get_db),
    ],
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
) -> WorkOrderNote:
    """Add a note to a work order."""

    work_order = database.get(
        WorkOrder,
        work_order_id,
    )

    if work_order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Work order not found.",
        )

    note = WorkOrderNote(
        work_order_id=work_order.id,
        author_id=current_user.id,
        content=note_data.content.strip(),
    )

    database.add(note)
    database.commit()
    database.refresh(note)

    return note


@router.get(
    "/{work_order_id}/notes",
    response_model=list[WorkOrderNoteRead],
)
def list_work_order_notes(
    work_order_id: int,
    database: Annotated[
        Session,
        Depends(get_db),
    ],
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
) -> list[WorkOrderNote]:
    """Return notes for a work order."""

    work_order = database.get(
        WorkOrder,
        work_order_id,
    )

    if work_order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Work order not found.",
        )

    statement = (
        select(WorkOrderNote)
        .where(
            WorkOrderNote.work_order_id
            == work_order_id
        )
        .order_by(
            WorkOrderNote.created_at.asc()
        )
    )

    return list(
        database.scalars(statement).all()
    )
