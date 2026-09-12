import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import { messageConfig } from 'element-plus'
import zhCn from 'element-plus/es/locale/lang/zh-cn'

import 'element-plus/dist/index.css'
import 'element-plus/theme-chalk/dark/css-vars.css'
import 'vditor/dist/index.css'
// 自托管 @font-face 要放在主题之前, 保证 --font-sans/--font-mono 引用时字体已注册
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

app.use(createPinia())
app.use(router)
app.use(ElementPlus, { locale: zhCn })
app.mount('#app')
