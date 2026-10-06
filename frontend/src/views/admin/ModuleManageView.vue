<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import { modulesApi } from '@/api'
import { MODULE_BY_ID } from '@/modules/registry'
import { useModulesStore } from '@/stores/modules'
import type { ModuleInfo } from '@/types'

/**
 * @brief 后台 - 模块管理
 *
 * 展示系统里注册的全部能力(后端模块注册表), 支持:
 *   - 启用 / 禁用(核心模块锁定, 禁用后它的接口 404, 前台与后台入口一起消失)
 *   - 维护模块自己的配置项(类型由后端模块元数据声明)
 *
 * 修改先落在本地草稿里, 点"保存"才提交; 提交后清空草稿并刷新前台的模块状态,
 * 因此侧栏与后台菜单会立刻跟着变
 */

const moduleStore = useModulesStore()

const modules = ref<ModuleInfo[]>([])
const categories = ref<Record<string, string>>({})
const loading = ref(true)
const saving = ref(false)

/** 本地草稿: 开关与配置分两份, 便于模板里按类型取值(避免在模板中做类型断言) */
const draftEnabled = ref<Record<string, boolean>>({})
const draftSettings = ref<Record<string, Record<string, boolean | number | string>>>({})

/** 把后端返回的模块清单写进草稿 */
function resetDraft(list: ModuleInfo[]) {
  draftEnabled.value = Object.fromEntries(list.map((item) => [item.id, item.enabled]))
  draftSettings.value = Object.fromEntries(
    list.map((item) => [item.id, Object.fromEntries(item.settings.map((setting) => [setting.key, setting.value]))]),
  )
}

/** 有改动的模块 id(只有这些会提交) */
const dirtyIds = computed(() =>
  modules.value
    .filter((item) => {
      if (draftEnabled.value[item.id] !== item.enabled) return true
      return item.settings.some((setting) => draftSettings.value[item.id]?.[setting.key] !== setting.value)
    })
    .map((item) => item.id),
)

/** 取模块配置的当前草稿值(按类型给模板用) */
function settingValue(id: string, key: string): boolean | number | string {
  return draftSettings.value[id]?.[key] ?? ''
}

/**
 * 写入模块配置的草稿值
 *
 * @param id 模块 id
 * @param key 配置键
 * @param value 新值(布尔/数字/字符串)
 */
function updateSetting(id: string, key: string, value: boolean | number | string) {
  draftSettings.value[id] = { ...draftSettings.value[id], [key]: value }
}

/** 按分类分组展示(顺序由后端给出) */
const groups = computed(() =>
  Object.entries(categories.value)
    .map(([key, name]) => ({ key, name, items: modules.value.filter((item) => item.category === key) }))
    .filter((group) => group.items.length > 0),
)

/** 模块占用的前台入口 / 后台菜单(来自前端注册表, 让"关掉会发生什么"一眼可见) */
function navOf(id: string) {
  const def = MODULE_BY_ID.get(id)
  if (!def) return []
  return [...(def.frontNav ?? []), ...(def.adminNav ?? [])].map((item) => item.label)
}

async function load() {
  loading.value = true
  try {
    const data = await modulesApi.admin()
    modules.value = data.modules
    categories.value = data.categories
    resetDraft(data.modules)
  } finally {
    loading.value = false
  }
}

