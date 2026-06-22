export default function EmailCard({ email, onView }) {
  return (
    <div className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0 flex-1">
          <p className="text-xs text-gray-400 mb-0.5 truncate">{email.from}</p>
          <h3 className="font-semibold text-gray-800 truncate">{email.subject}</h3>
          <p className="text-sm text-gray-500 mt-1 line-clamp-2">{email.snippet}</p>
        </div>
        <button
          onClick={() => onView(email)}
          className="shrink-0 text-sm px-3 py-1.5 rounded-lg border border-indigo-200 text-indigo-600 hover:bg-indigo-50 active:scale-95 transition-all"
        >
          View
        </button>
      </div>
    </div>
  );
}
