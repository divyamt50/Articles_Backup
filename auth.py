import os
import bcrypt
import jwt
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta, timezone
from fastapi import Depends,HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_session
from models import User

DB_URL = os.getenv("DB_URL", "postgresql+psycopg://postgres:password@localhost:5432/fastapi_db")
JWT_SECRET = os.getenv("JWT_SECRET", "jwt_secret")
ALG = 'HS256'
TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

def hash_password(plain:str) -> str:
    return bcrypt.hashpw(plain.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(plain:str, hash:str) -> bool:
    return bcrypt.checkpw(plain.encode('utf-8'), hash.encode('utf-8'))

def create_token(user_id:int)->str:
    exp_time = datetime.now(timezone.utc) + timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    payload = {'sub':str(user_id), 'exp':exp_time}
    return jwt.encode(payload, JWT_SECRET, algorithm=ALG)


async def get_current_user(
        token:str=Depends(oauth2_scheme),
        session:AsyncSession=Depends(get_session)
)->User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate":"Bearer"}
    )

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALG])
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_error
    except jwt.PyJWTError:
        raise credentials_error
    
    user = await session.get(User, int(user_id))
    if not user:
        raise credentials_error
    return user