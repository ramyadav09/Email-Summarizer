import { useState } from "react";

export default function EmailCard({ email, onSummarize, getToken }) {
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
    onSummarize(email.id, "AI-generated summary will appear here once the backend is connected.");
    setLoading(false);
  };

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <p className="text-xs text-gray-400 mb-0.5">{email.from}</p>
          <h3 className="font-semibold text-gray-800 truncate">{email.subject}</h3>
          <p className="text-sm text-gray-500 mt-1 line-clamp-2">{email.snippet}</p>
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
