import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Proxy API + uploads to the FastAPI backend (docker-compose exposes :8000)
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": { target: "http://localhost:8000", changeOrigin: true },
      "/uploads": { target: "http://localhost:8000", changeOrigin: true },
    },
  },
});
