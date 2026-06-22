import { useSelector, useDispatch } from "react-redux";
import { useNavigate } from "react-router-dom";
import Header from "../components/Header";
import EmailCard from "../components/EmailCard";
import {
  fetchEmails,
  setFilter,
  clearError,
} from "../store/emailSlice";

export default function InboxPage({ onLogout }) {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const token = useSelector((s) => s.auth.token);
  const { list: emails, filters, loading, loaded, error } = useSelector(
    (s) => s.email
  );

  const today = new Date().toISOString().split("T")[0];

  const handleLoadEmails = () => {
    dispatch(clearError());
    dispatch(
      fetchEmails({
        token,
        after: filters.after,
        before: filters.before,
        readStatus: filters.readStatus,
      })
    );
  };

  const handleView = (email) => {
    navigate(`/email/${email.id}`);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header onLogout={onLogout} />
      <main className="max-w-2xl mx-auto px-4 py-8">
        {/* Date filter */}
        <div className="bg-white border border-gray-200 rounded-xl p-4 mb-6 shadow-sm">
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-3">
            Filters
          </p>
          <div className="flex flex-col sm:flex-row gap-3 items-end">
            <div className="flex-1">
              <label className="text-xs text-gray-500 mb-1 block">From</label>
              <input
                type="date"
                value={filters.after}
                max={filters.before}
                onChange={(e) =>
                  dispatch(setFilter({ key: "after", value: e.target.value }))
                }
                className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-indigo-300"
              />
            </div>
            <div className="flex-1">
              <label className="text-xs text-gray-500 mb-1 block">To</label>
              <input
                type="date"
                value={filters.before}
                min={filters.after}
                max={today}
                onChange={(e) =>
                  dispatch(setFilter({ key: "before", value: e.target.value }))
                }
                className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-indigo-300"
              />
            </div>
            <div className="flex-1">
              <label className="text-xs text-gray-500 mb-1 block">Status</label>
              <select
                value={filters.readStatus}
                onChange={(e) =>
                  dispatch(
                    setFilter({ key: "readStatus", value: e.target.value })
                  )
                }
                className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-indigo-300 bg-white"
              >
                <option value="">All</option>
                <option value="read">Read</option>
                <option value="unread">Unread</option>
              </select>
            </div>
            <button
              onClick={handleLoadEmails}
              disabled={loading}
              className="px-5 py-2 bg-indigo-600 text-white text-sm rounded-lg hover:bg-indigo-700 disabled:opacity-60 active:scale-95 transition-all flex items-center gap-2 whitespace-nowrap"
            >
              {loading && (
                <span className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
              )}
              {loading ? "Loading\u2026" : loaded ? "Refresh" : "Fetch Emails"}
            </button>
          </div>
          {error && (
            <p className="text-red-500 text-xs mt-3">{error}</p>
          )}
        </div>

        {/* Email list */}
        {!loaded ? (
          <div className="flex flex-col items-center justify-center py-16 gap-3 text-gray-400">
            <span className="text-4xl">📬</span>
            <p className="text-sm">
              Select a date range and fetch your emails
            </p>
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
                <EmailCard key={email.id} email={email} onView={handleView} />
              ))}
            </div>
          </>
        )}
      </main>
    </div>
  );
}
