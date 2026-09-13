import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    /*
     * Element Plus 按需引入。
     *
     * 以前是 main.ts 里 `app.use(ElementPlus)` 全量注册: 产物里出现了 100 多个
     * 组件(ElWatermark / ElCarousel / ElCalendar / ElTour / ElTransfer ...),
     * 而源码实际只用到 43 个, 主 chunk 因此多出 300~400 KB。
     *
     * importStyle: 'css' 让每个**模板里用到**的组件顺带引入自己的样式文件,
     * 于是可以把 `element-plus/dist/index.css`(349 KB)整包去掉。
     *
     * 注意: 解析器看不到程序式 API(ElMessage / ElMessageBox / ElLoading)的调用,
     * 它们的样式**不会**自动注入, 必须在 main.ts 里手动 import(那里有清单与说明),
     * 否则确认框会变成左上角的裸按钮、提示条不可见。
     * 漏了会被 `npm run check:element-styles` 拦下。
     */
    Components({
      dts: 'src/components.d.ts',
      resolvers: [ElementPlusResolver({ importStyle: 'css' })],
    }),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    port: 5173,
    // 监听所有地址, 保证 localhost / 127.0.0.1 均可访问
    host: true,
    /*
     * 忽略构建产物与「临时配置文件」。
     *
     * watch.ignored 有两层作用:
     *   1) 忽略 dist/ 与 .vite/: 否则 `npm run build` 写盘时 dev server 会收到大量
     *      change 事件并整页刷新, 看起来像「服务出问题」。
     *   2) 忽略 config 临时文件(Windows 上是必须的):
     *      vite.config.ts 被改动时, Vite 会写一个 `.vite.config.ts.<pid>.<guid>.tmpdir\`
     *      临时文件再去 watch 它; 该文件在 Windows 上常被占用, fs.watch 抛
     *      EBUSY, 而 FSWatcher 的 error 事件没人处理 → 整个 dev server 进程直接退出。
     *      这就是「改完配置就得重启服务」的根因。
     *      Vite 会把你自己的 ignore 模式与内建模式合并(见 Vite resolveChokidarOptions),
     *      所以这里追加即可, 不会覆盖它自带的忽略规则。
     */
    watch: {
      ignored: [
        '**/dist/**',
        '**/.vite/**',
        '**/.vite.config.ts.*.tmpdir/**',
        '**/*.tmpdir/**',
        '**/vite.config.ts.tmp*',
      ],
    },
    // 开发环境代理: 前端请求统一转发到 FastAPI 后端
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/assets': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      // API 文档(仅 admin 可访问, 需携带文档鉴权 cookie)
      '/docs': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/redoc': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/openapi.json': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
