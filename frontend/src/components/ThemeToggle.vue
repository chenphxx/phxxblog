<script setup lang="ts">
import { Moon, Sunny } from '@element-plus/icons-vue'
import { useThemeStore } from '@/stores/theme'

const theme = useThemeStore()
</script>

<template>
  <el-tooltip :content="theme.isDark ? '切换到浅色模式' : '切换到深色模式'">
    <!-- el-tooltip 不会给触发器加 aria-label(只加在提示内容上), 这里显式补上:
         否则纯图标按钮在屏幕阅读器里是一个"没有名字的按钮" -->
    <el-button
      circle
      :icon="theme.isDark ? Sunny : Moon"
      :aria-label="theme.isDark ? '切换到浅色模式' : '切换到深色模式'"
      @click="theme.toggle()"
    />
  </el-tooltip>
</template>
