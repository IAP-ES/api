import os
import logging
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse
from pydantic import BaseModel, Field

from db.database import get_db
from auth.auth import jwks
from auth.JWTBearer import JWTBearer
from auth.user_auth import auth_with_code, user_info_with_token
from crud.user import create_user, get_user_by_username, get_user_by_email
from schemas.user import UserCreate

load_dotenv()

router = APIRouter(tags=["Authentication and Authorization"])

auth = JWTBearer(jwks)

COGNITO_REDIRECT_URI = os.environ.get("COGNITO_REDIRECT_URI")


class SignInRequest(BaseModel):
    code: str = Field(..., description="Authorization code obtained after user login.")


@router.post("/auth/signin", response_model=dict, status_code=status.HTTP_200_OK)
async def signin(request: SignInRequest, db: Session = Depends(get_db)):
    """
    Endpoint to log in a user and return an access token.

    :param request: Contains the authorization code.
    :param db: Database session.
    :return: Access token and expiration time if authentication is successful.
    """

    # Authenticate user with the provided code
    try:
        token = auth_with_code(request.code, COGNITO_REDIRECT_URI)
        if token is None:
            logging.error("Failed to authenticate user with the provided code.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization code. Please try again.",
            )

        # Get user info from the token
        user_info = user_info_with_token(token.get("token"))
        if not user_info:
            logging.error("Failed to retrieve user information from the token.")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to retrieve user information.",
            )

        # Create a new user object
        new_user = UserCreate(
            id=user_info["UserAttributes"][4]["Value"],
            given_name=user_info["UserAttributes"][3]["Value"],
            family_name=user_info["UserAttributes"][2]["Value"],
            username=user_info["Username"],
            email=user_info["UserAttributes"][0]["Value"],
        )

        # Check if the user already exists
        existing_user = get_user_by_username(
            new_user.username, db
        ) or get_user_by_email(new_user.email, db)
        if not existing_user:
            create_user(new_user, db)
        else:
            logging.info(f"User '{new_user.username}' already exists in the database.")

        # Return the token if authentication is successful
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"token": token, "message": "Login successful."},
        )

    except Exception as e:
        logging.exception("Unexpected error occurred during sign-in process.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during sign-in. Please try again later.",
        )
