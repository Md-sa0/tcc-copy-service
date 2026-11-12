import { readFileSync } from "node:fs";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const apiTarget = process.env.API_PROXY_TARGET || "http://127.0.0.1:8000";
const tlsCertPath = process.env.DEV_TLS_CERT;
const tlsKeyPath = process.env.DEV_TLS_KEY;
const https = tlsCertPath && tlsKeyPath
  ? {
      cert: readFileSync(tlsCertPath),
      key: readFileSync(tlsKeyPath),
    }
  : undefined;

function apiProxy() {
  return {
    target: apiTarget,
    configure(proxy) {
      proxy.on("proxyReq", (proxyRequest) => {
        proxyRequest.setHeader(
          "X-Forwarded-Proto",
          process.env.APP_PUBLIC_SCHEME || "http",
        );
      });
    },
  };
}

export default defineConfig({
  plugins: [react()],
  server: {
    https,
    watch: {
      usePolling: true,
    },
    proxy: {
      "/api": apiProxy(),
      "/health": apiProxy(),
    },
  },
});
