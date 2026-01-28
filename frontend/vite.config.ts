import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
    // Load env file based on `mode` in the current working directory.
    // Set the third parameter to '' to load all env regardless of the `VITE_` prefix.
    // const env = loadEnv(mode, process.cwd(), '') 
    // actually process.env is usually sufficient for simple node usage in config if we use 'dotenv' or similar, 
    // but in vite config, we can just use a default or check process.env if available (node context).

    const apiTarget = process.env.VITE_API_URL || 'http://127.0.0.1:8000';

    return {
        plugins: [react()],
        resolve: {
            alias: {
                "@": path.resolve(__dirname, "./src"),
            },
        },
        server: {
            host: true,
            watch: {
                usePolling: true,
            },
            proxy: {
                '/api': {
                    target: apiTarget,
                    changeOrigin: true,
                },
                '/images': {
                    target: apiTarget,
                    changeOrigin: true,
                },
                '/temp_images': {
                    target: apiTarget,
                    changeOrigin: true,
                }
            }
        }
    }
})
