import os

import boto3
import requests
import base64
import json
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), "..", ".aws")
load_dotenv(env_path)

cognito_client = boto3.client(
    "cognito-idp", region_name=os.getenv("AWS_REGION", "us-east-1")
)


def auth_with_code(code: str, redirect_uri: str):
    """
    Authenticate using the authorization code -> returns tokens from Amazon Cognito User Pool.

    :param code: Authorization code obtained after user login.
    :param redirect_uri: Redirect URI configured in the Cognito User Pool.
    :param client_id: Cognito User Pool App Client ID (optional).
    :return: Access token if authentication is successful, otherwise None.
    """
    client_id = os.getenv("COGNITO_USER_CLIENT_ID")
    client_credentials = f"{client_id}:{os.getenv('COGNITO_USER_CLIENT_SECRET')}"
    auth_header = base64.b64encode(client_credentials.encode()).decode()
    token_endpoint = os.getenv(
        "COGNITO_TOKEN_ENDPOINT"
    )  # Example: https://your_cognito_domain/oauth2/token

    # Prepare token request payload
    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": client_id,
        "redirect_uri": redirect_uri,
    }

    # Send request to the token endpoint to exchange the code for tokens
    response = requests.post(
        token_endpoint,
        data=payload,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {auth_header}",
        },
    )

    # Check if request was successful
    if response.status_code == 200:
        token_data = response.json()
        return token_data.get(
            "access_token"
        )  # Returns the access token from the response
    else:
        print(f"Error: {response.status_code}, {response.text}")
        return None


def user_info_with_token(access_token: str):

    response = cognito_client.get_user(AccessToken=access_token)

    if response.get("ResponseMetadata").get("HTTPStatusCode") == 200:
        return response
    else:
        print(f"Error: Error getting user info: {response}")
        return None
