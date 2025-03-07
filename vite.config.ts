import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    strictPort: true,
  },
  // Prevent vite from obscuring Rust errors
  clearScreen: false,
  // Tauri expects a fixed port, fail if that port is not available
  build: {
    // Tauri supports es2021
    target: ['es2021', 'chrome100', 'safari13'],
    // Don't minify for debug builds
    minify: !!process.env.TAURI_DEBUG ? false : 'esbuild',
    // Produce sourcemaps for debug builds
    sourcemap: !!process.env.TAURI_DEBUG,
  },
}); 