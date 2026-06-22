import { useState } from "react";

export default function EmailCard({ email, onSummarize, getToken }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSummarize = async () => {
    setLoading(true);
    setError(null);
    try {
      const token = await getToken();
      const res = await fetch("http://localhost:8000/api/summarize", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ id: email.id }),
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      onSummarize(email.id, data.summary);
    } catch {
      setError("Failed to summarize. Try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0 flex-1">
          <p className="text-xs text-gray-400 mb-0.5 truncate">{email.from}</p>
          <h3 className="font-semibold text-gray-800 truncate">{email.subject}</h3>
          <p className="text-sm text-gray-500 mt-1 line-clamp-2">{email.snippet}</p>
        </div>
        {!email.summary && (
          <button
            onClick={handleSummarize}
            disabled={loading}
            className="shrink-0 text-sm px-3 py-1.5 rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed active:scale-95 transition-all flex items-center gap-1.5"
          >
            {loading && <span className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />}
            {loading ? "Summarizing…" : "Summarize"}
          </button>
        )}
      </div>
      {email.summary && (
        <div className="mt-3 p-3 bg-indigo-50 border border-indigo-100 rounded-lg text-sm text-indigo-800 leading-relaxed">
          <span className="font-medium text-indigo-600 text-xs uppercase tracking-wide block mb-1">Summary</span>
          {email.summary}
        </div>
      )}
      {error && <p className="mt-2 text-xs text-red-500">{error}</p>}
    </div>
  );
}
