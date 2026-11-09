<script setup lang="ts">
/**
 * @brief 视口懒加载图片
 *
 * 与原生 loading="lazy" 不同, 此组件在图片接近视口前不会写入 src,
 * 因此长列表或媒体库不会提前创建大量图片请求, 也不会阻塞路由切换等交互
 */
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'

const props = withDefaults(
  defineProps<{
    /** 图片真实地址 */
    src: string
    /** 替代文本 */
    alt?: string
    /** 立即加载, 用于已经打开的预览浮层 */
    eager?: boolean
    /** 提前加载距离, 默认在进入视口前 300px 开始请求 */
    rootMargin?: string
  }>(),
  {
    alt: '',
    eager: false,
    rootMargin: '300px 0px',
  },
)

const image = ref<HTMLImageElement | null>(null)
const activeSrc = ref(props.eager ? props.src : '')
let observer: IntersectionObserver | null = null

function loadNow() {
  if (props.src) activeSrc.value = props.src
  observer?.disconnect()
  observer = null
}

function startObserving() {
  if (!image.value) return
  observer?.disconnect()
  observer = new IntersectionObserver(
    (entries) => {
      if (entries.some((entry) => entry.isIntersecting)) loadNow()
    },
    { rootMargin: props.rootMargin },
  )
  observer.observe(image.value)
}

onMounted(() => {
  if (props.eager || !props.src || !('IntersectionObserver' in window)) {
    loadNow()
    return
  }
  startObserving()
})

watch(
  () => props.src,
  (src) => {
    if (!src) {
      activeSrc.value = ''
      observer?.disconnect()
      observer = null
      return
    }
    if (activeSrc.value) {
      activeSrc.value = src
      return
    }
    startObserving()
  },
)

onBeforeUnmount(() => {
  observer?.disconnect()
  observer = null
})
</script>

<template>
  <img ref="image" :src="activeSrc || undefined" :alt="alt" loading="lazy" decoding="async" fetchpriority="low" />
</template>
