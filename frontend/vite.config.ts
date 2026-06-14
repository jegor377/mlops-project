import { reactRouter } from "@react-router/dev/vite";
import tailwindcss from "@tailwindcss/vite";
import { defineConfig } from "vite";
import tsconfigPaths from "vite-tsconfig-paths";

const BACKEND_URL = process.env.VITE_BACKEND_URL;
const enableProxy = Boolean(BACKEND_URL);

export default defineConfig({
  plugins: [tailwindcss(), reactRouter(), tsconfigPaths()],
  ...(enableProxy
    ? {
        server: {
          proxy: {
            "/api": {
              target: BACKEND_URL,
              changeOrigin: true,
            },
            "/auth": {
              target: BACKEND_URL,
              changeOrigin: true,
            },
            "/docs": {
              target: BACKEND_URL,
              changeOrigin: true,
            },
            "/openapi.json": {
              target: BACKEND_URL,
              changeOrigin: true,
            },
          },
        },
      }
    : {}),
});
