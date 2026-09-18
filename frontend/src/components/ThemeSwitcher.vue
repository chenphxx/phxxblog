<script setup lang="ts">
import { computed } from 'vue'
import { Brush, Check, Moon, Sunny } from '@element-plus/icons-vue'
import { THEME_OPTIONS, type ThemeId } from '@/styles/themes/registry'
import { useThemeStore } from '@/stores/theme'

const theme = useThemeStore()

const current = computed(() => THEME_OPTIONS.find((t) => t.id === theme.themeId) ?? THEME_OPTIONS[0])

function pick(id: ThemeId) {
  theme.setTheme(id)
}
</script>

<template>
  <div class="theme-bar">
    <!-- 配色主题: 下拉里每一项带三色小圆点预览 -->
    <el-dropdown trigger="click" placement="bottom-end" popper-class="theme-dropdown">
      <button class="theme-picker" type="button" :title="`当前主题: ${current.name}`">
        <el-icon class="picker-icon"><Brush /></el-icon>
        <span class="picker-dots" aria-hidden="true">
          <i v-for="c in current.swatch" :key="c" :style="{ background: c }" />
        </span>
        <span class="picker-name">{{ current.name }}</span>
      </button>

      <template #dropdown>
        <el-dropdown-menu class="theme-menu">
          <el-dropdown-item
            v-for="item in THEME_OPTIONS"
            :key="item.id"
            :class="{ 'is-current': item.id === theme.themeId }"
            @click="pick(item.id)"
          >
            <div class="opt">
              <span class="opt-dots" aria-hidden="true">
                <i v-for="c in item.swatch" :key="c" :style="{ background: c }" />
              </span>
              <span class="opt-name">{{ item.name }}</span>
              <el-icon v-if="item.id === theme.themeId" class="opt-check"><Check /></el-icon>
            </div>
          </el-dropdown-item>
        </el-dropdown-menu>
      </template>
    </el-dropdown>

    <!-- 深色 / 浅色 -->
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
  </div>
</template>

<style scoped>
.theme-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.theme-picker {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  height: 32px;
  padding: 0 12px;
  cursor: pointer;
  color: var(--text);
  background: var(--card-bg);
  border: 1px solid var(--border-strong);
  border-radius: var(--el-border-radius-base, 6px);
  font-family: inherit;
  font-size: 13px;
  transition:
    border-color 0.2s ease,
    background-color 0.2s ease,
    color 0.2s ease;
}

.theme-picker:hover {
  border-color: var(--primary);
  color: var(--primary-strong);
}

html.dark .theme-picker:hover {
  color: var(--primary);
}

.picker-icon {
  font-size: 15px;
  color: var(--primary);
}

.picker-dots,
.opt-dots {
  display: inline-flex;
  gap: 3px;
  flex-shrink: 0;
}

.picker-dots i {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  border: 1px solid color-mix(in srgb, var(--border-strong) 70%, transparent);
}

.picker-name {
  font-weight: 600;
  white-space: nowrap;
}

/* 下拉面板: 面板本身挂在 body 上, 靠 popper-class 选中 */
:global(.theme-dropdown) {
  padding: 6px;
}

:global(.theme-dropdown .el-dropdown-menu) {
  padding: 0;
  background: transparent;
  border: 0;
}

:global(.theme-dropdown .el-dropdown-menu__item) {
  padding: 8px 10px;
  border-radius: var(--el-border-radius-base, 6px);
  line-height: 1.4;
  transition: background-color 0.18s ease;
}

:global(.theme-dropdown .el-dropdown-menu__item.is-current) {
  background: var(--primary-weak);
}

.opt {
  display: flex;
  align-items: center;
  gap: 10px;
  /* 只显示「色点 + 主题名」, 因此比原来(带描述时 250px)窄很多 */
  min-width: 160px;
}

.opt-dots i {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  border: 1px solid color-mix(in srgb, var(--border-strong) 70%, transparent);
}

.opt-name {
  font-size: 13.5px;
  font-weight: 600;
  color: var(--text);
  white-space: nowrap;
}

.opt-check {
  margin-left: auto;
  color: var(--primary);
}

@media (max-width: 720px) {
  .picker-name {
    display: none;
  }
}
</style>
