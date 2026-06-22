import { useState, useEffect } from "react";
import Header from "../components/Header";
import EmailCard from "../components/EmailCard";

export default function InboxPage({ token, onLogout }) {
  const [emails, setEmails] = useState([]);

  useEffect(() => {
    const loadEmails = async () => {
      try {
        const response = await fetch("http://localhost:8000/api/emails", {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!response.ok) throw new Error(await response.text());
        const data = await response.json();
        setEmails(Array.isArray(data) ? data : []);
      } catch (err) {
        console.error("Failed to load emails:", err);
      }
    };
    loadEmails();
  }, [token]);

  const handleSummarize = (id, summary) =>
    setEmails((prev) => prev.map((e) => (e.id === id ? { ...e, summary } : e)));

  return (
    <div className="min-h-screen bg-gray-50">
      <Header onLogout={onLogout} />
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
              getToken={() => token}
            />
          ))}
        </div>
      </main>
    </div>
  );
}
