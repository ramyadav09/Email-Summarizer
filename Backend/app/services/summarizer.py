from langchain_mistralai import ChatMistralAI
from langchain_core.messages import HumanMessage
from app.config import MISTRAL_API_KEY


def summarize(text: str) -> str:
    llm = ChatMistralAI(model="mistral-large-latest", api_key=MISTRAL_API_KEY)
    response = llm.invoke([HumanMessage(content=f"Summarize this email in 2 sentences:\n\n{text}")])
    return response.content
