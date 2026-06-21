import { useAuth0 } from "@auth0/auth0-react";
import LoginPage from "./pages/LoginPage";
import InboxPage from "./pages/InboxPage";

export default function App() {
  const { isLoading, isAuthenticated, error } = useAuth0();

  if (isLoading)
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin" />
      </div>
    );

  if (error)
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-red-500">Authentication error: {error.message}</p>
      </div>
    );

  return isAuthenticated ? <InboxPage /> : <LoginPage />;
}
