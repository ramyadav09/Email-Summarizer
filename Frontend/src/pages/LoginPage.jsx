import { useState } from "react";
import { useSelector, useDispatch } from "react-redux";
import { Navigate, Link } from "react-router-dom";
import { loginUser, clearAuthError } from "../store/authSlice";

export default function LoginPage() {
  const dispatch = useDispatch();
  const { token, loading, error } = useSelector((s) => s.auth);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  if (token) return <Navigate to="/inbox" replace />;

  const handleSubmit = (e) => {
    e.preventDefault();
    dispatch(clearAuthError());
    dispatch(loginUser({ email, password }));
  };

  return (
    <div className="min-h-screen bg-slate-50/50 flex items-center justify-center px-4">
      <div className="bg-white/80 backdrop-blur-md rounded-[24px] shadow-[0_8px_32px_rgba(0,0,0,0.04)] p-10 max-w-md w-full text-center border border-gray-100">
        <div className="w-16 h-16 bg-gradient-to-br from-indigo-100 to-violet-100 rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-inner">
          <span className="text-3xl drop-shadow-sm">📧</span>
        </div>
        <h1 className="font-heading text-3xl font-bold bg-gradient-to-r from-indigo-600 to-violet-600 bg-clip-text text-transparent mb-2">Welcome Back</h1>
        <p className="text-gray-500 mb-6 text-sm leading-relaxed">
          Sign in to your Email Summarizer account
        </p>

        {error && (
          <div className="bg-red-50 text-red-600 border border-red-200 rounded-lg px-4 py-2 text-sm mb-4">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4 text-left">
          <div>
            <label className="text-xs font-medium text-gray-500 mb-1 block uppercase tracking-wide">Email</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full border border-gray-200 rounded-lg px-3 py-2.5 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-indigo-300"
              placeholder="you@example.com"
            />
          </div>
          <div>
            <label className="text-xs font-medium text-gray-500 mb-1 block uppercase tracking-wide">Password</label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full border border-gray-200 rounded-lg px-3 py-2.5 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-indigo-300"
              placeholder="••••••••"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full px-5 py-3.5 bg-gradient-to-r from-indigo-500 to-violet-600 text-white rounded-xl font-medium hover:shadow-[0_4px_12px_rgba(79,70,229,0.3)] hover:-translate-y-0.5 active:scale-95 transition-all disabled:opacity-60 flex items-center justify-center gap-2"
          >
            {loading && (
              <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
            )}
            {loading ? "Signing in…" : "Sign In"}
          </button>
        </form>

        <p className="text-sm text-gray-500 mt-6">
          Don't have an account?{" "}
          <Link to="/register" className="text-indigo-600 font-medium hover:underline">
            Create one
          </Link>
        </p>
      </div>
    </div>
  );
}
