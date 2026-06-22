# Email Summarizer — Frontend

React + Vite + Tailwind CSS frontend for the Email Summarizer app.

## Stack

- [React 19](https://react.dev/)
- [Vite 8](https://vitejs.dev/)
- [Tailwind CSS v4](https://tailwindcss.com/)

## Setup

```bash
npm install
npm run dev    # dev server → http://localhost:5173
npm run build  # production build → dist/
```

## Structure

```
src/
├── components/
│   ├── Header.jsx       # Top nav with logout
│   └── EmailCard.jsx    # Email row with summarize action
├── pages/
│   ├── LoginPage.jsx    # Connect Gmail landing page
│   └── InboxPage.jsx    # Inbox with date filter + email list
├── data/
│   └── mockEmails.js    # Placeholder data
└── App.jsx              # Token state + page routing
```

## Environment

Expects backend running at `http://localhost:8000`. Update the fetch URLs in `InboxPage.jsx` and `EmailCard.jsx` if your backend runs on a different port.
