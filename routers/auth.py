from fastapi import APIRouter, HTTPException
from fastapi.encoders import jsonable_encoder
from starlette.responses import JSONResponse
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException
from db.database import get_db

from auth.JWTBearer import JWTBearer
from auth.auth import jwks, get_current_user
from auth.user_auth import auth_with_code, user_info_with_token
from models.user import User, save_user
from repositories.userRepo import get_user
from schemas.user import CreateUser

router = APIRouter(tags=["Authentication and Authorization"])

auth = JWTBearer(jwks)


@router.post("/auth/sign-in")
async def login(code: str, redirect_uri: str, db: Session = Depends(get_db)):
    """
    Function that signs in a user and returns a token
    """
    token = auth_with_code(code, redirect_uri)
    if token is None:
        raise HTTPException(status_code=404, detail="Error loging in...")
    else:
        user_info = user_info_with_token(token)

        new_user = CreateUser(
            id=user_info["UserAttributes"][4]["Value"],
            given_name=user_info["UserAttributes"][3]["Value"],
            family_name=user_info["UserAttributes"][2]["Value"],
            username=user_info["Username"],
            email=user_info["UserAttributes"][0]["Value"],
        )

        if not (
            db.query(User).filter(User.username == new_user.username).first()
            or db.query(User).filter(User.email == new_user.email).first()
        ):
            save_user(new_user, db)

        return JSONResponse(status_code=200, content=jsonable_encoder({"token": token}))


@router.get("/auth/me", dependencies=[Depends(auth)])
async def current_user(
    username: str = Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    Function that returns the current user
    """
    return JSONResponse(
        status_code=200,
        content=jsonable_encoder(get_user(username=username, db=db)),
    )
