import { useEffect, useState, useRef, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useSelector, useDispatch } from "react-redux";
import Header from "../components/Header";
import {
  fetchEmailById,
  summarizeEmail,
  generateReply,
  sendReply,
  clearSelected,
  setReplyDraft,
  clearSendStatus,
} from "../store/emailSlice";

/* Sandboxed iframe wrapper for HTML emails — like Gmail does */
function HtmlEmailBody({ html }) {
  const iframeRef = useRef(null);

  const handleLoad = useCallback(() => {
    const iframe = iframeRef.current;
    if (!iframe) return;
    const doc = iframe.contentDocument || iframe.contentWindow.document;

    // Inject sandbox styles — smaller font, contained layout
    const style = doc.createElement("style");
    style.textContent = `
      html, body {
        margin: 0;
        padding: 0;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        font-size: 11px;
        line-height: 1.4;
        color: #1a1a1a;
        word-wrap: break-word;
        overflow-wrap: break-word;
        background: transparent;
      }
      img { max-width: 100%; height: auto; }
      a { color: #1a73e8; }
      table { max-width: 100%; }
      pre { white-space: pre-wrap; word-wrap: break-word; }
      p { margin: 0.4em 0; }
    `;
    doc.head.appendChild(style);
  }, []);

  return (
    <iframe
      ref={iframeRef}
      srcDoc={html}
      sandbox="allow-same-origin"
      onLoad={handleLoad}
      title="Email content"
      className="w-full border-0"
      style={{ height: "380px" }}
    />
  );
}

