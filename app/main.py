from fastapi import FastAPI
from fastapi.security import OAuth2PasswordBearer
from app.database import Base, engine
from fastapi.middleware.cors import CORSMiddleware
from app.api.files import router as filesRouter
from app.api.auth import router as authRouter

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True
)


app.include_router(authRouter, prefix="/auth", tags=["Auth"])
app.include_router(filesRouter, prefix="/files", tags=["files"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
