from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Response,
    status,
)
from sqlalchemy import (
    func,
    or_,
    select,
)
from sqlalchemy.exc import IntegrityError
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
    WorkOrder,
)
from work_order_api.schemas import (
    AssetCreate,
    AssetHistoryItem,
    AssetListResponse,
    AssetRead,
    AssetUpdate,
    PaginationMeta,
)


router = APIRouter(
    prefix="/assets",
    tags=["Assets"],
    dependencies=[
        Depends(get_current_user),
    ],
)

def normalize_asset_tag(
    asset_tag: str,
) -> str:
    """Normalize asset tags for consistent uniqueness checks."""
    return asset_tag.strip().upper()


@router.post(
    "",
    response_model=AssetRead,
    status_code=status.HTTP_201_CREATED,
)
def create_asset(
    asset_data: AssetCreate,
    database: Annotated[
        Session,
        Depends(get_db),
    ],
) -> Asset:
    """Create a new equipment asset."""

    asset_tag = normalize_asset_tag(
        asset_data.asset_tag
    )

    existing_asset = database.scalar(
        select(Asset).where(
            Asset.asset_tag == asset_tag
        )
    )

    if existing_asset is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Asset tag already exists.",
        )

    if asset_data.serial_number:
        serial_number = (
            asset_data.serial_number.strip()
        )

        existing_serial = database.scalar(
            select(Asset).where(
                Asset.serial_number == serial_number
            )
        )

        if existing_serial is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Serial number already exists.",
            )
    else:
        serial_number = None

    asset = Asset(
        name=asset_data.name.strip(),
        asset_tag=asset_tag,
        manufacturer=(
            asset_data.manufacturer.strip()
            if asset_data.manufacturer
            else None
        ),
        model=(
            asset_data.model.strip()
            if asset_data.model
            else None
        ),
        serial_number=serial_number,
        location=(
            asset_data.location.strip()
            if asset_data.location
            else None
        ),
    )

    database.add(asset)

    try:
        database.commit()
    except IntegrityError:
        database.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Asset tag or serial number "
                "already exists."
            ),
        )

    database.refresh(asset)

    return asset


@router.get(
    "",
    response_model=AssetListResponse,
)
def list_assets(
    database: Annotated[
        Session,
        Depends(get_db),
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
    asset_status: Annotated[
        AssetStatus | None,
        Query(alias="status"),
    ] = None,
    location: Annotated[
        str | None,
        Query(
            min_length=1,
            max_length=255,
        ),
    ] = None,
    search: Annotated[
        str | None,
        Query(
            min_length=1,
            max_length=100,
        ),
    ] = None,
) -> AssetListResponse:
    """Return filtered and paginated assets."""

    filters = []

    if asset_status is not None:
        filters.append(
            Asset.status == asset_status
        )

    if location:
        filters.append(
            Asset.location.ilike(
                f"%{location.strip()}%"
            )
        )

    if search:
        search_term = (
            f"%{search.strip()}%"
        )
        
        filters.append(
            or_(
                Asset.name.ilike(search_term),
                Asset.asset_tag.ilike(search_term),
                Asset.manufacturer.ilike(search_term),
                Asset.model.ilike(search_term),
                Asset.serial_number.ilike(search_term),
            )
        )

    count_statement = (
        select(
            func.count(Asset.id)
        )
        .where(*filters)
    )

    total = database.scalar(
        count_statement
    ) or 0

    statement = (
        select(Asset)
        .where(*filters)
        .order_by(Asset.id)
        .offset(offset)
        .limit(limit)
    )

    assets = list(
        database.scalars(statement).all()
    )

    return AssetListResponse(
        items=assets,
        pagination=PaginationMeta(
            total=total,
            limit=limit,
            offset=offset,
        ),
    )

@router.get(
    "/{asset_id}",
    response_model=AssetRead,
)
def get_asset(
    asset_id: int,
    database: Annotated[
        Session,
        Depends(get_db),
    ],
) -> Asset:
    """Return a single asset."""

    asset = database.get(
        Asset,
        asset_id,
    )

    if asset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found.",
        )

    return asset


@router.patch(
    "/{asset_id}",
    response_model=AssetRead,
)
def update_asset(
    asset_id: int,
    asset_data: AssetUpdate,
    database: Annotated[
        Session,
        Depends(get_db),
    ],
) -> Asset:
    """Update selected fields on an asset."""

    asset = database.get(
        Asset,
        asset_id,
    )

    if asset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found.",
        )

    updates = asset_data.model_dump(
        exclude_unset=True,
    )

    if "asset_tag" in updates:
        normalized_tag = normalize_asset_tag(
            updates["asset_tag"]
        )

        duplicate = database.scalar(
            select(Asset).where(
                Asset.asset_tag == normalized_tag,
                Asset.id != asset.id,
            )
        )

        if duplicate is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Asset tag already exists.",
            )

        updates["asset_tag"] = normalized_tag

    if (
        "serial_number" in updates
        and updates["serial_number"] is not None
    ):
        serial_number = (
            updates["serial_number"].strip()
        )

        duplicate = database.scalar(
            select(Asset).where(
                Asset.serial_number == serial_number,
                Asset.id != asset.id,
            )
        )

        if duplicate is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Serial number already exists.",
            )

        updates["serial_number"] = serial_number

    for field in (
        "name",
        "manufacturer",
        "model",
        "location",
    ):
        if (
            field in updates
            and updates[field] is not None
        ):
            updates[field] = updates[field].strip()

    for field, value in updates.items():
        setattr(
            asset,
            field,
            value,
        )

    try:
        database.commit()

    except IntegrityError:
        database.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Asset tag or serial number "
                "already exists."
            ),
        )

    database.refresh(asset)

    return asset

@router.delete(
    "/{asset_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def retire_asset(
    asset_id: int,
    database: Annotated[
        Session,
        Depends(get_db),
    ],
) -> Response:
    """Retire an asset without deleting its history."""

    asset = database.get(
        Asset,
        asset_id,
    )

    if asset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found.",
        )

    asset.status = AssetStatus.RETIRED

    database.commit()

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )

@router.get(
    "/{asset_id}/history",
    response_model=list[AssetHistoryItem],
)
def get_asset_history(
    asset_id: int,
    database: Annotated[
        Session,
        Depends(get_db),
    ],
) -> list[WorkOrder]:
    """Return maintenance history for an asset."""

    asset = database.get(
        Asset,
        asset_id,
    )

    if asset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found.",
        )

    statement = (
        select(WorkOrder)
        .options(
            selectinload(
                WorkOrder.notes
            )
        )
        .where(
            WorkOrder.asset_id == asset_id
        )
        .order_by(
            WorkOrder.created_at.desc()
        )
    )

    return list(
        database.scalars(statement).all()
    )

