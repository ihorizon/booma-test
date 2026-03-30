import { defineConfig } from 'vite';
import { nodePolyfills } from 'vite-plugin-node-polyfills'
import aurelia from '@aurelia/vite-plugin';
import babel from 'vite-plugin-babel';

const apiProxy = {
  '/api': { target: 'http://127.0.0.1:8000', changeOrigin: true },
  '/health': { target: 'http://127.0.0.1:8000', changeOrigin: true },
};

export default defineConfig({
  server: {
    open: !process.env.CI,
    port: 9000,
    proxy: apiProxy,
  },
  preview: {
    port: 9000,
    proxy: apiProxy,
  },
  esbuild: {
    target: 'es2022'
  },
  plugins: [
    // Extra dev instrumentation; omit during production build to save memory/CPU.
    aurelia({
      useDev: process.env.NODE_ENV !== 'production',
    }),
    babel(),
    nodePolyfills(),
  ],
});
