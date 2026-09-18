<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import Vditor from 'vditor'
import { ElMessage } from 'element-plus'
import { useThemeStore } from '@/stores/theme'
import { getAccessToken } from '@/utils/tokenStorage'

const props = withDefaults(defineProps<{ modelValue: string; height?: number | 'auto' }>(), {
  // 默认自适应内容高度: 编辑区(以及外层卡片)高度完全跟随正文, 滚动交给页面完成,
  // 编辑器内部不再出现滚动条, 内容少时也不会留下一块空白。需要固定高度(内部滚动)时传数字。
  height: 'auto',
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
    // 全屏层级必须高于站点头部(.site-header 的 z-index: 100), 否则全屏后
    // 编辑器的工具栏会被头部盖住, 既看不见也点不到(无法退出全屏)。
    fullscreen: { index: 1000 },
    theme: theme.isDark ? 'dark' : 'classic',
    mode: 'ir',
    cache: { enable: false },
    preview: {
      // Vditor 的"居中"是 JS 按 (容器宽 - maxWidth) / 2 算出左右行内 padding 实现的,
      // 默认的 800 会让后台上千像素宽的编辑区两侧各空出 200px 以上;
      // 放宽到 1100 让写作区更宽, 同时保留少量居中留白(容器变窄时 Vditor 会自动回落到 35px)。
      maxWidth: 1100,
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
 * 深浅色切换时同步编辑器主题。
 *
 * Vditor 的深色是 vditor--dark 类加一组 CSS 变量, 代码高亮配色(vs / vs2015)
 * 也是按主题名单独加载的样式表, 因此只在初始化时读一次主题是不够的:
 * 运行中切换深浅色后编辑器会一直保持初始化时的浅色(白底), 与页面其余部分割裂。
 */
watch(
  () => theme.isDark,
  (isDark) => {
    vditor?.setTheme(isDark ? 'dark' : 'classic', isDark ? 'dark' : 'light', isDark ? 'vs2015' : 'vs')
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

<style scoped>
/*
 * 编辑器跟随外层高度: 写作页会把卡片拉满视口(见 WriteView), 这里以 flex 让 .vditor 吃掉
 * 表单项里的剩余高度, 内容更多时仍按内容继续变长(高度本身是 auto, 见 onMounted 的 height 选项)。
 * 外层不是 flex 容器时(如日记对话框)高度仍只由内容决定。
 */
.vditor-editor {
  display: flex;
  flex-direction: column;
  flex: 1;
}

.vditor-editor :deep(.vditor) {
  flex: 1 1 auto;
}
</style>
