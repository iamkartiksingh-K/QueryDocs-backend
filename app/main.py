from fastapi import FastAPI
from fastapi.security import OAuth2PasswordBearer
from app.database import Base, engine
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
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


app.include_router(router)
app.include_router(authRouter, prefix="/auth", tags=["Auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
