import { Routes, Route, Navigate, useNavigate } from "react-router-dom";
import { useSelector, useDispatch } from "react-redux";
import { setToken, logout } from "./store/authSlice";
import LoginPage from "./pages/LoginPage";
import InboxPage from "./pages/InboxPage";
import EmailPage from "./pages/EmailPage";

function ProtectedRoute({ children }) {
  const token = useSelector((s) => s.auth.token);
  if (!token) return <Navigate to="/login" replace />;
  return children;
}

export default function App() {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const token = useSelector((s) => s.auth.token);

  /* synchronously capture OAuth token from URL before any routing */
  const params = new URLSearchParams(window.location.search);
  const oauthToken = params.get("access_token");
  if (oauthToken && oauthToken !== token) {
    dispatch(setToken(oauthToken));
    const cleanUrl = new URL(window.location.href);
    cleanUrl.searchParams.delete("access_token");
    window.history.replaceState({}, "", cleanUrl.pathname);
    return <Navigate to="/inbox" replace />;
  }

  const handleLogout = () => {
    dispatch(logout());
    navigate("/login");
  };

  return (
    <Routes>
      <Route path="/login" element={token ? <Navigate to="/inbox" replace /> : <LoginPage />} />
      <Route
        path="/inbox"
        element={
          <ProtectedRoute>
            <InboxPage onLogout={handleLogout} />
          </ProtectedRoute>
        }
      />
      <Route
        path="/email/:id"
        element={
          <ProtectedRoute>
            <EmailPage onLogout={handleLogout} />
          </ProtectedRoute>
        }
      />
      <Route path="*" element={<Navigate to="/inbox" replace />} />
    </Routes>
  );
}
