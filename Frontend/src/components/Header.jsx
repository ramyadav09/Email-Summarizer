import { Link, useLocation } from "react-router-dom";

export default function Header({ onLogout }) {
  const { pathname } = useLocation();

  return (
    <header className="bg-white/70 backdrop-blur-md border-b border-gray-200/50 px-6 py-4 flex items-center justify-between sticky top-0 z-10 shadow-[0_1px_3px_rgba(0,0,0,0.02)]">
      <div className="flex items-center gap-4">
        <Link to="/inbox" className="flex items-center gap-2.5 hover:opacity-80 transition-opacity">
          <span className="text-2xl drop-shadow-sm">📧</span>
          <h1 className="font-heading text-lg font-bold bg-gradient-to-r from-indigo-600 to-violet-600 bg-clip-text text-transparent tracking-tight">
            Email Summarizer
          </h1>
        </Link>
        {pathname !== "/inbox" && (
          <Link
            to="/inbox"
            className="text-sm text-gray-500 hover:text-indigo-600 transition-colors hidden sm:block"
          >
            Inbox
          </Link>
        )}
      </div>
      <button
        onClick={onLogout}
        className="text-sm font-medium px-4 py-2 rounded-xl border border-gray-200/80 text-gray-600 hover:bg-gray-50 hover:text-gray-900 active:scale-95 transition-all shadow-sm"
      >
        Logout
      </button>
    </header>
  );
}
