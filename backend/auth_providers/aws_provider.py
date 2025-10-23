"""
AWS Cognito authentication provider implementation.

Handles authentication using AWS Cognito User Pools with OIDC.
"""

from typing import Dict, Any, Optional
from fastapi import HTTPException, status
import structlog
import httpx
import jwt
import json

from .base import AuthProvider

logger = structlog.get_logger()


class AWSCognitoAuthProvider(AuthProvider):
    """
    AWS Cognito authentication provider.

    Uses AWS Cognito User Pools with OpenID Connect (OIDC) to validate
    tokens and retrieve user information.
    """

    def __init__(
        self,
        user_pool_id: str,
        client_id: str,
        client_secret: str,
        region: str,
        issuer: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize AWS Cognito provider.

        Args:
            user_pool_id: Cognito User Pool ID (e.g., us-east-1_aBcDeFgHi)
            client_id: Cognito App Client ID
            client_secret: Cognito App Client Secret
            region: AWS region (e.g., us-east-1)
            issuer: Cognito issuer URL (auto-generated if not provided)
            **kwargs: Additional configuration options
        """
        super().__init__(**kwargs)
        self.user_pool_id = user_pool_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.region = region

        # Generate issuer URL if not provided
        if issuer:
            self.issuer = issuer
        else:
            self.issuer = f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}"

        # Cognito endpoints
        self.jwks_uri = f"{self.issuer}/.well-known/jwks.json"
        self.userinfo_endpoint = f"https://{self._get_cognito_domain()}/oauth2/userInfo"
        self.token_endpoint = f"https://{self._get_cognito_domain()}/oauth2/token"

        # Cache for JWKS (JSON Web Key Set)
        self._jwks_cache: Optional[Dict[str, Any]] = None

        # Validate configuration
        if not self.user_pool_id:
            logger.warning("Cognito User Pool ID not configured")
        if not self.client_id:
            logger.warning("Cognito Client ID not configured")

        logger.info("AWS Cognito provider initialized",
                   user_pool_id=self.user_pool_id,
                   region=self.region)

    def _get_cognito_domain(self) -> str:
        """Get the Cognito domain from the user pool ID."""
        # Extract domain from user pool ID
        # Format: https://cognito-idp.{region}.amazonaws.com/{user_pool_id}
        return f"cognito-idp.{self.region}.amazonaws.com"

    async def _get_jwks(self) -> Dict[str, Any]:
        """
        Retrieve JSON Web Key Set (JWKS) from Cognito.

        Returns:
            JWKS document with public keys for token verification
        """
        if self._jwks_cache:
            return self._jwks_cache

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.jwks_uri)
                response.raise_for_status()

                jwks = response.json()
                self._jwks_cache = jwks

                logger.debug("JWKS retrieved from Cognito", keys_count=len(jwks.get("keys", [])))
                return jwks

        except Exception as e:
            logger.error("Failed to retrieve JWKS from Cognito",
                        error=str(e),
                        jwks_uri=self.jwks_uri)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Failed to retrieve authentication keys"
            )

    async def validate_token(self, token: str) -> Dict[str, Any]:
        """
        Validate a Cognito JWT token (ID token or access token).

        Args:
            token: Cognito JWT token

        Returns:
            Dict containing validated user information

        Raises:
            HTTPException: If token is invalid
        """
        try:
            # Decode token header to get key ID
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get("kid")

            if not kid:
                raise ValueError("Token missing key ID (kid)")

            # Get JWKS and find matching key
            jwks = await self._get_jwks()
            key = None

            for jwk in jwks.get("keys", []):
                if jwk.get("kid") == kid:
                    key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(jwk))
                    break

            if not key:
                raise ValueError("No matching key found in JWKS")

            # Verify and decode token
            payload = jwt.decode(
                token,
                key=key,
                algorithms=["RS256"],
                audience=self.client_id,
                issuer=self.issuer,
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_aud": True,
                    "verify_iss": True
                }
            )

            # Check token use (should be "id" for ID tokens or "access" for access tokens)
            token_use = payload.get("token_use")
            if token_use not in ["id", "access"]:
                raise ValueError(f"Invalid token_use: {token_use}")

            logger.info("Cognito token validated successfully",
                       user_id=payload.get("sub"),
                       token_use=token_use)

            # For access tokens, we need to call userinfo endpoint
            if token_use == "access":
                user_info = await self.get_user_info(token)
                return self.normalize_user_info(user_info)

            # For ID tokens, we have all the user info in the payload
            return self.normalize_user_info(payload)

        except jwt.ExpiredSignatureError:
            logger.warning("Cognito token expired")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.InvalidTokenError as e:
            logger.error("Invalid Cognito token", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}"
            )
        except Exception as e:
            logger.error("Cognito token validation failed", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token validation failed"
            )

    def get_oauth_config(self) -> Dict[str, Any]:
        """
        Get Cognito OAuth configuration.

        Returns:
            OAuth configuration for Cognito
        """
        cognito_domain = self._get_cognito_domain()

        return {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "authorization_endpoint": f"https://{cognito_domain}/oauth2/authorize",
            "token_endpoint": self.token_endpoint,
            "userinfo_endpoint": self.userinfo_endpoint,
            "issuer": self.issuer,
            "jwks_uri": self.jwks_uri,
            "scopes": ["openid", "email", "profile"],
            "region": self.region,
            "user_pool_id": self.user_pool_id
        }

    async def get_user_info(self, token: str) -> Dict[str, Any]:
        """
        Get user information from Cognito using an access token.

        Args:
            token: Cognito access token

        Returns:
            Dict containing user information

        Raises:
            HTTPException: If request fails
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.userinfo_endpoint,
                    headers={"Authorization": f"Bearer {token}"}
                )

                if response.status_code != 200:
                    logger.error("Cognito userinfo request failed",
                               status_code=response.status_code,
                               response=response.text)
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Failed to get user info from Cognito"
                    )

                user_info = response.json()
                logger.info("Cognito user info retrieved successfully",
                           user_id=user_info.get("sub"),
                           email=user_info.get("email"))

                return user_info

        except httpx.HTTPError as e:
            logger.error("HTTP error getting Cognito user info", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Failed to communicate with Cognito"
            )

    async def validate_logout(self, token: str) -> bool:
        """
        Validate and handle logout for Cognito.

        Cognito supports global sign-out which invalidates all tokens
        for a user. This would require additional API calls to Cognito.

        Args:
            token: The OAuth access token

        Returns:
            True if logout was successful
        """
        # For now, just log the logout
        # Full implementation would call Cognito's GlobalSignOut API
        logger.info("Cognito logout processed (client-side)")

        # TODO: Implement GlobalSignOut if needed:
        # import boto3
        # cognito_client = boto3.client('cognito-idp', region_name=self.region)
        # cognito_client.global_sign_out(AccessToken=token)

        return True

    def get_provider_name(self) -> str:
        """
        Get provider name.

        Returns:
            "cognito"
        """
        return "cognito"

    def supports_refresh(self) -> bool:
        """
        Check if Cognito supports token refresh.

        Returns:
            True (Cognito supports refresh tokens)
        """
        return True

    async def refresh_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """
        Refresh a Cognito access token.

        Args:
            refresh_token: Cognito refresh token

        Returns:
            Dict with new access token and expiry
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.token_endpoint,
                    data={
                        "grant_type": "refresh_token",
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "refresh_token": refresh_token
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )

                if response.status_code != 200:
                    logger.error("Cognito token refresh failed",
                               status_code=response.status_code,
                               response=response.text)
                    return None

                token_data = response.json()
                logger.info("Cognito token refreshed successfully")

                return {
                    "access_token": token_data.get("access_token"),
                    "id_token": token_data.get("id_token"),
                    "expires_in": token_data.get("expires_in", 3600),
                    "token_type": token_data.get("token_type", "Bearer")
                }

        except Exception as e:
            logger.error("Error refreshing Cognito token", error=str(e))
            return None

    def normalize_user_info(self, raw_user_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize Cognito user info to standard format.

        Cognito user attributes may have different naming conventions
        (e.g., cognito:username, email_verified as string "true"/"false")

        Args:
            raw_user_info: Raw user info from Cognito

        Returns:
            Normalized user information
        """
        # Handle email_verified as string or boolean
        email_verified = raw_user_info.get("email_verified", False)
        if isinstance(email_verified, str):
            email_verified = email_verified.lower() == "true"

        # Get username (Cognito uses 'cognito:username' or 'username')
        username = raw_user_info.get("cognito:username") or raw_user_info.get("username")

        return {
            "sub": raw_user_info.get("sub"),
            "email": raw_user_info.get("email"),
            "email_verified": email_verified,
            "name": raw_user_info.get("name") or username or raw_user_info.get("email"),
            "picture": raw_user_info.get("picture"),
            "given_name": raw_user_info.get("given_name"),
            "family_name": raw_user_info.get("family_name"),
            "username": username,
            "provider": "cognito"
        }
