import { useAuth } from "./auth/AuthContext";
import { BooksList } from "./components/BooksList";
import { LoginScreen } from "./components/LoginScreen";

export default function App() {
  const { isAuthenticated } = useAuth();
  // Gating: the Books view only mounts when authenticated, so an
  // unauthenticated user never issues the GET /books request.
  return isAuthenticated ? <BooksList /> : <LoginScreen />;
}
