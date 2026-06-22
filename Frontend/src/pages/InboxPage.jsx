import { useState } from "react";
import Header from "../components/Header";
import EmailCard from "../components/EmailCard";

const today = new Date().toISOString().split("T")[0];
const thirtyDaysAgo = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000)
  .toISOString()
  .split("T")[0];

export default function InboxPage({ token, onLogout }) {
  const [emails, setEmails] = useState([]);
  const [loaded, setLoaded] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [after, setAfter] = useState(thirtyDaysAgo);
  const [before, setBefore] = useState(today);
  const [readStatus, setReadStatus] = useState("");

  const toGmailDate = (dateStr) => dateStr.replace(/-/g, "/");

  const loadEmails = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (after) params.set("after", toGmailDate(after));
      if (before) params.set("before", toGmailDate(before));
      if (readStatus) params.set("read_status", readStatus);
      const res = await fetch(
        `http://localhost:8000/api/emails?${params.toString()}`,
        { headers: { Authorization: `Bearer ${token}` } },
      );
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      setEmails(Array.isArray(data) ? data : []);
      setLoaded(true);
    } catch {
      setError("Failed to load emails. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleSummarize = (id, summary) =>
    setEmails((prev) => prev.map((e) => (e.id === id ? { ...e, summary } : e)));

  return (
    <div className="min-h-screen bg-gray-50">
      <Header onLogout={onLogout} />
      <main className="max-w-2xl mx-auto px-4 py-8">

        {/* Date filter */}
        <div className="bg-white border border-gray-200 rounded-xl p-4 mb-6 shadow-sm">
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-3">Filters</p>
          <div className="flex flex-col sm:flex-row gap-3 items-end">
            <div className="flex-1">
              <label className="text-xs text-gray-500 mb-1 block">From</label>
              <input
                type="date"
                value={after}
                max={before}
                onChange={(e) => setAfter(e.target.value)}
                className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-indigo-300"
              />
            </div>
            <div className="flex-1">
              <label className="text-xs text-gray-500 mb-1 block">To</label>
              <input
                type="date"
                value={before}
                min={after}
                max={today}
                onChange={(e) => setBefore(e.target.value)}
                className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-indigo-300"
              />
            </div>
            <div className="flex-1">
              <label className="text-xs text-gray-500 mb-1 block">Status</label>
              <select
                value={readStatus}
                onChange={(e) => setReadStatus(e.target.value)}
                className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-indigo-300 bg-white"
              >
                <option value="">All</option>
                <option value="read">Read</option>
                <option value="unread">Unread</option>
              </select>
            </div>
            <button
              onClick={loadEmails}
              disabled={loading}
              className="px-5 py-2 bg-indigo-600 text-white text-sm rounded-lg hover:bg-indigo-700 disabled:opacity-60 active:scale-95 transition-all flex items-center gap-2 whitespace-nowrap"
            >
              {loading && (
                <span className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
              )}
              {loading ? "Loading…" : loaded ? "Refresh" : "Fetch Emails"}
            </button>
          </div>
          {error && <p className="text-red-500 text-xs mt-3">{error}</p>}
        </div>

        {/* Email list */}
        {!loaded ? (
          <div className="flex flex-col items-center justify-center py-16 gap-3 text-gray-400">
            <span className="text-4xl">📬</span>
            <p className="text-sm">Select a date range and fetch your emails</p>
          </div>
        ) : emails.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 gap-3 text-gray-400">
            <span className="text-4xl">🔍</span>
            <p className="text-sm">No emails found for this date range</p>
          </div>
        ) : (
          <>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-base font-semibold text-gray-700">
                {emails.length} email{emails.length !== 1 ? "s" : ""} found
              </h2>
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
          </>
        )}
      </main>
    </div>
  );
}
