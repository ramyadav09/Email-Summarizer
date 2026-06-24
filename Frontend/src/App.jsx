import { Routes, Route, Navigate, useNavigate } from "react-router-dom";
import { useSelector, useDispatch } from "react-redux";
import { setToken, logout, setUser } from "./store/authSlice";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
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
  const user = useSelector((s) => s.auth.user);

  /* capture OAuth token from URL (Google callback redirect) */
  const params = new URLSearchParams(window.location.search);
  const oauthToken = params.get("access_token");
  if (oauthToken && oauthToken !== token) {
    dispatch(setToken(oauthToken));
    if (user) {
      dispatch(setUser({ ...user, is_google_linked: true }));
    }
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
      <Route path="/register" element={token ? <Navigate to="/inbox" replace /> : <RegisterPage />} />
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

