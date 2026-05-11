from pydantic import BaseModel, Field, model_validator


class RegisterRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    full_name: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=4, max_length=128)


class RegisterResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    role: str
    site_id: int | None = None


class LoginRequest(BaseModel):
    login_id: str | None = Field(default=None, min_length=2, max_length=255, description="Email or ID part before '@'")
    email: str | None = Field(default=None, description="Legacy key. Use login_id instead.")
    password: str = Field(min_length=4, max_length=128)

    @model_validator(mode="after")
    def validate_identifier(self) -> "LoginRequest":
        if self.login_id is None and self.email is None:
            raise ValueError("login_id or email is required")
        return self

    @property
    def identifier(self) -> str:
        return (self.login_id or self.email or "").strip()


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    role: str
    site_id: int | None = None


class MeResponse(BaseModel):
    user_id: int
    email: str
    full_name: str
    role: str
    is_active: bool
