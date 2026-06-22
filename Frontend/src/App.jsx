import { useState, useEffect } from "react";
import LoginPage from "./pages/LoginPage";
import InboxPage from "./pages/InboxPage";

export default function App() {
  const [googleToken, setGoogleToken] = useState(() =>
    localStorage.getItem("google_access_token"),
  );

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const token = params.get("access_token");

    if (!token) return;

    setGoogleToken(token);

    const url = new URL(window.location.href);
    url.searchParams.delete("access_token");

    window.history.replaceState({}, "", url.pathname + url.search);
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("google_access_token");
    setGoogleToken(null);
  };

  return googleToken ? (
    <InboxPage token={googleToken} onLogout={handleLogout} />
  ) : (
    <LoginPage />
  );
}
