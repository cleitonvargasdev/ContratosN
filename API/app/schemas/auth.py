from pydantic import BaseModel, ConfigDict


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "<access-jwt-token>",
                "refresh_token": "<refresh-jwt-token>",
                "token_type": "bearer",
            }
        }
    )


class TokenPayload(BaseModel):
    sub: str
    token_type: str
    tenant_id: str | None = None


class RefreshTokenRequest(BaseModel):
    refresh_token: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "refresh_token": "<refresh-jwt-token>",
            }
        }
    )
