import { Navigate, Route, Routes } from "react-router";
import { BookCopies } from "./components/BookCopies";
import { BookForm } from "./components/BookForm";
import { BooksList } from "./components/BooksList";
import { MemberDetail } from "./components/MemberDetail";
import { MemberForm } from "./components/MemberForm";
import { MembersList } from "./components/MembersList";
import { LoanForm } from "./components/LoanForm";
import { LoansList } from "./components/LoansList";
import { LoginScreen } from "./components/LoginScreen";
import { ProtectedLayout } from "./components/ProtectedLayout";
import { DEFAULT_AUTHENTICATED_ROUTE, LOGIN_ROUTE } from "./routes";

export default function App() {
  return (
    <Routes>
      <Route path={LOGIN_ROUTE} element={<LoginScreen />} />
      <Route element={<ProtectedLayout />}>
        <Route path="/books" element={<BooksList />} />
        <Route path="/books/new" element={<BookForm />} />
        <Route path="/books/:id/edit" element={<BookForm />} />
        <Route path="/books/:id/copies" element={<BookCopies />} />
        <Route path="/members" element={<MembersList />} />
        <Route path="/members/new" element={<MemberForm />} />
        <Route path="/members/:id" element={<MemberDetail />} />
        <Route path="/members/:id/edit" element={<MemberForm />} />
        <Route path="/loans" element={<LoansList />} />
        <Route path="/loans/new" element={<LoanForm />} />
        <Route index element={<Navigate to={DEFAULT_AUTHENTICATED_ROUTE} replace />} />
      </Route>
      <Route path="*" element={<Navigate to={DEFAULT_AUTHENTICATED_ROUTE} replace />} />
    </Routes>
  );
}
