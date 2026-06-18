// Client-side mirror of the backend's book validation (BookCreate/BookUpdate),
// so the form can reject bad input before issuing a request the API would answer
// with a 422. The ISBN algorithm intentionally matches `_validate_isbn` in
// `app/books/domain/book_model.py` byte-for-byte (hyphens stripped, uppercase
// "X" only, ISBN-10/13 checksums).

export interface BookFormValues {
  title: string;
  author: string;
  isbn: string;
  publicationYear: string;
  synopsis: string;
}

export const EMPTY_BOOK_FORM_VALUES: BookFormValues = {
  title: "",
  author: "",
  isbn: "",
  publicationYear: "",
  synopsis: "",
};

export type BookFieldErrors = Partial<Record<keyof BookFormValues, string>>;

const TITLE_MAX = 500;
const AUTHOR_MAX = 300;

/** Validate an ISBN string the way the backend does. Returns an error message,
 * or `null` when valid. The caller decides whether an empty ISBN is allowed. */
export function validateIsbn(raw: string): string | null {
  const stripped = raw.replace(/-/g, "");

  if (stripped.length === 10) {
    if (!/^[0-9]{9}[0-9X]$/.test(stripped)) {
      return "Invalid ISBN-10 format.";
    }
    let total = 0;
    for (let i = 0; i < 9; i++) total += Number(stripped[i]) * (10 - i);
    const check = stripped[9] === "X" ? 10 : Number(stripped[9]);
    if ((total + check) % 11 !== 0) return "Invalid ISBN-10 checksum.";
    return null;
  }

  if (stripped.length === 13) {
    if (!/^[0-9]{13}$/.test(stripped)) return "Invalid ISBN-13 format.";
    let total = 0;
    for (let i = 0; i < 13; i++) total += Number(stripped[i]) * (i % 2 === 0 ? 1 : 3);
    if (total % 10 !== 0) return "Invalid ISBN-13 checksum.";
    return null;
  }

  return "ISBN must be 10 or 13 digits after removing hyphens.";
}

/** Generate a random, format-valid ISBN-13: the `978` prefix, 9 random digits,
 * and the mod-10 check digit. Its output always passes {@link validateIsbn}; it
 * exists so the form can offer a "Generate" shortcut without weakening the rule. */
export function generateIsbn13(): string {
  const digits = [9, 7, 8];
  for (let i = 0; i < 9; i++) digits.push(Math.floor(Math.random() * 10));
  let total = 0;
  for (let i = 0; i < 12; i++) total += digits[i] * (i % 2 === 0 ? 1 : 3);
  const check = (10 - (total % 10)) % 10;
  digits.push(check);
  return digits.join("");
}

/** Per-field validation for the book form. An empty map means the values are
 * safe to submit. Optional fields (ISBN, year, synopsis) are only validated
 * when provided. */
export function validateBookForm(values: BookFormValues): BookFieldErrors {
  const errors: BookFieldErrors = {};

  const title = values.title.trim();
  if (title === "") errors.title = "Title is required.";
  else if (title.length > TITLE_MAX)
    errors.title = `Title must be at most ${TITLE_MAX} characters.`;

  const author = values.author.trim();
  if (author === "") errors.author = "Author is required.";
  else if (author.length > AUTHOR_MAX) {
    errors.author = `Author must be at most ${AUTHOR_MAX} characters.`;
  }

  const isbn = values.isbn.trim();
  if (isbn !== "") {
    const isbnError = validateIsbn(isbn);
    if (isbnError) errors.isbn = isbnError;
  }

  const year = values.publicationYear.trim();
  if (year !== "") {
    const parsed = Number(year);
    if (!Number.isInteger(parsed)) {
      errors.publicationYear = "Publication year must be a whole number.";
    } else if (parsed < 0 || parsed > new Date().getFullYear() + 1) {
      errors.publicationYear = "Enter a valid publication year.";
    }
  }

  return errors;
}
