from typing import Optional, Union
from pydantic import BaseModel

class User(BaseModel):
    id: Optional[int] = None
    username: str
    mail_address: str
    password: str
    memo: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False

class Text(BaseModel):
    id: Optional[int] = None
    name: str
    contents: str
    memo: Optional[str] = None
    description: Optional[str] = None
    course_id: int
    order_id: Optional[int] = 0

class Course(BaseModel):
    id: Optional[int] = None
    name: str
    memo: Optional[str] = None
    description: Optional[str] = None

class UsersCourses(BaseModel):
    id: Optional[int] = None
    user_id: int
    course_id: int

class UsersTexts(BaseModel):
    id: Optional[int] = None
    user_id: int
    text_id: int
    is_completed: bool = False

class TokenData(BaseModel):
    username: Union[str, None] = None
