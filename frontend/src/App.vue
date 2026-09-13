<script setup lang="ts">
/**
 * 根组件。
 *
 * 用 <el-config-provider> 提供 Element Plus 的中文语言包 —— 组件改为按需引入后,
 * main.ts 里不再有 `app.use(ElementPlus, { locale })`, 而 provideGlobalConfig
 * 必须在组件上下文中调用, 这是官方的等价写法。
 */
import zhCn from 'element-plus/es/locale/lang/zh-cn'
</script>

<template>
  <el-config-provider :locale="zhCn">
    <router-view />
  </el-config-provider>
</template>
