import { createSlice } from "@reduxjs/toolkit";

const authSlice = createSlice({
  name: "auth",
  initialState: {
    token: localStorage.getItem("google_access_token") || null,
  },
  reducers: {
    setToken(state, action) {
      state.token = action.payload;
      if (action.payload) {
        localStorage.setItem("google_access_token", action.payload);
      }
    },
    logout(state) {
      state.token = null;
      localStorage.removeItem("google_access_token");
    },
  },
});

export const { setToken, logout } = authSlice.actions;
export default authSlice.reducer;
