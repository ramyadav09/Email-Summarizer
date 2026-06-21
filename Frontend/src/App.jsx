import { useState } from "react";
import { useAuth0 } from "@auth0/auth0-react";

const MOCK_EMAILS = [
  {
    id: 1,
    from: "alice@example.com",
    subject: "Q3 Report",
    snippet: "Please find the Q3 report attached for your review...",
    summary: null,
  },
  {
    id: 2,
    from: "bob@example.com",
    subject: "Team Standup Notes",
    snippet: "Here are the notes from today's standup meeting...",
    summary: null,
  },
  {
    id: 3,
    from: "carol@example.com",
    subject: "Invoice #1042",
    snippet: "Attached is invoice #1042 due by end of month...",
    summary: null,
  },
];

function EmailCard({ email, onSummarize, getToken }) {
  const [loading, setLoading] = useState(false);

  const handleSummarize = async () => {
    setLoading(true);
    const token = await getToken();
    console.log("access_token:", token); // remove once backend is connected
    // const res = await fetch("/api/summarize", {
    //   method: "POST",
    //   headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
    //   body: JSON.stringify({ id: email.id }),
    // });
    await new Promise((r) => setTimeout(r, 1200)); // replace with real API call
    onSummarize(
      email.id,
      "AI-generated summary will appear here once the backend is connected.",
    );
    setLoading(false);
  };

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <p className="text-xs text-gray-400 mb-0.5">{email.from}</p>
          <h3 className="font-semibold text-gray-800 truncate">
            {email.subject}
          </h3>
          <p className="text-sm text-gray-500 mt-1 line-clamp-2">
            {email.snippet}
          </p>
        </div>
        <button
          onClick={handleSummarize}
          disabled={loading || email.summary}
          className="shrink-0 text-sm px-3 py-1.5 rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? "Summarizing…" : email.summary ? "Done" : "Summarize"}
        </button>
      </div>
      {email.summary && (
        <div className="mt-3 p-3 bg-indigo-50 border border-indigo-100 rounded-lg text-sm text-indigo-800">
          {email.summary}
        </div>
      )}
    </div>
  );
}

function Header({ user, onLogout }) {
  return (
    <header className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
      <h1 className="text-lg font-bold text-indigo-600">📧 Email Summarizer</h1>
      <div className="flex items-center gap-3">
        <img
          src={user.picture}
          alt={user.name}
          className="w-8 h-8 rounded-full"
        />
        <span className="text-sm text-gray-600 hidden sm:block">
          {user.email}
        </span>
        <button
          onClick={onLogout}
          className="text-sm px-3 py-1.5 rounded-lg border border-gray-300 text-gray-600 hover:bg-gray-50 transition-colors"
        >
          Logout
        </button>
      </div>
    </header>
  );
}

export default function App() {
  const {
    isLoading,
    isAuthenticated,
    error,
    loginWithRedirect,
    logout,
    user,
    getAccessTokenSilently,
  } = useAuth0();
  const [emails, setEmails] = useState(MOCK_EMAILS);

  const handleSummarize = (id, summary) =>
    setEmails((prev) => prev.map((e) => (e.id === id ? { ...e, summary } : e)));

  const handleLogout = () =>
    logout({ logoutParams: { returnTo: window.location.origin } });

  if (isLoading)
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin" />
      </div>
    );

  if (error)
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-red-500">Authentication error: {error.message}</p>
      </div>
    );

  if (!isAuthenticated)
    return (
      <div className="min-h-screen bg-gradient-to-br from-indigo-50 to-white flex items-center justify-center px-4">
        <div className="text-center max-w-md">
          <div className="text-5xl mb-4">📧</div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Email Summarizer
          </h1>
          <p className="text-gray-500 mb-8">
            Fetch your Gmail inbox and get AI-powered summaries in seconds.
          </p>
          <div className="flex gap-3 justify-center">
            <button
              onClick={() => loginWithRedirect()}
              className="px-5 py-2.5 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 transition-colors"
            >
              Log in
            </button>
            <button
              onClick={() =>
                loginWithRedirect({
                  authorizationParams: { screen_hint: "signup" },
                })
              }
              className="px-5 py-2.5 border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50 transition-colors"
            >
              Sign up
            </button>
          </div>
        </div>
      </div>
    );

  return (
    <div className="min-h-screen bg-gray-50">
      <Header user={user} onLogout={handleLogout} />
      <main className="max-w-2xl mx-auto px-4 py-8">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold text-gray-800">Your Inbox</h2>
          <span className="text-sm text-gray-400">{emails.length} emails</span>
        </div>
        <div className="flex flex-col gap-3">
          {emails.map((email) => (
            <EmailCard
              key={email.id}
              email={email}
              onSummarize={handleSummarize}
              getToken={getAccessTokenSilently}
            />
          ))}
        </div>
      </main>
    </div>
  );
}
