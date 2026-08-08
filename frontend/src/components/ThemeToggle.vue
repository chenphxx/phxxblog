<script setup lang="ts">
import { Moon, Sunny } from '@element-plus/icons-vue'
import { useThemeStore } from '@/stores/theme'

const theme = useThemeStore()
</script>

<template>
  <el-tooltip :content="theme.isDark ? '切换到浅色模式' : '切换到深色模式'">
    <el-button circle :icon="theme.isDark ? Sunny : Moon" @click="theme.toggle()" />
  </el-tooltip>
</template>
