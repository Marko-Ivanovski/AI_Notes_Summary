// vite.config.ts

import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // any request to /upload is forwarded to your Flask backend
      "/upload": {
        target: "http://localhost:5000",
        changeOrigin: true,
        secure: false,
      },
      // later you can proxy /query the same way
      "/query": {
        target: "http://localhost:5000",
        changeOrigin: true,
        secure: false,
      },
    },
  },
});
