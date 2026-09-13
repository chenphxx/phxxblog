import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { messageConfig } from 'element-plus'

/*
 * 样式引入顺序(有意义, 别随手调换):
 *   1. element-plus 的深色变量 + 程序式组件样式 —— Element Plus 基础样式
 *   2. vditor/dist/index.css                      —— 编辑器与正文预览
 *   3. styles/fonts.css                           —— 自托管 Cascadia Code
 *   4. styles/theme-green.css                     —— 主题令牌 + 后台主题层
 * 主题令牌必须晚于 Element Plus 与 Vditor 才能覆盖它们(见 admin.css 的说明)。
 *
 * 这里**不再**引入 element-plus/dist/index.css(整包 349 KB):
 * 模板里用到的组件由 vite.config.ts 的 ElementPlusResolver 按需注入样式。
 */
import 'element-plus/theme-chalk/dark/css-vars.css'
/*
 * 程序式调用的组件必须手动补样式。
 *
 * ElementPlusResolver 只能看到**模板里的标签**(<el-button> 等), 看不到
 * `ElMessageBox.confirm(...)` / `ElMessage.success(...)` 这类 JS 调用, 所以这两处样式
 * 不会自动进来 —— 后果是确认框变成页面左上角一堆裸按钮, 提示条完全不可见
 * (曾经因此把"内容为空"的提示吞噬掉, 表现为"点保存没反应, 要点两次")。
 *
 * 以后再加 ElNotification / ElLoading 等程序式 API, 在这里补一行对应样式;
 * npm run check:element-styles 会检查有没有漏。
 */
import 'element-plus/es/components/message-box/style/css'
import 'element-plus/es/components/message/style/css'
import 'vditor/dist/index.css'
import './styles/fonts.css'
import './styles/theme-green.css'

import App from './App.vue'
import router from './router'

// 应用加载前先应用保存的深浅色与主题, 避免闪烁。
// 未选过主题时回退到 'cuanmu'(即"预设", 与 styles/themes/registry.ts 的
// DEFAULT_THEME 一致), 此时 :root 中的默认令牌就是这套配色。
const savedMode = localStorage.getItem('blog_theme')
const savedStyle = localStorage.getItem('blog_theme_style')
document.documentElement.classList.toggle('dark', savedMode === 'dark')
document.documentElement.setAttribute('data-theme', savedStyle || 'cuanmu')

const app = createApp(App)

// 全局: 顶部提示条支持手动点击关闭
messageConfig.showClose = true

// 组件按需引入, 不再 app.use(ElementPlus)。
// Element Plus 的中文语言包通过 App.vue 里的 <el-config-provider :locale="zhCn"> 提供。
app.use(createPinia())
app.use(router)
app.mount('#app')
