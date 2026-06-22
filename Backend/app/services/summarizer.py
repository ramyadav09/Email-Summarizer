from langchain_mistralai import ChatMistralAI
from app.config import MISTRAL_API_KEY
from langchain_core.prompts import ChatPromptTemplate


def summarize(text: str) -> str:
    llm = ChatMistralAI(model="mistral-large-latest", api_key=MISTRAL_API_KEY)
    prompt = ChatPromptTemplate.from_template(
        "Summarize this email in 2-3 sentences:\n\n{text}"
    )
    response = llm.invoke(prompt.format_messages(text=text))
    return response.content
