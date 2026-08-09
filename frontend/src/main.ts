import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import { messageConfig } from 'element-plus'
import zhCn from 'element-plus/es/locale/lang/zh-cn'

import 'element-plus/dist/index.css'
import 'element-plus/theme-chalk/dark/css-vars.css'
import 'vditor/dist/index.css'
import './styles/theme.css'

import App from './App.vue'
import router from './router'

// 应用加载前先应用保存的主题, 避免闪烁
const savedTheme = localStorage.getItem('blog_theme')
document.documentElement.classList.toggle('dark', savedTheme === 'dark')
document.documentElement.setAttribute('data-theme', savedTheme === 'dark' ? 'dark' : 'light')

const app = createApp(App)

// 全局: 顶部提示条支持手动点击关闭
messageConfig.showClose = true

app.use(createPinia())
app.use(router)
app.use(ElementPlus, { locale: zhCn })
app.mount('#app')
