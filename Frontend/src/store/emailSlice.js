import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";

/* ---------- helpers ---------- */
const API = "http://localhost:8000";

/* ---------- async thunks ---------- */
export const fetchEmails = createAsyncThunk(
  "email/fetchEmails",
  async ({ token, page = 1, limit = 10 }, { rejectWithValue }) => {
    try {
      const res = await fetch(`${API}/api/emails?page=${page}&limit=${limit}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        if (res.status === 403) return rejectWithValue({ status: 403, detail: data.detail || "Google account not linked" });
        throw new Error(data.detail || await res.text());
      }
      return await res.json();
    } catch (err) {
      return rejectWithValue(err.message);
    }
  }
);

export const syncEmails = createAsyncThunk(
  "email/syncEmails",
  async ({ token, page = 1, limit = 10 }, { rejectWithValue }) => {
    try {
      const res = await fetch(`${API}/api/emails/sync?page=${page}&limit=${limit}`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        if (res.status === 403) return rejectWithValue({ status: 403, detail: data.detail || "Google account not linked" });
        throw new Error(data.detail || "Sync failed");
      }
      return await res.json();
    } catch (err) {
      return rejectWithValue(err.message);
    }
  }
);

export const fetchEmailById = createAsyncThunk(
  "email/fetchEmailById",
  async ({ token, id }, { rejectWithValue }) => {
    try {
      const res = await fetch(`${API}/api/emails/${id}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error(await res.text());
      return await res.json();
    } catch (err) {
      return rejectWithValue(err.message);
    }
  }
);

export const summarizeEmail = createAsyncThunk(
  "email/summarize",
  async ({ token, id, body }, { rejectWithValue }) => {
    try {
      const res = await fetch(`${API}/api/summarize`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ id, body: body || undefined }),
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      return { id, summary: data.summary };
    } catch (err) {
      return rejectWithValue(err.message);
    }
  }
);

export const generateReply = createAsyncThunk(
  "email/generateReply",
  async ({ token, id, from, subject, body }, { rejectWithValue }) => {
    try {
      const res = await fetch(`${API}/api/generate-response`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          id,
          from_addr: from || undefined,
          subject: subject || undefined,
          body: body || undefined,
        }),
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      return { id, reply: data.reply };
    } catch (err) {
      return rejectWithValue(err.message);
    }
  }
);

export const sendReply = createAsyncThunk(
  "email/sendReply",
  async ({ token, id, threadId, to, subject, body, messageId }, { rejectWithValue }) => {
    try {
      const res = await fetch(`${API}/api/send-reply`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          id,
          thread_id: threadId,
          to,
          subject,
          body,
          message_id: messageId || "",
        }),
      });
      if (!res.ok) throw new Error(await res.text());
      return await res.json();
    } catch (err) {
      return rejectWithValue(err.message);
    }
  }
);