export default function EmailPage({ onLogout }) {
  const { id } = useParams();
  const navigate = useNavigate();
  const dispatch = useDispatch();

  const token = useSelector((s) => s.auth.token);
  const email = useSelector((s) => s.email.selected);
  const loading = useSelector((s) => s.email.detailLoading);
  const error = useSelector((s) => s.email.detailError);
  const summaryLoading = useSelector((s) => s.email.summaryLoading);
  const summaryError = useSelector((s) => s.email.summaryError);
  const summary = useSelector((s) => s.email.summaries[id]);
  const replyLoading = useSelector((s) => s.email.replyLoading);
  const replyError = useSelector((s) => s.email.replyError);
  const replyDraft = useSelector((s) => s.email.generatedReplies[id]) || "";
  const sendLoading = useSelector((s) => s.email.sendLoading);
  const sendError = useSelector((s) => s.email.sendError);
  const sendSuccess = useSelector((s) => s.email.sendSuccess);

  const [copied, setCopied] = useState(false);
  const [showDetails, setShowDetails] = useState(false);
  const [showReply, setShowReply] = useState(false);
  const [showBody, setShowBody] = useState(false);

  useEffect(() => {
    dispatch(fetchEmailById({ token, id }));
    dispatch(clearSendStatus());
    return () => {
      dispatch(clearSelected());
    };
  }, [dispatch, token, id]);

  const handleSummarize = () => {
    const bodyText = email?.body || email?.snippet || "";
    dispatch(summarizeEmail({ token, id, body: bodyText }));
  };

  const handleGenerateReply = () => {
    const bodyText = email?.body || email?.snippet || "";
    dispatch(
      generateReply({
        token,
        id,
        from: email?.from || "",
        subject: email?.subject || "",
        body: bodyText,
      })
    );
    setShowReply(true);
  };

  const handleSendReply = () => {
    if (!replyDraft.trim() || !email) return;
    dispatch(
      sendReply({
        token,
        id,
        threadId: email.thread_id || "",
        to: email.from || "",
        subject: email.subject || "",
        body: replyDraft,
        messageId: email.message_id || "",
      })
    );
  };

  const handleCopy = async () => {
    if (!summary) return;
    try {
      await navigator.clipboard.writeText(summary);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      /* ignore */
    }
  };

  const handleBack = () => {
    navigate("/inbox");
  };

  /* ---------- loading skeleton ---------- */
  if (loading || (!email && !error)) {
    return (
      <div className="min-h-screen bg-slate-50/50">
        <Header onLogout={onLogout} />
        <main className="max-w-3xl mx-auto px-4 py-8">
          <div className="animate-pulse">
            <div className="h-4 w-32 bg-gray-200 rounded mb-8" />
            <div className="bg-white border border-gray-100 rounded-2xl overflow-hidden shadow-[0_4px_24px_rgba(0,0,0,0.02)]">
              <div className="p-8 space-y-4">
                <div className="h-6 w-3/4 bg-gray-200 rounded" />
                <div className="h-4 w-1/2 bg-gray-200 rounded" />
              </div>
              <div className="border-t border-gray-100 p-8 space-y-4">
                <div className="h-4 w-full bg-gray-100 rounded" />
                <div className="h-4 w-full bg-gray-100 rounded" />
                <div className="h-4 w-full bg-gray-100 rounded" />
                <div className="h-4 w-2/3 bg-gray-100 rounded" />
              </div>
            </div>
          </div>
        </main>
      </div>
    );
  }

  /* ---------- error state ---------- */
  if (error) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header onLogout={onLogout} />
        <main className="max-w-3xl mx-auto px-4 py-4">
          <button
            onClick={handleBack}
            className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-indigo-600 mb-6 transition-colors"
          >
            &larr; Back to Inbox
          </button>
          <div className="bg-white border border-red-200 rounded-2xl p-8 text-center">
            <div className="w-12 h-12 mx-auto mb-3 rounded-full bg-red-50 flex items-center justify-center">
              <svg className="w-6 h-6 text-red-400" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <p className="text-red-600 text-sm font-medium">{error}</p>
            <button
              onClick={() => dispatch(fetchEmailById({ token, id }))}
              className="mt-4 text-sm px-5 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
            >
              Retry
            </button>
          </div>
        </main>
      </div>
    );
  }

  /* ---------- extract sender info ---------- */
  const senderName =
    email.from?.match(/^([^<]+)/)?.[1]?.trim() || email.from || "Unknown";
  const senderEmail =
    email.from?.match(/<([^>]+)>/)?.[1] || email.from || "";

  const hasHtml = !!email.body_html;

  return (
    <div className="min-h-screen bg-slate-50/50">
      <Header onLogout={onLogout} />
      <main className="max-w-3xl mx-auto px-4 py-8">
        {/* Back button */}
        <button
          onClick={handleBack}
          className="flex items-center gap-1.5 text-sm font-medium text-gray-500 hover:text-indigo-600 mb-6 transition-colors group"
        >
          <svg className="w-4 h-4 transition-transform group-hover:-translate-x-0.5" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
          </svg>
          Back to Inbox
        </button>

        {/* Email card — mail UI style */}
        <div className="bg-white border border-gray-100 rounded-2xl shadow-[0_4px_24px_rgba(0,0,0,0.02)] overflow-hidden">

          {/* Subject + sender header */}
          <div className="px-4 pt-4 pb-3">
            <h2 className="text-base font-semibold text-gray-900 leading-snug mb-3">
              {email.subject || "(No Subject)"}
            </h2>

            {/* Sender row */}
            <div className="flex items-start gap-2">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center text-white font-bold text-xs shrink-0 shadow-sm">
                {senderName.charAt(0).toUpperCase()}
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex items-baseline gap-1.5 flex-wrap">
                  <span className="text-xs font-semibold text-gray-900">
                    {senderName}
                  </span>
                  {senderEmail && senderEmail !== senderName && (
                    <span className="text-[10px] text-gray-400">
                      &lt;{senderEmail}&gt;
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-1.5 mt-0.5">
                  <span className="text-[10px] text-gray-400">to {email.to || "me"}</span>
                  <button
                    onClick={() => setShowDetails(!showDetails)}
                    className="text-gray-400 hover:text-gray-600 transition-colors"
                  >
                    <svg className={`w-3 h-3 transition-transform ${showDetails ? "rotate-180" : ""}`} fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>
                </div>

                {/* Expandable details */}
                {showDetails && (
                  <div className="mt-1.5 text-[10px] text-gray-500 space-y-0.5 bg-gray-50 rounded p-2">
                    <div><span className="text-gray-400 w-12 inline-block">From:</span> {email.from}</div>
                    <div><span className="text-gray-400 w-12 inline-block">To:</span> {email.to || "me"}</div>
                    {email.date && (
                      <div><span className="text-gray-400 w-12 inline-block">Date:</span> {email.date}</div>
                    )}
                  </div>
                )}
              </div>

              {/* Date on the right */}
              {email.date && (
                <span className="text-[10px] text-gray-400 whitespace-nowrap shrink-0 ml-1.5 mt-0.5">
                  {new Date(email.date).toLocaleDateString(undefined, {
                    month: "short",
                    day: "numeric",
                  })}
                </span>
              )}
            </div>

            {/* Labels */}
            {email.labels && email.labels.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-2">
                {email.labels.map((label) => (
                  <span
                    key={label}
                    className="text-[10px] px-1.5 py-0.5 rounded-full bg-gray-100 text-gray-500 font-medium"
                  >
                    {label}
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* Divider */}
          <div className="mx-4 border-t border-gray-100" />

          {/* Summarize section */}
          <div className="px-5 py-4">
            {!summary ? (
              <div className="flex items-center gap-3">
                <button
                  onClick={handleSummarize}
                  disabled={summaryLoading}
                  className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-indigo-500 to-violet-600 text-white text-sm font-medium rounded-xl hover:shadow-[0_4px_12px_rgba(79,70,229,0.3)] hover:-translate-y-0.5 disabled:opacity-50 active:scale-95 transition-all"
                >
                  {summaryLoading && (
                    <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  )}
                  {summaryLoading ? "Summarizing\u2026" : "\u2728 Summarize with AI"}
                </button>
                {summaryError && (
                  <p className="text-sm text-red-500">{summaryError}</p>
                )}
              </div>
            ) : (
              <div className="relative p-3.5 bg-gradient-to-br from-indigo-50 to-purple-50 border border-indigo-100 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="text-xs">\u2728</span>
                    <span className="text-[10px] font-bold text-indigo-600 uppercase tracking-wide">
                      AI Summary
                    </span>
                  </div>
                  <button
                    onClick={handleCopy}
                    className="text-[10px] text-indigo-400 hover:text-indigo-600 transition-colors flex items-center gap-1 px-1.5 py-0.5 rounded hover:bg-indigo-100/50"
                  >
                    {copied ? (
                      <>
                        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                        </svg>
                        Copied!
                      </>
                    ) : (
                      <>
                        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                          <rect x="9" y="9" width="13" height="13" rx="2" />
                          <path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1" />
                        </svg>
                        Copy
                      </>
                    )}
                  </button>
                </div>
                <p className="text-xs text-gray-800 leading-relaxed">
                  {summary}
                </p>
              </div>
            )}
          </div>

          {/* Divider */}
          <div className="mx-4 border-t border-gray-100" />

          {/* Body — toggleable visibility */}
          <div className="px-4 py-2">
            <button
              onClick={() => setShowBody(!showBody)}
              className="flex items-center gap-1.5 text-[10px] font-medium text-gray-500 hover:text-indigo-600 transition-colors group"
            >
              <svg
                className={`w-3 h-3 transition-transform ${showBody ? "rotate-90" : ""}`}
                fill="none"
                stroke="currentColor"
                strokeWidth={2}
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
              </svg>
              {showBody ? "Hide Email Content" : "Show Email Content"}
            </button>
          </div>

          {showBody && (
            <div className="px-4 pb-3 max-h-[380px] overflow-y-auto">
              {hasHtml ? (
                <HtmlEmailBody html={email.body_html} />
              ) : (
                <p className="text-[11px] text-gray-700 leading-relaxed whitespace-pre-wrap break-words">
                  {email.body || email.snippet || "No content available."}
                </p>
              )}
            </div>
          )}

          {/* Divider */}
          <div className="mx-4 border-t border-gray-100" />

          {/* Reply section */}
          <div className="px-5 py-4">
            {!showReply && !replyDraft ? (
              <button
                onClick={handleGenerateReply}
                disabled={replyLoading}
                className="flex items-center gap-2 px-5 py-2.5 border border-indigo-200 text-indigo-600 text-sm font-medium rounded-xl hover:bg-indigo-50 hover:border-indigo-300 disabled:opacity-50 active:scale-95 transition-all"
              >
                {replyLoading && (
                  <span className="w-4 h-4 border-2 border-indigo-400 border-t-transparent rounded-full animate-spin" />
                )}
                {replyLoading ? "Generating\u2026" : "\u21a9 Generate AI Reply"}
              </button>
            ) : (
              <div className="space-y-2.5">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-bold text-gray-500 uppercase tracking-wide">
                    Reply
                  </span>
                  {!replyDraft && !replyLoading && (
                    <button
                      onClick={handleGenerateReply}
                      className="text-[10px] text-indigo-500 hover:text-indigo-700 transition-colors"
                    >
                      Regenerate
                    </button>
                  )}
                </div>

                {replyLoading && !replyDraft ? (
                  <div className="animate-pulse space-y-2">
                    <div className="h-3 w-full bg-gray-100 rounded" />
                    <div className="h-3 w-full bg-gray-100 rounded" />
                    <div className="h-3 w-2/3 bg-gray-100 rounded" />
                  </div>
                ) : (
                  <textarea
                    value={replyDraft}
                    onChange={(e) =>
                      dispatch(setReplyDraft({ id, text: e.target.value }))
                    }
                    rows={5}
                    className="w-full border border-gray-200 rounded-lg px-3 py-2.5 text-xs text-gray-700 leading-relaxed focus:outline-none focus:ring-2 focus:ring-indigo-300 resize-y"
                    placeholder="Type your reply or generate one with AI\u2026"
                  />
                )}

                {replyError && (
                  <p className="text-[10px] text-red-500">{replyError}</p>
                )}

                <div className="flex items-center gap-3 mt-3">
                  <button
                    onClick={handleSendReply}
                    disabled={sendLoading || !replyDraft.trim() || sendSuccess}
                    className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-indigo-500 to-violet-600 text-white text-sm font-medium rounded-xl hover:shadow-[0_4px_12px_rgba(79,70,229,0.3)] hover:-translate-y-0.5 disabled:opacity-50 active:scale-95 transition-all shadow-sm"
                  >
                    {sendLoading && (
                      <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    )}
                    {sendLoading ? "Sending\u2026" : sendSuccess ? "\u2713 Sent" : "Send Reply"}
                  </button>
                  {!sendSuccess && !sendLoading && (
                    <button
                      onClick={() => {
                        setShowReply(false);
                        dispatch(clearSendStatus());
                      }}
                      className="text-xs text-gray-400 hover:text-gray-600 transition-colors"
                    >
                      Cancel
                    </button>
                  )}
                  {sendError && (
                    <p className="text-[10px] text-red-500">{sendError}</p>
                  )}
                </div>

                {sendSuccess && (
                  <div className="flex items-center gap-1.5 text-xs text-green-600 bg-green-50 px-3 py-2 rounded-lg">
                    <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                    </svg>
                    Reply sent successfully!
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
