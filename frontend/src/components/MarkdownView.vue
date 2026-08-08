<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import Vditor from 'vditor'
import { useThemeStore } from '@/stores/theme'

const props = defineProps<{ content: string }>()
const el = ref<HTMLDivElement>()
const theme = useThemeStore()

async function render() {
  if (!el.value) return
  const currentTheme = theme.isDark ? 'dark' : 'light'
  el.value.innerHTML = ''
  await Vditor.preview(el.value, props.content || '', {
    mode: currentTheme,
    theme: { current: currentTheme },
    hljs: { lineNumber: true, style: currentTheme === 'dark' ? 'github-dark' : 'github' },
  })
  // 代码块一键复制按钮
  Vditor.codeRender(el.value)
  // 视频/音频/iframe 渲染
  Vditor.mediaRender(el.value)
  // 图片点击放大
  const images = el.value.querySelectorAll('img')
  images.forEach((img) => {
    img.addEventListener('click', () => Vditor.previewImage(img as HTMLImageElement))
  })
}

onMounted(render)
watch(() => props.content, render)
watch(() => theme.isDark, render)
</script>

<template>
  <div ref="el" class="markdown-body vditor-reset" />
</template>
