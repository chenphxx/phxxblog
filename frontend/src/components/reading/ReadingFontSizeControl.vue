<script setup lang="ts">
/**
 * @brief 文章正文字号控件
 *
 * 结构是 A- / 5 个档位点 / A+, 档位点的像素来自固定档位表(见 utils/readingFont.ts);
 * 后台可以限制允许范围, 因此只渲染范围内的档位点, 窄屏(<720px)只留两端的加减按钮
 */
import { computed } from 'vue'
import { READING_FONT_STEPS } from '@/utils/readingFont'

const props = defineProps<{
  /** 当前档位(1 起) */
  step: number
  /** 后台允许的最小档位 */
  minStep: number
  /** 后台允许的最大档位 */
  maxStep: number
}>()

const emit = defineEmits<{ 'update:step': [number] }>()

const canDecrease = computed(() => props.step > props.minStep)
const canIncrease = computed(() => props.step < props.maxStep)

/** 允许范围内的档位点(序号 + 像素, 用于 title 与无障碍标签) */
const steps = computed(() =>
  READING_FONT_STEPS.map((px, index) => ({ step: index + 1, px })).filter(
    (item) => item.step >= props.minStep && item.step <= props.maxStep,
  ),
)
</script>

<template>
  <div class="reading-font" role="group" aria-label="正文字号">
    <button
      type="button"
      class="reading-font-btn"
      :disabled="!canDecrease"
      title="减小字号"
      aria-label="减小字号"
      @click="emit('update:step', step - 1)"
    >
      A-
    </button>
    <div class="reading-font-dots">
      <button
        v-for="item in steps"
        :key="item.step"
        type="button"
        class="reading-font-dot"
        :class="{ 'is-active': item.step === step }"
        :title="`正文字号 ${item.px}px`"
        :aria-label="`正文字号 ${item.px} 像素`"
        :aria-pressed="item.step === step"
        @click="emit('update:step', item.step)"
      />
    </div>
    <button
      type="button"
      class="reading-font-btn"
      :disabled="!canIncrease"
      title="增大字号"
      aria-label="增大字号"
      @click="emit('update:step', step + 1)"
    >
      A+
    </button>
  </div>
</template>

<style scoped>
.reading-font {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}
.reading-font-btn {
  min-width: 28px;
  height: 24px;
  padding: 0 6px;
  font-family: var(--font-sans);
  font-size: 12px;
  line-height: 1;
  color: var(--muted);
  background: transparent;
  border: 1px solid var(--border);
  border-radius: var(--radius-chip);
  cursor: pointer;
  transition:
    color 0.15s ease,
    border-color 0.15s ease;
}
.reading-font-btn:hover:not(:disabled) {
  color: var(--text);
  border-color: var(--border-strong);
}
.reading-font-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
.reading-font-dots {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.reading-font-dot {
  width: 7px;
  height: 7px;
  padding: 0;
  border: 1px solid var(--border-strong);
  border-radius: 50%;
  background: transparent;
  cursor: pointer;
  transition:
    background-color 0.15s ease,
    border-color 0.15s ease;
}
.reading-font-dot:hover {
  border-color: var(--primary);
}
.reading-font-dot.is-active {
  background: var(--primary);
  border-color: var(--primary);
}
/* 窄屏放不下 5 个点: 只留 A- / A+ */
@media (max-width: 720px) {
  .reading-font-dots {
    display: none;
  }
}
</style>
