// vite.config.ts

import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      "/upload": {
        target: "http://localhost:5000",
        changeOrigin: true,
        secure: false,
      },
      "/query": {
        target: "http://localhost:5000",
        changeOrigin: true,
        secure: false,
      },
    },
  },
});
