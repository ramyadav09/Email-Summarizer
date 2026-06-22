import os
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
REDIRECT_URI = "http://localhost:8000/auth/google/callback"
FRONTEND_URL = "http://localhost:5173"
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
ALLOWED_DOMAINS = ["kiit.ac.in", "seagol.com"]
