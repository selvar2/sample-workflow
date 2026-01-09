"""
Configuration module for the ServiceNow MCP server.
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class AuthType(str, Enum):
    """Authentication types supported by the ServiceNow MCP server."""

    BASIC = "basic"
    OAUTH = "oauth"
    API_KEY = "api_key"


class BasicAuthConfig(BaseModel):
    """Configuration for basic authentication."""

    username: str
    password: str


class OAuthConfig(BaseModel):
    """Configuration for OAuth authentication.
    
    Supports two grant types:
    - client_credentials: Only requires client_id and client_secret
    - password: Requires client_id, client_secret, username, and password
    """

    client_id: str
    client_secret: str
    username: Optional[str] = None  # Required only for password grant
    password: Optional[str] = None  # Required only for password grant
    token_url: Optional[str] = None
    grant_type: str = "client_credentials"  # "client_credentials" or "password"


class ApiKeyConfig(BaseModel):
    """Configuration for API key authentication."""

    api_key: str
    header_name: str = "X-ServiceNow-API-Key"


class AuthConfig(BaseModel):
    """Authentication configuration."""

    type: AuthType
    basic: Optional[BasicAuthConfig] = None
    oauth: Optional[OAuthConfig] = None
    api_key: Optional[ApiKeyConfig] = None


class ServerConfig(BaseModel):
    """Server configuration."""

    instance_url: str
    auth: AuthConfig
    debug: bool = False
    timeout: int = 30

    @property
    def api_url(self) -> str:
        """Get the API URL for the ServiceNow instance."""
        return f"{self.instance_url}/api/now"
