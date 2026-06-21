from googleapiclient.discovery import build

service = build("gmail", "v1", credentials=creds)

results = service.users().messages().list(userId="me", maxResults=10).execute()

messages = results.get("messages", [])
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()
app.get("/summarize")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class Tokens(BaseModel):
    access_token: str
    refresh_token: str


@app.post("/login")
def read_root(tokens: Tokens):
    print(tokens.access_token)
    print(tokens.refresh_token)
