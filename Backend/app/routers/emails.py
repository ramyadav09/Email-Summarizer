from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel
from app.services.gmail import fetch_emails, fetch_email_body
from app.services.summarizer import summarize

router = APIRouter(prefix="/api")


class SummarizeRequest(BaseModel):
    id: str


@router.get("/emails")
def get_emails(authorization: str = Header(...)):
    token = authorization.removeprefix("Bearer ")
    try:
        return fetch_emails(token)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/summarize")
def summarize_email(req: SummarizeRequest, authorization: str = Header(...)):
    token = authorization.removeprefix("Bearer ")
    try:
        body = fetch_email_body(token, req.id)
        return {"summary": summarize(body)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
