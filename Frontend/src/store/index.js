import { configureStore, combineReducers } from "@reduxjs/toolkit";
import authReducer from "./authSlice";
import emailReducer from "./emailSlice";

const appReducer = combineReducers({
  auth: authReducer,
  email: emailReducer,
});

const rootReducer = (state, action) => {
  if (action.type === "auth/logout") {
    state = undefined;
  }
  return appReducer(state, action);
};

const store = configureStore({
  reducer: rootReducer,
});

export default store;
