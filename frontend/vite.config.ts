import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import tsconfigPaths from "vite-tsconfig-paths";

// GitHub Pages project site:
// https://amulyavarshney.github.io/AI-Enhanced-Attendance-Operations-Platform/
const pagesBase =
  process.env.VITE_BASE_PATH ||
  (process.env.GITHUB_PAGES === "true"
    ? "/AI-Enhanced-Attendance-Operations-Platform/"
    : "/");

export default defineConfig(({ mode }) => ({
  base: pagesBase,
  server: {
    host: "::",
    port: 8080,
  },
  plugins: [react(), tsconfigPaths()].filter(Boolean),
  build: {
    outDir: "dist",
    sourcemap: mode === "development",
  },
}));
