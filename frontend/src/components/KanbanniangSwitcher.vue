<script setup lang="ts">
import { Check, MagicStick, Picture } from '@element-plus/icons-vue'
import { KANBANNIAN_MODELS, type KanbanniangModelId } from '@/kanbanniang/registry'
import { useKanbanniangStore } from '@/stores/kanbanniang'

const kb = useKanbanniangStore()

function pick(id: KanbanniangModelId) {
  kb.setModel(id)
}
</script>

<template>
  <div v-if="kb.allowed" class="kb-bar">
    <!-- 形象: 关掉看板娘后整组收起, 只留开关 -->
    <el-dropdown v-if="kb.enabled" trigger="click" placement="bottom-end" popper-class="kb-dropdown">
      <button class="kb-picker" type="button" :title="`当前形象: ${kb.current.name}`">
        <el-icon class="picker-icon"><Picture /></el-icon>
        <span class="picker-name">{{ kb.current.name }}</span>
      </button>

      <template #dropdown>
        <el-dropdown-menu class="kb-menu">
          <el-dropdown-item
            v-for="item in KANBANNIAN_MODELS"
            :key="item.id"
            :class="{ 'is-current': item.id === kb.modelId }"
            @click="pick(item.id)"
          >
            <div class="opt">
              <span class="opt-name">{{ item.name }}</span>
              <span class="opt-series">{{ item.series }}</span>
              <el-icon v-if="item.id === kb.modelId" class="opt-check"><Check /></el-icon>
            </div>
          </el-dropdown-item>
        </el-dropdown-menu>
      </template>
    </el-dropdown>

    <!-- 是否展示看板娘 -->
    <el-tooltip :content="kb.enabled ? '隐藏看板娘' : '展示看板娘'">
      <!-- el-tooltip 不会给触发器加 aria-label, 这里显式补上(同 ThemeSwitcher) -->
      <el-button
        class="kb-toggle"
        :class="{ 'is-on': kb.enabled }"
        circle
        :icon="MagicStick"
        :aria-label="kb.enabled ? '隐藏看板娘' : '展示看板娘'"
        @click="kb.toggle()"
      />
    </el-tooltip>
  </div>
</template>

<style scoped>
.kb-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.kb-picker {
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
  transition: border-color 0.2s ease, background-color 0.2s ease, color 0.2s ease;
}

.kb-picker:hover {
  border-color: var(--primary);
  color: var(--primary-strong);
}

html.dark .kb-picker:hover {
  color: var(--primary);
}

.picker-icon {
  font-size: 15px;
  color: var(--primary);
}

.picker-name {
  font-weight: 600;
  white-space: nowrap;
}

/* 开关打开时用主题主色, 关闭时保持普通按钮观感, 一眼能看出当前状态 */
.kb-toggle.is-on,
.kb-toggle.is-on:hover {
  color: var(--primary);
  border-color: var(--primary);
  background: var(--primary-weak);
}

/* 下拉面板挂在 body 上, 靠 popper-class 选中 */
:global(.kb-dropdown) {
  padding: 6px;
}

:global(.kb-dropdown .el-dropdown-menu) {
  padding: 0;
  background: transparent;
  border: 0;
}

:global(.kb-dropdown .el-dropdown-menu__item) {
  padding: 8px 10px;
  border-radius: var(--el-border-radius-base, 6px);
  line-height: 1.4;
  transition: background-color 0.18s ease;
}

:global(.kb-dropdown .el-dropdown-menu__item.is-current) {
  background: var(--primary-weak);
}

.opt {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 160px;
}

.opt-name {
  font-size: 13.5px;
  font-weight: 600;
  color: var(--text);
  white-space: nowrap;
}

.opt-series {
  font-family: var(--font-mono);
  font-size: 11.5px;
  color: var(--muted);
  white-space: nowrap;
}

.opt-check {
  margin-left: auto;
  color: var(--primary);
}

/* 窄屏既不展示看板娘, 也不展示这组控件(断点与 Kanbanniang.vue 的 NARROW_QUERY 一致) */
@media (max-width: 900px) {
  .kb-bar {
    display: none;
  }
}
</style>
