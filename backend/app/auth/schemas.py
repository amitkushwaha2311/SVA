from typing import List
from pydantic import BaseModel, EmailStr, Field

class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    display_name: str = Field(..., min_length=1)
    workspace_name: str = Field(..., min_length=1)

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class WorkspaceSummary(BaseModel):
    id: str
    name: str
    role: str

class AuthResponse(BaseModel):
    user_id: str
    email: str
    display_name: str
    workspace_ids: List[str]

class MeResponse(BaseModel):
    user_id: str
    email: str
    display_name: str
    status: str
    workspaces: List[WorkspaceSummary]
