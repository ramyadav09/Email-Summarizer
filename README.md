# Email Summarizer

A full-stack app that fetches emails from Gmail and summarizes them using Mistral AI via LangChain.

## Project Structure

```
Email-Summarizer/
├── Backend/
│   ├── app/
│   │   ├── core/
│   │   │   ├── config.py        # Settings via pydantic-settings
│   │   │   ├── database.py      # SQLAlchemy setup
│   │   │   ├── dependencies.py
│   │   │   └── logging.py
│   │   ├── models/              # SQLAlchemy models
│   │   ├── routers/
│   │   │   ├── auth.py          # /auth/login, /auth/google/callback
│   │   │   └── emails.py        # /api/emails, /api/summarize, /api/generate-response, /api/send-reply
│   │   ├── schemas/             # Pydantic schemas
│   │   ├── services/
│   │   │   ├── email_repository.py # DB operations
│   │   │   ├── generation.py    # Mistral AI logic (summarize, reply)
│   │   │   └── gmail.py         # Gmail API logic
│   │   └── main.py              # FastAPI app entry point
│   ├── requirements.txt
│   └── .env
└── Frontend/
    ├── src/
    │   ├── components/
    │   │   ├── Header.jsx
    │   │   └── EmailCard.jsx
    │   ├── pages/
    │   │   ├── LoginPage.jsx
    │   │   └── InboxPage.jsx
    │   ├── store/               # Redux Toolkit store
    │   └── App.jsx
    ├── package.json
    └── vite.config.js
```

## Prerequisites

- Python 3.10+
- Node.js 18+
- Google Cloud project with Gmail API enabled
- OAuth 2.0 credentials (Client ID + Client Secret)
- Mistral AI API key

## Backend Setup

```bash
cd Backend
python -m venv myenv
myenv\Scripts\activate        # Windows
pip install -r requirements.txt
```

Create a `.env` file in `Backend/`:

```env
CLIENT_ID=<your_google_client_id>
CLIENT_SECRET=<your_google_client_secret>
MISTRAL_API_KEY=<your_mistral_api_key>
DEBUG=True
```

Start the server:

```bash
uvicorn app.main:app --reload
```

Backend runs at `http://localhost:8000`.

## Frontend Setup

```bash
cd Frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`.

## Auth Flow

1. User clicks **Connect Gmail** → redirected to `http://localhost:8000/auth/login`
2. Google OAuth consent screen appears
3. On approval, backend exchanges code for access token
4. User is redirected back to frontend with `?access_token=...`
5. Token is stored in `localStorage` and used for all API calls

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/auth/login` | Starts Google OAuth flow |
| GET | `/auth/google/callback` | OAuth callback, returns token |
| GET | `/api/emails?after=YYYY/MM/DD&before=YYYY/MM/DD&read_status=unread` | Fetch emails by date range and read status |
| GET | `/api/emails/{email_id}` | Fetch full detail of a single email |
| POST | `/api/summarize` | Summarize an email by ID (uses DB caching) |
| POST | `/api/generate-response` | Generate an AI-drafted reply |
| POST | `/api/send-reply` | Send a reply email within the same thread |

## Features

- Google OAuth 2.0 login
- Fetch Gmail emails filtered by allowed domains
- Date range and Read/Unread filters
- AI-powered email summarization and reply generation using Mistral AI
- Database caching using SQLAlchemy (SQLite) for faster subsequent loads
- Token persisted in `localStorage` across page refreshes
- State management via Redux Toolkit on the frontend

## Security Notes

- Never commit `.env`, `client_secret.json`, or `token.json`
- All three are listed in `.gitignore`
- Rotate credentials immediately if accidentally exposed
