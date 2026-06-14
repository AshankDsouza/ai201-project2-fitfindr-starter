import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Proxy /api calls to the Flask backend (server.py) on port 3000.

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": "http://localhost:3000",
    },
  },
});
