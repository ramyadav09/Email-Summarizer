# Email Summarizer

A full-stack app that fetches emails from Gmail and summarizes them using Mistral AI via LangChain.

## Project Structure

```
Email-Summarizer/
├── Backend/
│   ├── app/
│   │   ├── routers/
│   │   │   ├── auth.py          # /auth/login, /auth/google/callback
│   │   │   └── emails.py        # /api/emails, /api/summarize
│   │   ├── services/
│   │   │   ├── gmail.py         # Gmail API logic
│   │   │   └── summarizer.py    # Mistral/LangChain summarization
│   │   └── config.py            # Env vars
│   ├── main.py                  # FastAPI app entry point
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
    │   ├── data/
    │   │   └── mockEmails.js
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
```

Start the server:

```bash
uvicorn main:app --reload
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
| GET | `/api/emails?after=YYYY/MM/DD&before=YYYY/MM/DD` | Fetch emails by date range |
| POST | `/api/summarize` | Summarize an email by ID |

## Features

- Google OAuth 2.0 login
- Fetch Gmail emails filtered by allowed domains
- Date range filter (From / To date pickers)
- AI-powered email summarization using Mistral AI
- Token persisted in `localStorage` across page refreshes

## Security Notes

- Never commit `.env`, `client_secret.json`, or `token.json`
- All three are listed in `.gitignore`
- Rotate credentials immediately if accidentally exposed
