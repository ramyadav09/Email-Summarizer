"""LLM-powered email summarization and reply generation via Mistral AI."""

from langchain_mistralai import ChatMistralAI
from langchain_core.prompts import ChatPromptTemplate

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Singleton LLM client — avoids re-creating the HTTP connection pool per call
# ---------------------------------------------------------------------------

_llm = ChatMistralAI(model="mistral-large-latest", api_key=settings.MISTRAL_API_KEY)

# ---------------------------------------------------------------------------
# Prompt templates
# ---------------------------------------------------------------------------

_SUMMARIZE_PROMPT = ChatPromptTemplate.from_template(
    "Summarize this body of email in 2-3 sentences:\n\n{text}"
)

_REPLY_PROMPT = ChatPromptTemplate.from_template(
    """\
You are an experienced executive email assistant.

Your task is to draft a professional email reply based on the incoming message.

Original Email:

From: {from_addr}
Re: {subject}

Body:
{body}

Instructions:
- Understand the sender's intent and respond appropriately.
- Answer all questions raised in the email.
- Maintain a professional, polite, and concise tone.
- Do not invent facts or commitments that are not supported by the email.
- If information is missing, politely request clarification.
- Keep the reply under 200 words unless the email requires more detail.
- Include a greeting and a professional closing.
- Return only the email reply text.

Reply:"""
)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def summarize(text: str) -> str:
    """Generate a 2-3 sentence summary of the given email body text."""
    logger.info("Generating summary for %d-char text", len(text))
    response = _llm.invoke(_SUMMARIZE_PROMPT.format_messages(text=text))
    logger.debug("Summary generated successfully")
    return response.content


def generate_reply(original_email: dict) -> str:
    """Draft a professional reply to the given email."""
    logger.info(
        "Generating reply for email from=%s subject=%s",
        original_email.get("from", "?"),
        original_email.get("subject", "?"),
    )
    response = _llm.invoke(
        _REPLY_PROMPT.format_messages(
            from_addr=original_email["from"],
            subject=original_email["subject"],
            body=original_email["body"],
        )
    )
    logger.debug("Reply generated successfully")
    return response.content
