<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import Vditor from 'vditor'
import { ElMessage } from 'element-plus'
import { useThemeStore } from '@/stores/theme'
import { getAccessToken } from '@/utils/tokenStorage'

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
      // 对齐 VSCode 默认配色: 浅色 vs(Visual Studio), 深色 vs2015
      hljs: { lineNumber: true, style: theme.isDark ? 'vs2015' : 'vs' },
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
        Authorization: `Bearer ${getAccessToken()}`,
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

/**
 * 直接读编辑器里的当前内容, 不依赖 v-model 是否已经同步过来。
 *
 * 为什么需要: Vditor 的 `input` 回调在中文输入法组字期间会被跳过(见 vditor
 * src/ts/ir/index.ts 的 composingLock), 也就是说"编辑器里已经有字、但 modelValue
 * 还是空的"这一瞬间是真实存在的。此时点保存会命中"请输入内容"的空值判断,
 * 用户看到的现象是"点一次没反应, 再点一次才行"。
 * 因此保存前应调用本方法取值, 而不是相信 props.modelValue。
 */
function getValue(): string {
  return vditor?.getValue() ?? props.modelValue
}

defineExpose({ getValue })
</script>

<template>
  <div ref="el" class="vditor-editor" />
</template>
