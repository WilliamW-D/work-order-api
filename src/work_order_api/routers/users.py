from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
)

from work_order_api.dependencies import (
    get_current_user,
)
from work_order_api.models import User
from work_order_api.schemas import UserRead


router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.get(
    "/me",
    response_model=UserRead,
)
def read_current_user(
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
) -> User:
    """Return the currently authenticated user."""
    return current_user
