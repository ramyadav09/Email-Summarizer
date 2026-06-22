import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";

/* ---------- helpers ---------- */
const API = "http://localhost:8000";

/* ---------- async thunks ---------- */
export const fetchEmails = createAsyncThunk(
  "email/fetchEmails",
  async ({ token, after, before, readStatus }, { rejectWithValue }) => {
    try {
      const params = new URLSearchParams();
      if (after) params.set("after", after.replace(/-/g, "/"));
      if (before) params.set("before", before.replace(/-/g, "/"));
      if (readStatus) params.set("read_status", readStatus);

      const res = await fetch(`${API}/api/emails?${params.toString()}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error(await res.text());
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
  async ({ token, id }, { rejectWithValue }) => {
    try {
      const res = await fetch(`${API}/api/summarize`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ id }),
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      return { id, summary: data.summary };
    } catch (err) {
      return rejectWithValue(err.message);
    }
  }
);

/* ---------- slice ---------- */
const today = new Date().toISOString().split("T")[0];
const thirtyDaysAgo = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000)
  .toISOString()
  .split("T")[0];

const emailSlice = createSlice({
  name: "email",
  initialState: {
    list: [],
    selected: null,
    summaries: {},
    filters: {
      after: thirtyDaysAgo,
      before: today,
      readStatus: "",
    },
    loading: false,
    detailLoading: false,
    summaryLoading: false,
    loaded: false,
    error: null,
    detailError: null,
    summaryError: null,
  },
  reducers: {
    setFilter(state, action) {
      const { key, value } = action.payload;
      state.filters[key] = value;
    },
    clearSelected(state) {
      state.selected = null;
      state.detailError = null;
    },
    clearError(state) {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    /* fetch emails */
    builder
      .addCase(fetchEmails.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchEmails.fulfilled, (state, action) => {
        state.loading = false;
        state.list = Array.isArray(action.payload) ? action.payload : [];
        state.loaded = true;
      })
      .addCase(fetchEmails.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload || "Failed to load emails.";
        state.loaded = true;
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
  },
});

export const { setFilter, clearSelected, clearError } = emailSlice.actions;
export default emailSlice.reducer;
