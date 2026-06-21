# Email Summarizer

A full-stack app that fetches emails from Gmail and summarizes them using LangChain.

## Project Structure

```
Email-Summarizer/
├── Backend/   # Python + Gmail API + LangChain
└── Frontend/  # React + Vite + Tailwind CSS
```

## Prerequisites

- Python 3.10+
- Node.js 18+
- A Google Cloud project with the Gmail API enabled
- OAuth 2.0 `credentials.json` downloaded from Google Cloud Console

## Backend Setup

```bash
cd Backend
python -m venv myenv
myenv\Scripts\activate        # Windows
pip install -r requirements.txt
```

Place your `credentials.json` in the `Backend/` folder, then run:

```bash
python main.py
```

On first run, a browser window will open for Google OAuth. A `token.json` will be saved locally for subsequent runs.

## Frontend Setup

```bash
cd Frontend
npm install
npm run dev
```

The app will be available at `http://localhost:5173`.

## Environment Variables

Create a `.env` file inside `Backend/` for any additional config:

```
# Backend/.env
OPENAI_API_KEY=<your_key>
```

> Never commit `credentials.json`, `token.json`, or `.env` files.
