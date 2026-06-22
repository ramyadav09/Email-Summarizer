from langchain_mistralai import ChatMistralAI
from app.config import MISTRAL_API_KEY
from langchain_core.prompts import ChatPromptTemplate
from email.mime.text import MIMEText
import base64


def summarize(text: str) -> str:
    llm = ChatMistralAI(model="mistral-large-latest", api_key=MISTRAL_API_KEY)
    prompt = ChatPromptTemplate.from_template(
        "Summarize this body of email in 2-3 sentences:\n\n{text}"
    )
    response = llm.invoke(prompt.format_messages(text=text))
    return response.content


def generate_reply(original_email: dict) -> str:
    llm = ChatMistralAI(model="mistral-large-latest", api_key=MISTRAL_API_KEY)
    prompt = ChatPromptTemplate.from_template("""
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

        Reply:
    """)

    response = llm.invoke(
        prompt.format_messages(
            from_addr=original_email["from"],
            subject=original_email["subject"],
            body=original_email["body"],
        )
    )

    return response.content
