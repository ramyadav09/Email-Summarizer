import { configureStore } from "@reduxjs/toolkit";
import authReducer from "./authSlice";
import emailReducer from "./emailSlice";

const store = configureStore({
  reducer: {
    auth: authReducer,
    email: emailReducer,
  },
});

export default store;
