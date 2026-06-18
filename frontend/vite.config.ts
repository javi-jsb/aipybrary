import { configDefaults, defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  test: {
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"],
    // Playwright specs under e2e/ are *.spec.ts too; keep them out of Vitest
    // (they run via `pnpm test:e2e`, not the unit runner).
    exclude: [...configDefaults.exclude, "e2e/**"],
    // Tailwind classes are irrelevant to behaviour; skip CSS processing for speed.
    css: false,
    coverage: {
      provider: "v8",
      reporter: ["text", "html"],
      include: ["src/**/*.{ts,tsx}"],
      // Entry point and ambient declarations have no behaviour worth covering.
      exclude: ["src/main.tsx", "src/vite-env.d.ts", "src/test/**"],
    },
  },
});
