from fastapi import Body, FastAPI, status
from datetime import datetime, timedelta
from typing import Union, Optional
from fastapi import Depends, FastAPI, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
import logging
import random
import string
import time
from fastapi.responses import RedirectResponse
from models import User
from database import engine, SessionLocal
import models
from sqlalchemy.orm import Session
from db_utils import add_new_user, flush_users_table, get_all_users, get_users_db_size

# create all models
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="FastAPI Test Application"
)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



logging.basicConfig(filename="fastapi.log",
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)

logger = logging.getLogger(__name__)

SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

fake_users_db = {

}


class DummyPostBody(BaseModel):
    text: str
    title: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Union[str, None] = None


class UserBase(BaseModel):
    username: str
    email: str
    disabled: bool = False


class UserRegistrationModel(UserBase):
    password: str
    
    class Config:
        orm_mode = True


class UserInDB(UserBase):
    hashed_password: str


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def get_user(db: dict, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)
    return False


def generate_password_hash(password: str) -> bool:
    # returns password hash
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def authenticate_user(db, username: str, password: str):
    user = get_user(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)

    except JWTError:
        raise credentials_exception
    user = get_user(fake_users_db, username=token_data.username)
    if user is None:
        return credentials_exception
    return user


async def get_current_active_user(current_user: UserBase = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


@app.get("/", include_in_schema=False)
async def root():
    # redirects user from root page to swagger doc
    return RedirectResponse("/docs")


@app.get("/get/db")
async def get_db_items(db: Session = Depends(get_db)):
    return get_all_users(db)


@app.get("/clear/db")
async def clear_db(db: Session = Depends(get_db)):
    flush_users_table(db)
    return "db cleared"


@app.get("/size/db")
def get_db_size(db: Session = Depends(get_db)):
    return get_users_db_size(db)   


@app.post("/register")
async def register_user(user: UserRegistrationModel, db: Session = Depends(get_db)):
    user_exist = get_user(fake_users_db, user.username)
    if user_exist:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"user with username: <{user.username}> already exist")
    else:

        user_data = user.dict()
        # username = user_data.get("username")
        # email = user_data.get("email")
        # disabled = user_data.get("disabled")
        # password = user_data.get("password")
        hashed_password = generate_password_hash(user.password)
        user_data.update({"hashed_password": hashed_password})
        user = User(
            **user_data
        )
        add_new_user(db, user)


@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(
        fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.post('/dummy_post')
def simple_post_request(body: UserRegistrationModel):
    return body


@app.get("/users/me/", response_model=UserBase)
async def read_users_me(current_user: UserBase = Depends(get_current_active_user)):
    return current_user


@app.middleware("http")
async def log_requests(request: Request, call_next):
    idem = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    logger.info(f"rid={idem} start request path={request.url.path}")
    start_time = time.time()

    response = await call_next(request)

    process_time = (time.time() - start_time) * 1000
    formatted_process_time = '{0:.2f}'.format(process_time)
    logger.info(
        f"rid={idem} completed_in={formatted_process_time}ms status_code={response.status_code}")

    return response

