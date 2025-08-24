import path from "path"
import react from "@vitejs/plugin-react"
import { defineConfig } from "vite"

export default defineConfig({
  // server: {
  //   proxy: {
  //     '/api': 'http://127.0.0.1:5000',
  //   }
  // },
  server: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:5000', // Flask server
        changeOrigin: true,
        // Preserve the trailing slashes
        rewrite: (path) => path,
      },
    },
  },
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
})