/* ---------- slice ---------- */
const emailSlice = createSlice({
  name: "email",
  initialState: {
    list: [],
    page: 1,
    limit: 20,
    total: 0,
    totalPages: 0,
    selected: null,
    summaries: {},
    generatedReplies: {},
    googleNotLinked: false,
    syncLoading: false,
    syncError: null,
    loading: false,
    detailLoading: false,
    summaryLoading: false,
    replyLoading: false,
    sendLoading: false,
    loaded: false,
    error: null,
    detailError: null,
    summaryError: null,
    replyError: null,
    sendError: null,
    sendSuccess: false,
  },
  reducers: {
    setGoogleNotLinked(state, action) {
      state.googleNotLinked = action.payload;
    },
    clearSelected(state) {
      state.selected = null;
      state.detailError = null;
      state.replyError = null;
      state.sendError = null;
      state.sendSuccess = false;
    },
    setReplyDraft(state, action) {
      const { id, text } = action.payload;
      state.generatedReplies[id] = text;
    },
    clearSendStatus(state) {
      state.sendError = null;
      state.sendSuccess = false;
    },
    clearError(state) {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    /* fetch emails from DB */
    builder
      .addCase(fetchEmails.pending, (state) => {
        state.loading = true;
        state.error = null;
        state.googleNotLinked = false;
      })
      .addCase(fetchEmails.fulfilled, (state, action) => {
        state.loading = false;
        if (action.payload && typeof action.payload === 'object' && !Array.isArray(action.payload)) {
          state.list = Array.isArray(action.payload.emails) ? action.payload.emails : [];
          state.total = action.payload.total || 0;
          state.page = action.payload.page || 1;
          state.limit = action.payload.limit || 10;
          state.totalPages = action.payload.total_pages || 0;
        } else {
          state.list = Array.isArray(action.payload) ? action.payload : [];
          state.total = state.list.length;
          state.page = 1;
          state.totalPages = 1;
        }
        state.loaded = true;
      })
      .addCase(fetchEmails.rejected, (state, action) => {
        state.loading = false;
        if (action.payload?.status === 403) {
          state.googleNotLinked = true;
        }
        state.error = typeof action.payload === 'string' ? action.payload : action.payload?.detail || "Failed to load emails.";
        state.loaded = true;
      });

    /* sync emails from Google */
    builder
      .addCase(syncEmails.pending, (state) => {
        state.syncLoading = true;
        state.syncError = null;
        state.googleNotLinked = false;
      })
      .addCase(syncEmails.fulfilled, (state, action) => {
        state.syncLoading = false;
        if (action.payload && typeof action.payload === 'object' && !Array.isArray(action.payload)) {
          // Only overwrite the email list and pagination state if new emails were fetched.
          // Otherwise, we keep the previous fetched emails visible on the page.
          if (action.payload.new_emails_count === undefined || action.payload.new_emails_count > 0) {
            state.list = Array.isArray(action.payload.emails) ? action.payload.emails : [];
            state.total = action.payload.total || 0;
            state.page = action.payload.page || 1;
            state.limit = action.payload.limit || 10;
            state.totalPages = action.payload.total_pages || 0;
          }
        } else {
          state.list = Array.isArray(action.payload) ? action.payload : [];
          state.total = state.list.length;
          state.page = 1;
          state.totalPages = 1;
        }
        state.loaded = true;
      })
      .addCase(syncEmails.rejected, (state, action) => {
        state.syncLoading = false;
        if (action.payload?.status === 403) {
          state.googleNotLinked = true;
        }
        state.syncError = typeof action.payload === 'string' ? action.payload : action.payload?.detail || "Sync failed.";
      });

    /* fetch single email */
    builder
      .addCase(fetchEmailById.pending, (state) => {
        state.detailLoading = true;
        state.detailError = null;
        state.selected = null;
      })
      .addCase(fetchEmailById.fulfilled, (state, action) => {
        state.detailLoading = false;
        state.selected = action.payload;
        // Mark the email as read in the inbox list
        const idx = state.list.findIndex((e) => e.id === action.payload.id);
        if (idx !== -1) {
          state.list[idx].is_read = true;
        }
      })
      .addCase(fetchEmailById.rejected, (state, action) => {
        state.detailLoading = false;
        state.detailError = action.payload || "Failed to load email.";
      });

    /* summarize */
    builder
      .addCase(summarizeEmail.pending, (state) => {
        state.summaryLoading = true;
        state.summaryError = null;
      })
      .addCase(summarizeEmail.fulfilled, (state, action) => {
        state.summaryLoading = false;
        state.summaries[action.payload.id] = action.payload.summary;
      })
      .addCase(summarizeEmail.rejected, (state, action) => {
        state.summaryLoading = false;
        state.summaryError = action.payload || "Failed to summarize.";
      });

    /* generate reply */
    builder
      .addCase(generateReply.pending, (state) => {
        state.replyLoading = true;
        state.replyError = null;
      })
      .addCase(generateReply.fulfilled, (state, action) => {
        state.replyLoading = false;
        state.generatedReplies[action.payload.id] = action.payload.reply;
      })
      .addCase(generateReply.rejected, (state, action) => {
        state.replyLoading = false;
        state.replyError = action.payload || "Failed to generate reply.";
      });

    /* send reply */
    builder
      .addCase(sendReply.pending, (state) => {
        state.sendLoading = true;
        state.sendError = null;
        state.sendSuccess = false;
      })
      .addCase(sendReply.fulfilled, (state) => {
        state.sendLoading = false;
        state.sendSuccess = true;
      })
      .addCase(sendReply.rejected, (state, action) => {
        state.sendLoading = false;
        state.sendError = action.payload || "Failed to send reply.";
      });
  },
});

export const { setGoogleNotLinked, clearSelected, clearError, setReplyDraft, clearSendStatus } = emailSlice.actions;
export default emailSlice.reducer;
