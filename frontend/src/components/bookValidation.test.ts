import { describe, it, expect } from "vitest";
import {
  EMPTY_BOOK_FORM_VALUES,
  validateBookForm,
  validateIsbn,
  type BookFormValues,
} from "./bookValidation";

function values(overrides: Partial<BookFormValues> = {}): BookFormValues {
  return { ...EMPTY_BOOK_FORM_VALUES, title: "T", author: "A", ...overrides };
}

describe("validateIsbn", () => {
  it("accepts valid ISBN-13 (with or without hyphens)", () => {
    expect(validateIsbn("9780060934347")).toBeNull();
    expect(validateIsbn("978-0-06-093434-7")).toBeNull();
  });

  it("accepts valid ISBN-10, including a trailing X check digit", () => {
    expect(validateIsbn("0306406152")).toBeNull();
    expect(validateIsbn("043942089X")).toBeNull();
  });

  it("rejects bad checksums", () => {
    expect(validateIsbn("9780000000000")).toBe("Invalid ISBN-13 checksum.");
    expect(validateIsbn("0306406153")).toBe("Invalid ISBN-10 checksum.");
  });

  it("rejects bad formats and lengths", () => {
    expect(validateIsbn("12345")).toBe("ISBN must be 10 or 13 digits after removing hyphens.");
    expect(validateIsbn("12345X7890")).toBe("Invalid ISBN-10 format.");
    expect(validateIsbn("043942089x")).toBe("Invalid ISBN-10 format.");
    expect(validateIsbn("978006093434A")).toBe("Invalid ISBN-13 format.");
  });
});

describe("validateBookForm", () => {
  it("returns no errors for valid minimal input", () => {
    expect(validateBookForm(values())).toEqual({});
  });

  it("requires title and author (after trimming)", () => {
    const errors = validateBookForm(values({ title: "   ", author: "" }));
    expect(errors.title).toBe("Title is required.");
    expect(errors.author).toBe("Author is required.");
  });

  it("enforces max lengths", () => {
    const errors = validateBookForm(values({ title: "x".repeat(501), author: "y".repeat(301) }));
    expect(errors.title).toMatch(/at most 500/);
    expect(errors.author).toMatch(/at most 300/);
  });

  it("only validates the ISBN when provided, surfacing its message", () => {
    expect(validateBookForm(values({ isbn: "" })).isbn).toBeUndefined();
    expect(validateBookForm(values({ isbn: "1234567890" })).isbn).toBe("Invalid ISBN-10 checksum.");
  });

  it("rejects non-integer and out-of-range publication years", () => {
    expect(validateBookForm(values({ publicationYear: "19.5" })).publicationYear).toMatch(
      /whole number/,
    );
    expect(validateBookForm(values({ publicationYear: "3000" })).publicationYear).toMatch(
      /valid publication year/,
    );
    expect(validateBookForm(values({ publicationYear: "1965" })).publicationYear).toBeUndefined();
  });
});
