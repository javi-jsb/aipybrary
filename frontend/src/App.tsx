import { Navigate, Route, Routes } from "react-router";
import { BooksList } from "./components/BooksList";
import { LoginScreen } from "./components/LoginScreen";
import { ProtectedLayout } from "./components/ProtectedLayout";
import { DEFAULT_AUTHENTICATED_ROUTE, LOGIN_ROUTE } from "./routes";

export default function App() {
  return (
    <Routes>
      <Route path={LOGIN_ROUTE} element={<LoginScreen />} />
      <Route element={<ProtectedLayout />}>
        <Route path="/books" element={<BooksList />} />
        <Route index element={<Navigate to={DEFAULT_AUTHENTICATED_ROUTE} replace />} />
      </Route>
      <Route path="*" element={<Navigate to={DEFAULT_AUTHENTICATED_ROUTE} replace />} />
    </Routes>
  );
}
