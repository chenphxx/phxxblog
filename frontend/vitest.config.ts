import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'

/**
 * 测试专用配置。
 *
 * 为什么单独一份而不是往 vite.config.ts 里加 test 块:
 *   vite.config 里有 Element Plus 按需引入插件与 dev 代理 —— 测试用不到,
 *   而且 unplugin-vue-components 在测试时会试图解析组件并把结果写进
 *   src/components.d.ts, 造成"跑个测试改了源码"的副作用。
 *   这里只保留必需的两样: Vue 单文件组件编译 + `@` 路径别名。
 *
 * 环境: 默认 jsdom(组件与 DOM 相关测试需要); 纯函数测试可在文件顶部用
 *       `// @vitest-environment node` 切到更快的 node 环境。
 */
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    include: ['src/**/*.{test,spec}.{ts,js}', 'tests/**/*.{test,spec}.{ts,js}'],
    // element-plus 的样式引入在测试里没有意义, 直接忽略, 避免解析 CSS
    css: false,
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html'],
      include: ['src/**/*.{ts,vue}'],
      exclude: ['src/**/*.d.ts', 'src/types/**', 'src/main.ts'],
    },
  },
})
