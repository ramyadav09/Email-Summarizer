export default function Header({ onLogout }) {
  return (
    <header className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
      <h1 className="text-lg font-bold text-indigo-600">📧 Email Summarizer</h1>
      <button
        onClick={onLogout}
        className="text-sm px-3 py-1.5 rounded-lg border border-gray-300 text-gray-600 hover:bg-gray-50 transition-colors"
      >
        Logout
      </button>
    </header>
  );
}
