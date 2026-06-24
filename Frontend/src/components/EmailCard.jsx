export default function EmailCard({ email, onView }) {
  const isRead = email.is_read ?? true;

  return (
    <div
      className={`group bg-white border rounded-2xl p-4 shadow-[0_2px_8px_rgba(0,0,0,0.04)] hover:shadow-[0_8px_24px_rgba(0,0,0,0.08)] hover:-translate-y-[2px] transition-all duration-300 ${
        isRead ? "border-gray-100" : "border-indigo-100 bg-indigo-50/20"
      }`}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-2.5 min-w-0 flex-1">
          {/* Unread dot */}
          {!isRead && (
            <span className="mt-1.5 w-2 h-2 rounded-full bg-indigo-500 shrink-0" title="Unread" />
          )}
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2 mb-0.5">
              <p
                className={`text-xs truncate ${
                  isRead ? "text-gray-400" : "text-gray-700 font-semibold"
                }`}
              >
                {email.from}
              </p>
              <span
                className={`shrink-0 text-[10px] font-medium px-1.5 py-0.5 rounded-full ${
                  isRead
                    ? "bg-gray-100 text-gray-400"
                    : "bg-indigo-100 text-indigo-600"
                }`}
              >
                {isRead ? "Read" : "Unread"}
              </span>
            </div>
            <h3
              className={`truncate ${
                isRead
                  ? "font-semibold text-gray-800"
                  : "font-bold text-gray-900"
              }`}
            >
              {email.subject}
            </h3>
            <p
              className={`text-sm mt-0.5 truncate ${
                isRead ? "text-gray-500" : "text-gray-600"
              }`}
            >
              {email.snippet}
            </p>
          </div>
        </div>
        <button
          onClick={() => onView(email)}
          className="opacity-0 group-hover:opacity-100 shrink-0 text-sm font-medium px-4 py-2 rounded-xl border border-indigo-100 text-indigo-600 hover:bg-indigo-600 hover:text-white active:scale-95 transition-all shadow-sm"
        >
          View
        </button>
      </div>
    </div>
  );
}
