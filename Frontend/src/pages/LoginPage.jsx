import { useAuth0 } from "@auth0/auth0-react";

export default function LoginPage() {
  const { loginWithRedirect } = useAuth0();

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 to-white flex items-center justify-center px-4">
      <div className="text-center max-w-md">
        <div className="text-5xl mb-4">📧</div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Email Summarizer</h1>
        <p className="text-gray-500 mb-8">Fetch your Gmail inbox and get AI-powered summaries in seconds.</p>
        <div className="flex gap-3 justify-center">
          <button
            onClick={() => loginWithRedirect()}
            className="px-5 py-2.5 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 transition-colors"
          >
            Log in
          </button>
          <button
            onClick={() => loginWithRedirect({ authorizationParams: { screen_hint: "signup" } })}
            className="px-5 py-2.5 border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50 transition-colors"
          >
            Sign up
          </button>
        </div>
      </div>
    </div>
  );
}
