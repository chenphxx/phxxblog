<script setup lang="ts">
/**
 * @brief 文章页右下角的回到顶部胶囊
 *
 * 自己监听滚动(passive + rAF 合并)并在卸载时清理, 因此不需要改动页面既有的滚动逻辑,
 * 模块被禁用时整块卸载即可
 *
 * 进度按正文元素的滚动比例计算: 正文顶部对齐视口顶部为 0%, 正文底部对齐视口底部为 100%;
 * 正文比视口还短(没有可滚动空间)时视为已读完
 */
import { ArrowUp } from '@element-plus/icons-vue'
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useKanbanniangStore } from '@/stores/kanbanniang'
import { useModulesStore } from '@/stores/modules'

const props = defineProps<{
  /** 正文元素; 还没渲染出来时为 null */
  target: HTMLElement | null
  /** 滚动超过该像素数后出现 */
  threshold: number
  /** 是否显示阅读进度 */
  showProgress: boolean
}>()

const kb = useKanbanniangStore()
const modules = useModulesStore()

/**
 * 看板娘默认停在右下角(见 components/Kanbanniang.vue 的 .kanbanniang 定位), 与胶囊重叠
 *
 * 它可见时把胶囊抬到它的画布高度之上, 避免浮层压在角色上; 窄屏(<900px)看板娘本就不展示,
 * 上抬只由 CSS 的宽屏媒体查询生效, 因此这里只算高度
 */
const lift = computed(() => {
  if (!modules.isEnabled('kanbanniang') || !kb.allowed || !kb.enabled) return 0
  return (kb.current.canvas?.height ?? 250) + 12
})

/** 当前滚动距离, 只用于判断是否越过阈值 */
const scrolled = ref(0)
/** 正文阅读进度(0-100) */
const progress = ref(0)

const visible = computed(() => scrolled.value > props.threshold)
const percent = computed(() => (props.showProgress ? progress.value : 0))

/** rAF 句柄: 滚动事件高频触发, 合并到一帧里只算一次 DOM 位置 */
let frame = 0

function measure() {
  frame = 0
  const scrollY = window.scrollY || 0
  scrolled.value = scrollY
  const el = props.target
  if (!el) {
    progress.value = 0
    return
  }
  const top = el.getBoundingClientRect().top + scrollY
  const span = el.offsetHeight - window.innerHeight
  if (span <= 0) {
    progress.value = 100
    return
  }
  const ratio = (scrollY - top) / span
  progress.value = Math.min(100, Math.max(0, Math.round(ratio * 100)))
}

function onScroll() {
  if (frame) return
  frame = window.requestAnimationFrame(measure)
}

function toTop() {
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

// 正文元素在模块配置回来之后才挂上, 换了目标要重新算一次
watch(() => props.target, measure)

onMounted(() => {
  measure()
  window.addEventListener('scroll', onScroll, { passive: true })
  window.addEventListener('resize', onScroll, { passive: true })
})

onBeforeUnmount(() => {
  window.removeEventListener('scroll', onScroll)
  window.removeEventListener('resize', onScroll)
  if (frame) window.cancelAnimationFrame(frame)
})
</script>

<template>
  <button
    type="button"
    class="back-to-top"
    :class="{ 'is-visible': visible }"
    :tabindex="visible ? 0 : -1"
    :style="{ '--back-to-top-lift': `${lift}px` }"
    title="回到顶部"
    aria-label="回到顶部"
    @click="toTop"
  >
    <span class="back-to-top-fill" :style="{ width: `${percent}%` }" aria-hidden="true" />
    <el-icon class="back-to-top-icon"><ArrowUp /></el-icon>
    <span v-if="showProgress" class="back-to-top-percent">{{ percent }}%</span>
  </button>
</template>

<style scoped>
.back-to-top {
  position: fixed;
  right: 24px;
  bottom: 24px;
  /* 低于移动端顶栏(60)与侧栏(80), 高于正文内容 */
  z-index: 40;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 34px;
  padding: 0 12px;
  overflow: hidden;
  font-family: var(--font-sans);
  font-size: 12.5px;
  line-height: 1;
  color: var(--muted);
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: var(--radius-pill);
  box-shadow: var(--shadow-float);
  cursor: pointer;
  opacity: 0;
  transform: translateY(8px);
  pointer-events: none;
  transition:
    opacity var(--dur) var(--ease),
    transform var(--dur) var(--ease),
    color 0.15s ease,
    border-color 0.15s ease;
}
.back-to-top.is-visible {
  opacity: 1;
  transform: none;
  pointer-events: auto;
}
/* 看板娘只在宽屏展示: 它可见时按 --back-to-top-lift 把胶囊抬到角色上方 */
@media (min-width: 901px) {
  .back-to-top {
    bottom: calc(24px + var(--back-to-top-lift, 0px));
  }
}
.back-to-top:hover {
  color: var(--primary);
  border-color: var(--border-strong);
}
/* 胶囊内横向填充: 宽度等于阅读进度, 写在图标与文字下面一层 */
.back-to-top-fill {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  background: color-mix(in srgb, var(--primary) 16%, transparent);
  transition: width 0.15s linear;
  pointer-events: none;
}
.back-to-top-icon,
.back-to-top-percent {
  position: relative;
}
.back-to-top-percent {
  font-variant-numeric: tabular-nums;
}
</style>
