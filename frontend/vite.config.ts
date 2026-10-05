import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [react()],
  base: '/static/',
  server: {
    host: '0.0.0.0',
    port: 5173,
    strictPort: true,
    origin: 'http://localhost:5173',
    cors: true,
    watch: {
      usePolling: process.env.VITE_USE_POLLING === 'true',
    },
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    manifest: true,
    rollupOptions: {
      input: {
        settings: 'src/entries/settings.tsx',
        playground: 'src/entries/playground.tsx',
      },
    },
  },
});
