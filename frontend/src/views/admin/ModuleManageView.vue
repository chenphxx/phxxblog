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
 * 展示系统里注册的全部能力(后端模块注册表), 只负责"开启 / 禁用":
 *   - 核心模块锁定, 不允许禁用; 禁用后它的接口 404, 前台与后台入口一起消失
 *   - 模块自己的参数不在这里配: 声明了参数的功能启用后, 到"系统设置"里配置
 *   - 每个非核心模块还能设"可见范围": 公开(所有访客可用) / 仅管理员(只有站点管理
 *     权限的账号可用); 配成仅管理员后, 前台连它的入口与接口都不再对访客开放
 *
 * 这样开关与参数各归一处: 这里回答"这个能力在不在", 系统设置回答"它怎么工作"
 *
 * 修改先落在本地草稿里, 点"保存"才提交; 提交后清空草稿并刷新前台的模块状态,
 * 因此侧栏与后台菜单会立刻跟着变
 */

const moduleStore = useModulesStore()

const modules = ref<ModuleInfo[]>([])
const categories = ref<Record<string, string>>({})
const visibilities = ref<Record<string, string>>({})
const loading = ref(true)
const saving = ref(false)

/** 开关与可见范围的本地草稿 */
const draftEnabled = ref<Record<string, boolean>>({})
const draftVisibility = ref<Record<string, string>>({})

/** 把后端返回的模块清单写进草稿 */
function resetDraft(list: ModuleInfo[]) {
  draftEnabled.value = Object.fromEntries(list.map((item) => [item.id, item.enabled]))
  draftVisibility.value = Object.fromEntries(list.map((item) => [item.id, item.visibility]))
}

/** 有改动的模块 id(只有这些会提交) */
const dirtyIds = computed(() =>
  modules.value
    .filter(
      (item) =>
        draftEnabled.value[item.id] !== item.enabled ||
        // 可见范围固定的模块(核心模块与后台自身的能力)没有控件, 也不参与比较
        (!item.locked && !item.visibility_fixed && draftVisibility.value[item.id] !== item.visibility),
    )
    .map((item) => item.id),
)

/** 可见范围是不是可调的: 核心模块与"管理后台自身的能力"都由模块声明固定 */
function visibilityEditable(item: ModuleInfo): boolean {
  return !item.locked && !item.visibility_fixed
}

/** 可见范围固定时给一句理由: 后台自身的能力与"站点基本盘"固定下来的原因不同 */
function visibilityFixedHint(item: ModuleInfo): string {
  if (item.visibility_fixed) return '管理后台自身的内容固定为"仅管理员", 不允许修改'
  return '核心模块是站点基本盘, 可见范围不允许修改'
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
    visibilities.value = data.visibilities
    resetDraft(data.modules)
  } finally {
    loading.value = false
  }
}

async function save() {
  if (!dirtyIds.value.length) return
  const byId = new Map(modules.value.map((item) => [item.id, item]))
  const payload: Record<string, { enabled?: boolean; visibility?: string }> = {}
  for (const id of dirtyIds.value) {
    const patch: { enabled?: boolean; visibility?: string } = { enabled: draftEnabled.value[id] }
    const item = byId.get(id)
    // 固定值来自模块声明, 提交了也会被后端拒绝, 所以只提交可调模块的可见范围
    if (item && visibilityEditable(item)) patch.visibility = draftVisibility.value[id]
    payload[id] = patch
  }
  saving.value = true
  try {
    const data = await modulesApi.update(payload)
    modules.value = data.modules
    resetDraft(data.modules)
    // 前台的模块状态要重新拉一次, 侧栏与后台菜单才会立刻跟随
    await moduleStore.load(true)
    ElMessage.success('模块开关已保存')
  } catch {
    // 拦截器已提示(例如试图禁用核心模块)
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

    <p class="muted module-hint">
      "可见范围"控制这项能力对谁开放: 公开 = 所有访客都能使用; 仅管理员 = 只有拥有站点管理权限的账号能用
      模块自身的权限码不受影响(例如站内搜索设为公开, 也只影响访客能否搜索, 不改变任何权限)
      管理后台自身的内容固定为"仅管理员", 不提供调整入口
    </p>

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

          <div class="module-controls">
            <el-radio-group
              v-if="visibilityEditable(item)"
              :model-value="draftVisibility[item.id]"
              size="small"
              aria-label="可见范围"
              @update:model-value="
                (value: string | number | boolean | undefined) => (draftVisibility[item.id] = String(value))
              "
            >
              <el-radio-button v-for="(label, value) in visibilities" :key="value" :value="value">
                {{ label }}
              </el-radio-button>
            </el-radio-group>
            <el-tooltip v-else :content="visibilityFixedHint(item)" placement="top">
              <span class="muted module-visibility-fixed">
                {{ visibilities[item.visibility] || item.visibility }}
              </span>
            </el-tooltip>

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
          <!-- 有参数的功能, 参数在系统设置里配: 这里只说要到哪儿去配, 不重复渲染表单 -->
          <span v-if="item.settings.length" class="meta-line">
            {{ item.settings.length }} 项参数在「系统设置」里配置
          </span>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.module-group {
  margin-bottom: 16px;
}

/* 可见范围的语义说明: 放在工具条下方, 不占卡片内的空间 */
.module-hint {
  margin: 0 0 16px;
  font-size: 12.5px;
  line-height: 1.7;
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

/* 右侧控件: 可见范围 + 启用开关(核心模块没有可见范围控件, 用一段文字占位) */
.module-controls {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.module-visibility-fixed {
  font-size: 12.5px;
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
</style>
