import { defineConfig } from "vite";
import { resolve } from "path";

export default defineConfig({
  root: ".",
  server: {
    port: 3000,
    proxy: {
      "/api": {
        target: "http://localhost:5001",
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: "dist",
    rollupOptions: {
      input: {
        main: resolve(__dirname, "app.html"),
      },
    },
  },
});
