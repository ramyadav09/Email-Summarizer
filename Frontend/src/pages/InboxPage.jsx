import { useEffect, useState } from "react";
import { useSelector, useDispatch } from "react-redux";
import { useNavigate } from "react-router-dom";
import Header from "../components/Header";
import EmailCard from "../components/EmailCard";
import { fetchCurrentUser } from "../store/authSlice";
import {
  fetchEmails,
  syncEmails,
  clearError,
} from "../store/emailSlice";

const API = "http://localhost:8000";

export default function InboxPage({ onLogout }) {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { token, user } = useSelector((s) => s.auth);
  const {
    list: emails,
    loading,
    loaded,
    error,
    googleNotLinked,
    syncLoading,
    syncError,
    page = 1,
    totalPages = 1,
    total = 0,
  } = useSelector((s) => s.email);

  const [showNoNewEmails, setShowNoNewEmails] = useState(false);

  // Derive if google is linked based on the user profile or the redux state
  const isNotLinked = googleNotLinked || !user?.is_google_linked;

  /* Fetch emails and user profile on mount */
  useEffect(() => {
    if (token) {
      if (!loaded) {
        dispatch(fetchEmails({ token, page: 1, limit: 20 }));
      }
      dispatch(fetchCurrentUser(token));
    }
  }, [token, loaded, dispatch]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleSyncFromGoogle = async () => {
    dispatch(clearError());
    setShowNoNewEmails(false);
    const resultAction = await dispatch(syncEmails({ token, page: 1, limit: 20 }));
    if (syncEmails.fulfilled.match(resultAction)) {
      const count = resultAction.payload?.new_emails_count ?? 0;
      if (count === 0 && loaded) {
        setShowNoNewEmails(true);
        setTimeout(() => {
          setShowNoNewEmails(false);
        }, 4000);
      }
    }
  };

  const handleConnectGoogle = () => {
    window.location.href = `${API}/auth/google?token=${token}`;
  };

  const handleView = (email) => {
    navigate(`/email/${email.id}`);
  };

  return (
    <div className="min-h-screen bg-slate-50/50">
      <Header onLogout={onLogout} />
      <main className="max-w-2xl mx-auto px-4 py-8">

        {/* Actions Bar */}
        <div className="bg-white/80 backdrop-blur-sm border border-gray-100 rounded-2xl p-5 mb-8 shadow-[0_4px_16px_rgba(0,0,0,0.02)]">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-semibold text-gray-800">
                {loaded ? `${total} email${total !== 1 ? "s" : ""}` : "Your Inbox"}
              </p>
              <p className="text-xs text-gray-400">
                {loaded ? `Showing page ${page} of ${totalPages}` : "Loading your inbox…"}
              </p>
            </div>
            {isNotLinked ? (
              <button
                onClick={handleConnectGoogle}
                className="px-5 py-2.5 bg-gradient-to-r from-indigo-500 to-violet-600 text-white text-sm font-medium rounded-xl hover:shadow-[0_4px_12px_rgba(79,70,229,0.3)] hover:-translate-y-0.5 active:scale-95 transition-all flex items-center gap-2 whitespace-nowrap"
              >
                <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M20 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z" />
                </svg>
                Connect Gmail Account
              </button>
            ) : (
              <button
                onClick={handleSyncFromGoogle}
                disabled={syncLoading}
                className="px-5 py-2.5 bg-white text-gray-700 text-sm font-medium rounded-xl border border-gray-200 hover:bg-gray-50 hover:text-indigo-600 disabled:opacity-60 active:scale-95 transition-all flex items-center gap-2 whitespace-nowrap shadow-sm"
              >
                {syncLoading && (
                  <span className="w-3.5 h-3.5 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin" />
                )}
                {!syncLoading && (
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                )}
                {syncLoading ? "Refreshing…" : "Refresh"}
              </button>
            )}
          </div>
          {(error || syncError) && (
            <p className="text-red-500 text-xs mt-3">{error || syncError}</p>
          )}
        </div>

        {/* Transient "No New Emails" Toast */}
        {showNoNewEmails && (
          <div className="fixed bottom-8 left-1/2 -translate-x-1/2 z-50 bg-gray-900 text-white text-sm rounded-full px-6 py-3 shadow-2xl flex items-center gap-2 font-medium animate-bounce">
            <span>✨</span> No new emails found. Your inbox is up-to-date!
          </div>
        )}

        {/* Email list */}
        {!loaded && (syncLoading || loading) ? (
          <div className="flex flex-col items-center justify-center py-16 gap-3 text-gray-400">
            <span className="w-8 h-8 border-3 border-indigo-300 border-t-transparent rounded-full animate-spin" />
            <p className="text-sm">Loading emails…</p>
          </div>
        ) : emails.length === 0 && loaded ? (
          <div className="flex flex-col items-center justify-center py-16 gap-3 text-gray-400">
            <span className="text-4xl">🔍</span>
            <p className="text-sm">No emails found. Try refreshing.</p>
          </div>
        ) : (
          <>
            <div className="flex flex-col gap-3">
              {emails.map((email) => (
                <EmailCard key={email.id} email={email} onView={handleView} />
              ))}
            </div>

            {/* Pagination Controls */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between bg-white/80 backdrop-blur-sm border border-gray-100 rounded-2xl p-4 mt-8 shadow-[0_2px_8px_rgba(0,0,0,0.02)]">
                <button
                  disabled={page <= 1 || syncLoading}
                  onClick={() => dispatch(fetchEmails({ token, page: page - 1, limit: 20 }))}
                  className="px-4 py-2 bg-white border border-gray-200 text-gray-700 text-sm rounded-xl hover:bg-gray-50 disabled:opacity-50 disabled:hover:bg-white active:scale-95 transition-all font-medium flex items-center gap-1.5 shadow-sm"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
                  </svg>
                  Previous
                </button>
                <span className="text-sm font-medium text-gray-500">
                  Page {page} of {totalPages}
                </span>
                <button
                  disabled={page >= totalPages || syncLoading}
                  onClick={() => dispatch(fetchEmails({ token, page: page + 1, limit: 20 }))}
                  className="px-4 py-2 bg-white border border-gray-200 text-gray-700 text-sm rounded-xl hover:bg-gray-50 disabled:opacity-50 disabled:hover:bg-white active:scale-95 transition-all font-medium flex items-center gap-1.5 shadow-sm"
                >
                  Next
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                  </svg>
                </button>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}
