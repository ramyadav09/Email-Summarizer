from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.services.gmail import (
    fetch_emails,
    fetch_email_detail,
    send_reply,
)
from app.services.generation import summarize, generate_reply

router = APIRouter(prefix="/api")


class SummarizeRequest(BaseModel):
    id: str
    body: Optional[str] = None


class GenerateReplyRequest(BaseModel):
    id: str
    from_addr: Optional[str] = None
    subject: Optional[str] = None
    body: Optional[str] = None


class SendReplyRequest(BaseModel):
    id: str
    thread_id: str
    to: str
    subject: str
    body: str
    message_id: str = ""


@router.get("/emails")
def get_emails(
    authorization: str = Header(...),
    after: str = None,
    before: str = None,
    read_status: str = None,
):
    token = authorization.removeprefix("Bearer ")
    try:
        return fetch_emails(token, after=after, before=before, read_status=read_status)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/emails/{id}")
async def get_email_by_id(id: str, authorization: str = Header(...)):
    token = authorization.removeprefix("Bearer ")
    try:
        return fetch_email_detail(token, id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/summarize")
def summarize_email(req: SummarizeRequest, authorization: str = Header(...)):
    token = authorization.removeprefix("Bearer ")
    try:
        # Use pre-fetched body from frontend, fallback to fetching
        body_text = req.body
        if not body_text:
            detail = fetch_email_detail(token, req.id)
            body_text = detail.get("body") or detail.get("body_html") or detail.get("snippet", "")
        return {"summary": summarize(body_text)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/generate-response")
def generate_response(req: GenerateReplyRequest, authorization: str = Header(...)):
    token = authorization.removeprefix("Bearer ")
    try:
        # Use pre-fetched email data from frontend, fallback to fetching
        if req.body and req.from_addr and req.subject:
            email_data = {"from": req.from_addr, "subject": req.subject, "body": req.body}
        else:
            detail = fetch_email_detail(token, req.id)
            email_data = {
                "from": detail.get("from", ""),
                "subject": detail.get("subject", ""),
                "body": detail.get("body") or detail.get("body_html") or detail.get("snippet", ""),
            }
        reply = generate_reply(email_data)
        return {"reply": reply}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/send-reply")
def send_reply_endpoint(req: SendReplyRequest, authorization: str = Header(...)):
    token = authorization.removeprefix("Bearer ")
    try:
        result = send_reply(
            token=token,
            thread_id=req.thread_id,
            to=req.to,
            subject=req.subject,
            body=req.body,
            original_message_id=req.message_id or None,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
