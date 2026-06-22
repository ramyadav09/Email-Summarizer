import { Link, useLocation } from "react-router-dom";

export default function Header({ onLogout }) {
  const { pathname } = useLocation();

  return (
    <header className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between sticky top-0 z-10 shadow-sm">
      <div className="flex items-center gap-4">
        <Link to="/inbox" className="flex items-center gap-2 hover:opacity-80 transition-opacity">
          <span className="text-xl">📧</span>
          <h1 className="text-base font-bold text-indigo-600 tracking-tight">
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
        className="text-sm px-4 py-1.5 rounded-lg border border-gray-200 text-gray-600 hover:bg-red-50 hover:text-red-600 hover:border-red-200 transition-colors"
      >
        Logout
      </button>
    </header>
  );
}
