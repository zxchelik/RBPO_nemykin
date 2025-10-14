from adapters.db.repositories.user_repo import UserRepository
from adapters.db.session_context import get_async_session
from app.api.v1.deps.auth import get_current_user
from app.api.v1.schemas import Token, UserCreate, UserRead
from app.core.security import create_access_token, pwd_context, verify_password
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from services.user_service import UserService
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_async_session),
):
    users = UserRepository(session)
    user = await users.get_by_login(form_data.username)
    if not user or not verify_password(form_data.password, user.pass_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    token = create_access_token(sub=user.id)
    return Token(access_token=token)


@router.post("/register", response_model=UserRead, status_code=201)
async def register_user(payload: UserCreate, session: AsyncSession = Depends(get_async_session)):
    svc = UserService(session)
    try:
        user = await svc.register(
            login=payload.login,
            email=payload.email,
            pass_hash=pwd_context.hash(payload.password),
        )
        return user
    except Exception as e:
        # Reuse same mapper as services.fastapi_adapters
        from services.fastapi_adapters import map_service_errors

        print(e)
        map_service_errors(e)


@router.get("/me", response_model=UserRead)
async def whoami(current_user=Depends(get_current_user)):
    return current_user
