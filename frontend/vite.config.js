import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      '/chat': 'http://localhost:8000',
      '/agent': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        bypass: (req, res, options) => {
          if (req.method === 'GET' && req.headers.accept?.includes('html')) {
            return '/index.html';
          }
        }
      },
      '/sidebar': 'http://localhost:8000',
      '/chat-history': 'http://localhost:8000',
      '/upload-dox': 'http://localhost:8000',
      '/test-redis': 'http://localhost:8000'
    }
  }
})
