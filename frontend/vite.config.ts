import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'

// https://vite.dev/config/
export default defineConfig({
    plugins: [
        vue(),
        // Element Plus 按需引入
        Components({
            dts: 'src/components.d.ts',
            resolvers: [ElementPlusResolver({ importStyle: 'css' })],
        }),
    ],
    resolve:
    {
        alias:
        {
            '@': fileURLToPath(new URL('./src', import.meta.url)),
        },
    },
    server:
    {
        port: 5173,
        // 监听所有地址, 保证 localhost / 127.0.0.1 均可访问
        host: true,
        // 忽略构建产物与"临时配置文件"
        watch:
        {
            ignored: [
                '**/dist/**',
                '**/.vite/**',
                '**/.vite.config.ts.*.tmpdir/**',
                '**/*.tmpdir/**',
                '**/vite.config.ts.tmp*',
            ],
        },
        // 开发环境代理: 前端请求统一转发到 FastAPI 后端
        proxy:
        {
            '/api':
            {
                target: 'http://localhost:8000',
                changeOrigin: true,
            },
            '/assets':
            {
                target: 'http://localhost:8000',
                changeOrigin: true,
            },
            // API 文档(仅 admin 可访问, 需携带文档鉴权 cookie)
            '/docs':
            {
                target: 'http://localhost:8000',
                changeOrigin: true,
            },
            '/redoc':
            {
                target: 'http://localhost:8000',
                changeOrigin: true,
            },
            '/openapi.json':
            {
                target: 'http://localhost:8000',
                changeOrigin: true,
            },
        },
    },
})
