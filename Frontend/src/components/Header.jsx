export default function Header({ user, onLogout }) {
  return (
    <header className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
      <h1 className="text-lg font-bold text-indigo-600">📧 Email Summarizer</h1>
      <div className="flex items-center gap-3">
        <img src={user.picture} alt={user.name} className="w-8 h-8 rounded-full" />
        <span className="text-sm text-gray-600 hidden sm:block">{user.email}</span>
        <button
          onClick={onLogout}
          className="text-sm px-3 py-1.5 rounded-lg border border-gray-300 text-gray-600 hover:bg-gray-50 transition-colors"
        >
          Logout
        </button>
      </div>
    </header>
  );
}
