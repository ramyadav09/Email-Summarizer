import os
import secrets
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from app.routers import auth, emails

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=secrets.token_hex(32))
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(emails.router)
