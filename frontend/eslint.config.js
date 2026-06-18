import js from "@eslint/js";
import globals from "globals";
import reactHooks from "eslint-plugin-react-hooks";
import reactRefresh from "eslint-plugin-react-refresh";
import tseslint from "typescript-eslint";
import prettier from "eslint-config-prettier";
import { globalIgnores } from "eslint/config";

export default tseslint.config([
  globalIgnores(["dist", "coverage", "test-results", "playwright-report"]),
  {
    files: ["**/*.{ts,tsx}"],
    extends: [
      js.configs.recommended,
      tseslint.configs.recommended,
      reactRefresh.configs.vite,
      prettier,
    ],
    plugins: {
      "react-hooks": reactHooks,
    },
    rules: {
      ...reactHooks.configs.recommended.rules,
    },
    languageOptions: {
      ecmaVersion: 2022,
      globals: globals.browser,
    },
  },
  {
    // Test files and helpers export non-component utilities; the Fast Refresh
    // rule is irrelevant to them.
    files: ["**/*.test.{ts,tsx}", "src/test/**"],
    rules: {
      "react-refresh/only-export-components": "off",
    },
  },
  {
    // Playwright config and E2E specs run under Node, not Vite/Fast Refresh.
    // The Playwright fixture parameter `use` trips the React Hooks rule, which
    // doesn't apply here.
    files: ["playwright.config.ts", "e2e/**"],
    rules: {
      "react-refresh/only-export-components": "off",
      "react-hooks/rules-of-hooks": "off",
    },
  },
]);
