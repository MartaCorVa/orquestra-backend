from pydantic import BaseModel


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    must_change_password: bool


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str