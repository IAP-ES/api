import base64
import json
from typing import Dict, Optional, List

from fastapi import HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwk, JWTError
from jose.utils import base64url_decode
from pydantic import BaseModel
from starlette.requests import Request
from starlette.status import HTTP_403_FORBIDDEN

# Define the type for JWK
JWK = Dict[str, str]


# Model for the JSON Web Key Set (JWKS)
class JWKS(BaseModel):
    keys: List[JWK]


# Model for JWT authorization credentials
class JWTAuthorizationCredentials(BaseModel):
    jwt_token: str
    header: dict[str, str]
    claims: dict[str, str]
    signature: str
    message: str


# Class to handle JWT authentication
class JWTBearer(HTTPBearer):
    def __init__(self, jwks: JWKS, auto_error: bool = True):
        super().__init__(auto_error=auto_error)
        # Map KIDs to their corresponding JWKs
        self.kid_to_jwk = {jwk["kid"]: jwk for jwk in jwks.keys}

    def decode_jwt(self, token: str):
        """Decode the JWT into header and payload."""
        try:
            header, payload, signature = token.split(".")
            decoded_header = json.loads(
                base64.urlsafe_b64decode(header + "==").decode("utf-8")
            )
            decoded_payload = json.loads(
                base64.urlsafe_b64decode(payload + "==").decode("utf-8")
            )

            return decoded_header, decoded_payload
        except Exception as e:
            return None, None  # Return None on error

    def verify_jwk_token(self, jwt_credentials: JWTAuthorizationCredentials) -> bool:
        """Verify the JWT token using the JWK."""
        try:
            public_key = self.kid_to_jwk[jwt_credentials.header["kid"]]
        except KeyError:
            raise HTTPException(
                status_code=HTTP_403_FORBIDDEN, detail="JWK public key not found"
            )

        key = jwk.construct(public_key)
        decoded_signature = base64url_decode(jwt_credentials.signature.encode())

        # Verify the token's signature
        return key.verify(jwt_credentials.message.encode(), decoded_signature)

    async def __call__(self, request: Request) -> Optional[JWTAuthorizationCredentials]:
        """Call the authentication method when receiving a request."""
        credentials: HTTPAuthorizationCredentials = await super().__call__(request)

        if credentials:
            # Check if the authentication scheme is Bearer
            if credentials.scheme != "Bearer":
                raise HTTPException(
                    status_code=HTTP_403_FORBIDDEN, detail="Wrong authentication method"
                )

            jwt_token = credentials.credentials[7:]  # Remove the "Bearer " prefix

            # Ensure that the JWT has three parts
            if len(jwt_token.split(".")) != 3:
                raise HTTPException(
                    status_code=HTTP_403_FORBIDDEN, detail="Invalid JWT structure"
                )

            message, signature = jwt_token.rsplit(".", 1)
            header_, _, _ = jwt_token.split(".")

            try:
                # Decode the JWT and extract the header and claims
                decoded_header, claims = self.decode_jwt(jwt_token)

                if claims is None:
                    raise HTTPException(
                        status_code=HTTP_403_FORBIDDEN, detail="Failed to decode claims"
                    )

                # Remove unnecessary fields from claims
                claims.pop("version", None)
                claims.pop("cognito:groups", None)

                # Convert timestamps to strings
                for claim in ["auth_time", "iat", "exp"]:
                    if claim in claims:
                        claims[claim] = str(claims[claim])

                # Create a JWT credentials object
                jwt_credentials = JWTAuthorizationCredentials(
                    jwt_token=jwt_token,
                    header=decoded_header,
                    claims=claims,
                    signature=signature,
                    message=message,
                )

            except (ValueError, json.JSONDecodeError):
                raise HTTPException(
                    status_code=HTTP_403_FORBIDDEN, detail="Invalid JWT header"
                )
            except JWTError:
                raise HTTPException(
                    status_code=HTTP_403_FORBIDDEN, detail="JWK invalid"
                )

            # Verify if the token is valid
            if not self.verify_jwk_token(jwt_credentials):
                raise HTTPException(
                    status_code=HTTP_403_FORBIDDEN, detail="JWK invalid"
                )

        return jwt_credentials  # Return the JWT credentials if valid
