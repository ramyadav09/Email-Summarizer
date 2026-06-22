import { useSelector } from "react-redux";
import { Navigate } from "react-router-dom";

export default function LoginPage() {
  const token = useSelector((s) => s.auth.token);

  if (token) return <Navigate to="/inbox" replace />;

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50 flex items-center justify-center px-4">
      <div className="bg-white rounded-2xl shadow-xl p-10 max-w-md w-full text-center border border-gray-100">
        <div className="w-16 h-16 bg-indigo-100 rounded-2xl flex items-center justify-center mx-auto mb-6">
          <span className="text-3xl">📧</span>
        </div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Email Summarizer</h1>
        <p className="text-gray-500 mb-8 text-sm leading-relaxed">
          Connect your Gmail account and get AI-powered summaries of your emails in seconds.
        </p>
        <a
          href="http://localhost:8000/auth/login"
          className="flex items-center justify-center gap-3 w-full px-5 py-3 bg-indigo-600 text-white rounded-xl font-medium hover:bg-indigo-700 active:scale-95 transition-all"
        >
          <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
            <path d="M20 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z"/>
          </svg>
          Connect Gmail
        </a>
        <p className="text-xs text-gray-400 mt-4">We only read your emails. We never send or delete.</p>
      </div>
    </div>
  );
}
