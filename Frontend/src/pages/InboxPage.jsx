import { useState } from "react";
import { useAuth0 } from "@auth0/auth0-react";
import Header from "../components/Header";
import EmailCard from "../components/EmailCard";
import MOCK_EMAILS from "../data/mockEmails";

export default function InboxPage() {
  const { user, logout, getAccessTokenSilently } = useAuth0();
  const [emails, setEmails] = useState(MOCK_EMAILS);

  const handleSummarize = (id, summary) =>
    setEmails((prev) => prev.map((e) => (e.id === id ? { ...e, summary } : e)));

  const handleLogout = () =>
    logout({ logoutParams: { returnTo: window.location.origin } });

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
