export default function EmailCard({ email, onView }) {
  const isRead = email.is_read ?? true;

  return (
    <div
      className={`bg-white border rounded-xl p-4 shadow-sm hover:shadow-md transition-shadow ${
        isRead ? "border-gray-200" : "border-indigo-200 bg-indigo-50/30"
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
              className={`text-sm mt-1 line-clamp-2 ${
                isRead ? "text-gray-500" : "text-gray-600"
              }`}
            >
              {email.snippet}
            </p>
          </div>
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
