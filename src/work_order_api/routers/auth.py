from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from work_order_api.database import get_db
from work_order_api.models import User
from work_order_api.schemas import (
    Token,
    UserCreate,
    UserRead,
)
from work_order_api.security import (
    create_access_token,
    hash_password,
    verify_password,
)


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
)
def register_user(
    user_data: UserCreate,
    database: Annotated[
        Session,
        Depends(get_db),
    ],
) -> User:
    """Register a new application user."""

    normalized_email = (
        str(user_data.email)
        .strip()
        .lower()
    )

    existing_user = database.scalar(
        select(User).where(
            User.email == normalized_email
        )
    )

    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists.",
        )

    user = User(
        email=normalized_email,
        full_name=user_data.full_name.strip(),
        password_hash=hash_password(
            user_data.password
        ),
    )

    database.add(user)

    try:
        database.commit()
    except IntegrityError:
        database.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists.",
        )

    database.refresh(user)

    return user


@router.post(
    "/token",
    response_model=Token,
)
def login(
    form_data: Annotated[
        OAuth2PasswordRequestForm,
        Depends(),
    ],
    database: Annotated[
        Session,
        Depends(get_db),
    ],
) -> Token:
    """Authenticate a user and return a JWT access token."""

    email = (
        form_data.username
        .strip()
        .lower()
    )

    user = database.scalar(
        select(User).where(
            User.email == email
        )
    )

    if (
        user is None
        or not verify_password(
            form_data.password,
            user.password_hash,
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive.",
        )

    access_token = create_access_token(
        subject=str(user.id),
    )

    return Token(
        access_token=access_token,
    )
