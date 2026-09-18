<script setup lang="ts">
/**
 * 元信息小图标。
 *
 * 为什么不用 @element-plus/icons-vue:
 *   这里用的都是 12~14px 的元信息图标(日历/眼睛/标签…), EP 图标是为按钮设计的 1em 方形,
 *   在等宽字体的元信息行里基线不好对齐。内联 SVG 可以精确控制尺寸、描边粗细,
 *   并且 fill/stroke 用 currentColor, 自动跟随任意主题的 --muted / --primary。
 */
const props = withDefaults(
  defineProps<{
    name: IconName
    /** 图标边长, 默认 1em(跟随父级字号) */
    size?: string | number
    /** 顺时针旋转, 用于 loading */
    spin?: boolean
  }>(),
  { size: '1em', spin: false },
)

export type IconName =
  | 'calendar'
  | 'clock'
  | 'eye'
  | 'thumb'
  | 'folder'
  | 'tag'
  | 'file'
  | 'user'
  | 'link'
  | 'history'
  | 'refresh'
  | 'back'
  | 'external'
  | 'hash'

/** 路径数据: 统一 24x24 视口、描边风格, 与站内其它图标一致 */
const PATHS: Record<IconName, string> = {
  calendar: 'M8 2v4M16 2v4M3 10h18M5 4h14a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2Z',
  clock: 'M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20ZM12 6v6l4 2',
  eye: 'M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7-10-7-10-7Z M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z',
  thumb:
    'M7 22V10l4.2-7.4A1.6 1.6 0 0 1 14 3.4l.6 4.5H19a2 2 0 0 1 2 2.4l-1.4 8A2 2 0 0 1 17.6 22H7Z M7 22H4a1 1 0 0 1-1-1v-10a1 1 0 0 1 1-1h3',
  folder: 'M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7Z',
  tag: 'M20.6 13.4 12 22l-9-9V4a1 1 0 0 1 1-1h9l7.6 7.6a2 2 0 0 1 0 2.8Z M7.5 7.5h.01',
  hash: 'M4 9h16M4 15h16M10 3 8 21M16 3l-2 18',
  file: 'M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6Z M14 2v6h6',
  user: 'M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2 M12 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8Z',
  link: 'M10 13a5 5 0 0 0 7.5 .5l3-3a5 5 0 0 0-7-7l-1.7 1.7 M14 11a5 5 0 0 0-7.5-.5l-3 3a5 5 0 0 0 7 7l1.7-1.7',
  history: 'M3 12a9 9 0 1 0 3-6.7L3 8 M3 3v5h5 M12 7v5l3 2',
  refresh: 'M21 12a9 9 0 1 1-3-6.7L21 8 M21 3v5h-5',
  back: 'M19 12H5M11 18l-6-6 6-6',
  external: 'M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6 M15 3h6v6 M10 14 21 3',
}
</script>

<template>
  <svg
    class="meta-icon"
    :class="{ 'is-spin': props.spin }"
    :width="props.size"
    :height="props.size"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="1.8"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
    focusable="false"
  >
    <path :d="PATHS[props.name]" />
  </svg>
</template>

<style scoped>
.meta-icon {
  display: inline-block;
  flex-shrink: 0;
  vertical-align: -0.14em;
}
.meta-icon.is-spin {
  animation: meta-icon-spin 0.9s linear infinite;
}
@keyframes meta-icon-spin {
  to {
    transform: rotate(360deg);
  }
}
@media (prefers-reduced-motion: reduce) {
  .meta-icon.is-spin {
    animation-duration: 2.4s;
  }
}
</style>
