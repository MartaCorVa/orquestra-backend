from pydantic import BaseModel


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    role: str
    must_change_password: bool
    user: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str