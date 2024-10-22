import os
import logging
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse
from pydantic import BaseModel, Field

from db.database import get_db
from auth.auth import jwks, get_current_user
from auth.JWTBearer import JWTBearer, JWTAuthorizationCredentials
from auth.user_auth import auth_with_code, user_info_with_token, logout_with_token
from crud.user import (
    create_user,
    get_user_by_username,
    get_user_by_email,
)
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

    except HTTPException as http_exc:
        # Re-raise HTTP exceptions to maintain the status code
        raise http_exc
    except Exception:
        logging.exception("Unexpected error occurred during sign-in process.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during sign-in. Please try again later.",
        )


@router.get(
    "/auth/me",
    dependencies=[Depends(auth)],
    response_model=dict,
    status_code=status.HTTP_200_OK,
)
async def get_current_user_info(
    current_username: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns the authenticated user's information.

    This function uses the authentication system to retrieve the current user's
    username and fetches the corresponding user details from the database.

    :param current_username: The username of the currently authenticated user.
    :param db: Database session to query user details.
    :return: A JSON object containing the user's details if found.
    :raises HTTPException: If the user is not found in the database.
    """

    try:
        # Retrieve user details from the database using the username
        user = get_user_by_username(user_username=current_username, db=db)
        # If the user does not exist, raise an HTTPException
        if not user:
            logging.error(f"User '{current_username}' not found in the database.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found."
            )

        # Return the user details as JSON
        return JSONResponse(
            status_code=status.HTTP_200_OK, content=jsonable_encoder(user)
        )

    except HTTPException as http_exc:
        # Re-raise the HTTP exception for the FastAPI exception handler
        raise http_exc

    except Exception:
        # Log unexpected errors and raise a 500 error for the client
        logging.exception(
            f"An unexpected error occurred while retrieving user info for '{current_username}'."
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving the user information. Please try again later.",
        )


@router.get("/auth/logout", response_model=dict, status_code=status.HTTP_200_OK)
async def logout(credentials: JWTAuthorizationCredentials = Depends(auth)):
    """
    Logout the authenticated user by revoking their access token.

    This endpoint logs out the user by invalidating their access token using Amazon Cognito's
    `global_sign_out` function. The token is provided in the `Authorization` header as part of
    the request's JWT credentials.

    :param credentials: JWTAuthorizationCredentials object that contains the access token.
    :return: JSON response confirming the logout action if successful.
    :raises HTTPException: If the logout process fails.
    """
    try:
        # Attempt to log out by revoking the user's token
        result = logout_with_token(credentials.jwt_token)

        # If the logout process succeeds, return a success message
        if result:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={"message": "Logout successful."},
            )
        else:
            # If logout fails for any reason, raise an HTTP 400 error with a descriptive message
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to log out. Please try again.",
            )

    except HTTPException as http_exc:
        # Re-raise the HTTP exception for the FastAPI exception handler
        raise http_exc

    except Exception:
        # Log the exception for debugging purposes
        logging.exception("An unexpected error occurred during the logout process.")

        # Return a generic HTTP 500 error if something unexpected occurs
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal server error occurred during logout. Please try again later.",
        )
