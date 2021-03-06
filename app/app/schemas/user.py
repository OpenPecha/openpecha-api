from typing import Optional

from pydantic import BaseModel


# Shared proterties
class UserBase(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    is_superuser: Optional[bool] = False


# Properties to receive via API on creation
class UserCreate(UserBase):
    pass


# Properties to receive via API on update
class UserUpdate(UserBase):
    pass


class UserInDBBase(UserBase):
    class Config:
        orm_mode = True


# Additional properties to return via API
class User(UserInDBBase):
    pass


# Additational properties stored in DB
class UserInDB(UserInDBBase):
    pass
