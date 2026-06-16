from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field

#Auth
class Auth(BaseModel):
    access_token:str
    token_type:str = "bearer"

#user create
class UserCreate(BaseModel):
    email:EmailStr
    password:str = Field(min_length=8, max_length=72)
    tier:str = Field(default="Free", pattern="^(free|pro)$")

class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id:int
    email:EmailStr
    tier:str
    created_at:datetime

class ArticleCreate(BaseModel):

    title:str = Field(min_length=1, max_length=255)
    body:str = Field(min_length=1)
    author:str = Field(min_length=1, max_length=255)

class ArticleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:int
    title:str = Field(min_length=1, max_length=255)
    body:str = Field(min_length=1)
    author_id:int
    reading_time_seconds: int|None
    created_at:datetime