async function save() {
  if (!dirtyIds.value.length) return
  const payload: Record<string, { enabled?: boolean; settings?: Record<string, unknown> }> = {}
  for (const id of dirtyIds.value) {
    payload[id] = { enabled: draftEnabled.value[id], settings: draftSettings.value[id] }
  }
  saving.value = true
  try {
    const data = await modulesApi.update(payload)
    modules.value = data.modules
    resetDraft(data.modules)
    // 前台的模块状态要重新拉一次, 侧栏与后台菜单才会立刻跟随
    await moduleStore.load(true)
    ElMessage.success('模块配置已保存')
  } catch {
    // 拦截器已提示(例如试图禁用核心模块或配置值越界)
    await load()
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<template>
  <div v-loading="loading">
    <h2>模块管理</h2>

    <div class="admin-toolbar">
      <div class="admin-toolbar-filters">
        <span class="muted">
          共 {{ modules.length }} 个模块;
          <template v-if="dirtyIds.length">有 {{ dirtyIds.length }} 项未保存的改动</template>
          <template v-else>没有未保存的改动</template>
        </span>
      </div>
      <div class="admin-toolbar-actions">
        <el-button :icon="Refresh" :loading="loading" @click="load">重新载入</el-button>
        <el-button type="primary" :loading="saving" :disabled="!dirtyIds.length" @click="save">保存</el-button>
      </div>
    </div>

    <section v-for="group in groups" :key="group.key" class="card module-group">
      <h3>{{ group.name }}</h3>

      <div v-for="item in group.items" :key="item.id" class="module-row" :class="{ 'is-disabled': !item.available }">
        <div class="module-head">
          <div class="module-title">
            <span class="module-name">{{ item.name }}</span>
            <code class="module-id">{{ item.id }}</code>
            <el-tag v-if="item.locked" size="small" type="info" effect="plain">核心</el-tag>
            <el-tag v-if="item.frontend_only" size="small" type="info" effect="plain">纯前台</el-tag>
            <el-tag v-if="item.disabled_dependencies.length" size="small" type="warning" effect="plain">
              依赖未启用: {{ item.disabled_dependencies.join(', ') }}
            </el-tag>
          </div>

          <el-tooltip :disabled="!item.locked" content="核心模块被其它能力依赖, 不允许禁用" placement="top">
            <el-switch
              :model-value="draftEnabled[item.id]"
              :disabled="item.locked"
              inline-prompt
              active-text="启用"
              inactive-text="禁用"
              @update:model-value="(value: string | number | boolean) => (draftEnabled[item.id] = Boolean(value))"
            />
          </el-tooltip>
        </div>

        <p class="module-desc muted">{{ item.description }}</p>

        <div class="module-meta">
          <span v-if="item.api_prefix" class="meta-line">
            接口 <code>{{ item.api_prefix }}</code>
          </span>
          <span v-if="item.depends_on.length" class="meta-line">依赖 {{ item.depends_on.join(', ') }}</span>
          <span v-if="item.permissions.length" class="meta-line">
            权限
            <code v-for="code in item.permissions" :key="code" class="perm-chip">{{ code }}</code>
          </span>
          <span v-if="navOf(item.id).length" class="meta-line">入口 {{ navOf(item.id).join(' / ') }}</span>
        </div>

        <div v-if="item.settings.length" class="module-settings">
          <div v-for="setting in item.settings" :key="setting.key" class="setting-item">
            <label class="setting-label">
              {{ setting.name }}
              <span v-if="setting.description" class="muted setting-desc">{{ setting.description }}</span>
            </label>

            <el-switch
              v-if="setting.kind === 'bool'"
              :model-value="Boolean(settingValue(item.id, setting.key))"
              @update:model-value="
                (value: string | number | boolean) => updateSetting(item.id, setting.key, Boolean(value))
              "
            />
            <el-input-number
              v-else-if="setting.kind === 'int'"
              :model-value="Number(settingValue(item.id, setting.key))"
              :min="setting.minimum ?? undefined"
              :max="setting.maximum ?? undefined"
              controls-position="right"
              style="width: 160px"
              @update:model-value="(value: number | undefined) => updateSetting(item.id, setting.key, value ?? 0)"
            />
            <el-input
              v-else
              :model-value="String(settingValue(item.id, setting.key))"
              style="max-width: 520px"
              clearable
              @update:model-value="(value: string) => updateSetting(item.id, setting.key, value)"
            />
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.module-group {
  margin-bottom: 16px;
}

/* 分类标题与卡片内其它区块保持同一节奏 */
.module-group > h3 {
  margin: 0 0 var(--space-4);
  font-size: 17px;
  font-weight: 650;
}

.module-row {
  padding: 14px 0;
  border-top: 1px solid var(--border);
}

.module-row:first-of-type {
  border-top: none;
  padding-top: 0;
}

/* 不可用的模块(自己被禁用或依赖未启用)整行压暗, 一眼能看出当前没有生效 */
.module-row.is-disabled {
  opacity: 0.62;
}

.module-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.module-title {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  min-width: 0;
}

.module-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--text);
}

.module-id,
.perm-chip {
  font-family: var(--font-mono);
  font-size: 11.5px;
  color: var(--muted);
  background: var(--code-bg);
  border-radius: var(--radius-chip);
  padding: 1px 7px;
}

.module-desc {
  margin: 6px 0 0;
  font-size: 13px;
}

.module-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 16px;
  margin-top: 8px;
  font-size: 12.5px;
  color: var(--muted);
}

.module-meta code {
  font-family: var(--font-mono);
  font-size: 11.5px;
}

.meta-line {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

/* 模块配置: 与"系统设置"页一致的两列排布 */
.module-settings {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 12px 24px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px dashed var(--border);
}

.setting-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}

.setting-label {
  font-size: 13px;
  color: var(--text);
}

.setting-desc {
  margin-left: 6px;
  font-size: 12px;
}
</style>
