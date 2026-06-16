from fastapi import FastAPI, status, Depends, HTTPException
from schema import *
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_session
from sqlalchemy import select,update
from models import *
from auth import hash_password, verify_password, get_current_user, create_token
from fastapi.security import OAuth2PasswordRequestForm
from rate_limit import limit_check
from tasks import compute_reading_time, celery_app
from cache import redis_client, cache_delete, cache_get, cache_set
from celery.result import AsyncResult

app = FastAPI(title="Mini Article API")

@app.get("/")
def get_main():
    return {"status":"OK", "service":"Working"}

#auth
@app.post("/auth/register", response_model=UserRead, status_code = status.HTTP_201_CREATED)
async def register(payload:UserCreate, session:AsyncSession=Depends(get_session)):
    existing = await session.execute(select(User).where(User.email == payload.email))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email = payload.email,
        hashed_password = hash_password(payload.password),
        tier = payload.tier
    )

    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@app.post('auth/token', response_model=Auth, status_code=status.HTTP_200_OK)
async def login(
        form_data: OAuth2PasswordRequestForm = Depends(),
        session:AsyncSession = Depends(get_session)
    ):
    result = await session.execute(select(User).where(form_data.email == User.email))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="incorrect credentials",
            headers={"WWW-Authenticate":"Bearer"}
        )
    
    return Auth(access_token=create_token(user.id))


#Get User

@app.get("/users/me", response_model=UserRead, status_code=status.HTTP_200_OK)
async def get_me(current_user:User=Depends(get_current_user)):
    return current_user

@app.get("/users/{user_id}", response_model=UserRead, status_code=status.HTTP_200_OK)
async def get_user_by_id(user_id:int, session:AsyncSession=Depends(get_session)):
    result = await session.get(User, user_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")
    return result
    
#Create Article

@app.post("/create-article", response_model=ArticleCreate, status_code=status.HTTP_201_CREATED)
async def create_article(
    payload:ArticleCreate,
    session:AsyncSession=Depends(get_session),
    current_user:User=Depends(get_current_user)
):
    await limit_check(current_user.id, current_user.tier)

    article = Article(
        title = payload.title,
        body = payload.body,
        author = current_user.id
    )

    session.add(article)
    await session.commit()
    await session.refresh(article)

    task = compute_reading_time.delay(article.id, article.body)

    await redis_client.publish(
        "new_articles",
        ArticleRead.model_validate(article).model_dump_json()
    )

    return {
        "article":ArticleRead.model_validate(article).model_dump_json(),
        "task_id":task.id
    }

#Get Articles
@app.get('/article/{article_id:int}', response_model=ArticleRead, status_code=status.HTTP_200_OK)
async def get_article(
    article_id:int, 
    session:AsyncSession=Depends(get_session), 
):
    key = f"article:{article_id}"
    cached = await cache_get(key)
    if cached is not None:
        return ArticleCreate.model_validate_json(cached)
    
    result = await session.get(Article, article_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="no article found"
        )
    data = ArticleRead.model_validate(result)
    await cache_set(key, data.model_dump_json(), ttl=60)
    return data


#update Articles

@app.put('/update_article/{article_id}', response_model=ArticleRead, status_code=status.HTTP_201_CREATED)
async def updated_article(
    article_id:int, 
    payload:ArticleCreate,
    session:AsyncSession = Depends(get_session),
    current_user:User = Depends(get_current_user)
):
    article = await session.get(Article, article_id)

    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="no article found"
        )
    if article.id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
            detail="only the author can edit"
        )
    
    article.title = payload.title
    article.body = payload.body
    await session.commit()
    await session.refresh(article)

    await cache_delete(f"article:{article_id}")
    return article

#delete Articles

@app.delete('/article/{article_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_article(
    article_id:int, 
    session:AsyncSession=Depends(get_session), 
    current_user:User=Depends(get_current_user)
):
    article = await session.get(Article, article_id)
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="no article found"
        )
    if article.author != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
            detail="Only author can delete"
        )
    
    await session.delete(article)
    await session.commit()
    await cache_delete(f"article:{article_id}")

#celery task
@app.get("/task/{task_id}")
async def get_task_status(task_id: str):
    result = AsyncResult(task_id, app=celery_app)

    response = {"task_id":task_id, "status":result.status}
    if result.ready():
        response["result"] = result.result
    return response