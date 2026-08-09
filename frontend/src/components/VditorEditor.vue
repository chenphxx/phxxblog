<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import Vditor from 'vditor'
import { ElMessage } from 'element-plus'
import { useThemeStore } from '@/stores/theme'

const props = withDefaults(defineProps<{ modelValue: string; height?: number }>(), {
  height: 520,
})
const emit = defineEmits<{ (e: 'update:modelValue', value: string): void }>()

const el = ref<HTMLDivElement>()
let vditor: Vditor | null = null
let ready = false
const theme = useThemeStore()

onMounted(() => {
  if (!el.value) return
  vditor = new Vditor(el.value, {
    // 资源全部走本地 public/vditor, 避免依赖 unpkg/jsdelivr CDN 导致编辑器无法初始化
    cdn: '/vditor',
    width: '100%',
    value: props.modelValue,
    height: props.height,
    theme: theme.isDark ? 'dark' : 'classic',
    mode: 'ir',
    cache: { enable: false },
    preview: {
      theme: { current: theme.isDark ? 'dark' : 'light' },
      hljs: { lineNumber: true, style: theme.isDark ? 'github-dark' : 'github' },
    },
    toolbar: [
      'headings',
      'bold',
      'italic',
      'strike',
      '|',
      'list',
      'ordered-list',
      'check',
      'outdent',
      'indent',
      '|',
      'quote',
      'line',
      'code',
      'inline-code',
      'insert-after',
      'insert-before',
      '|',
      'upload',
      'link',
      'table',
      '|',
      'undo',
      'redo',
      '|',
      'fullscreen',
      'preview',
      'export',
      'edit-mode',
    ],
    upload: {
      url: '/api/v1/media/upload',
      fieldName: 'file',
      max: 100 * 1024 * 1024,
      headers: {
        Authorization: `Bearer ${localStorage.getItem('blog_access_token') || ''}`,
      },
      // 注意: Vditor 传给 success 的是 responseText 字符串, 需要自行 JSON.parse
      success: (_editor, responseText) => {
        try {
          const result = JSON.parse(responseText) as {
            code?: number
            message?: string
            data?: { original_name: string; url: string }
          }
          if (result.code === 0 && result.data?.url) {
            vditor?.insertValue(`\n![${result.data.original_name}](${result.data.url})\n`)
          } else {
            ElMessage.error(result.message || '上传失败')
          }
        } catch {
          ElMessage.error('上传失败: 响应解析错误')
        }
      },
      error: (msg) => {
        ElMessage.error(`上传失败: ${msg}`)
      },
    },
    input: (value) => emit('update:modelValue', value),
    after: () => {
      ready = true
      // 初始化完成后再同步外部值(编辑文章时带出原文)
      if (props.modelValue && props.modelValue !== vditor?.getValue()) {
        vditor?.setValue(props.modelValue)
      }
    },
  })
})

onBeforeUnmount(() => {
  ready = false
  vditor?.destroy()
  vditor = null
})

// 外部传入的值变化时同步到编辑器; 编辑器未初始化完成前跳过, 由 after 回调接管
watch(
  () => props.modelValue,
  (value) => {
    if (ready && vditor && value !== vditor.getValue()) {
      vditor.setValue(value)
    }
  },
)
</script>

<template>
  <div ref="el" class="vditor-editor" />
</template>
