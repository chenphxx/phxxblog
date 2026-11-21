<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import { modulesApi } from '@/api'
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
function resetDraft(list: ModuleInfo[])
{
    draftEnabled.value = Object.fromEntries(list.map((item) => [item.id, item.enabled]))
    draftVisibility.value = Object.fromEntries(list.map((item) => [item.id, item.visibility]))
}

/** 有改动的模块 id(只有这些会提交) */
const dirtyIds = computed(() =>
    modules.value
        .filter
        (
            (item) =>
                draftEnabled.value[item.id] !== item.enabled ||
                // 可见范围固定的模块(核心模块与后台自身的能力)没有控件, 也不参与比较
                (!item.locked && !item.visibility_fixed && draftVisibility.value[item.id] !== item.visibility),
        )
        .map((item) => item.id),
)

/** 可见范围是不是可调的: 核心模块与"管理后台自身的能力"都由模块声明固定 */
function visibilityEditable(item: ModuleInfo): boolean
{
    return !item.locked && !item.visibility_fixed
}

/** 可见范围固定时给一句理由: 后台自身的能力与"站点基本盘"固定下来的原因不同 */
function visibilityFixedHint(item: ModuleInfo): string
{
    if (item.visibility_fixed) return '管理后台自身的内容固定为"仅管理员", 不允许修改'
    return '核心模块是站点基本盘, 可见范围不允许修改'
}

/** 按分类分组展示(顺序由后端给出) */
const groups = computed(() =>
    Object.entries(categories.value)
        .map(([key, name]) => ({ key, name, items: modules.value.filter((item) => item.category === key) }))
        .filter((group) => group.items.length > 0),
)

async function load()
{
    loading.value = true
    try
    {
        const data = await modulesApi.admin()
        modules.value = data.modules
        categories.value = data.categories
        visibilities.value = data.visibilities
        resetDraft(data.modules)
    } finally
    {
        loading.value = false
    }
}

async function save()
{
    if (!dirtyIds.value.length) return
    const byId = new Map(modules.value.map((item) => [item.id, item]))
    const payload: Record<string, { enabled?: boolean; visibility?: string }> = {}
    for (const id of dirtyIds.value)
    {
        const patch: { enabled?: boolean; visibility?: string } = { enabled: draftEnabled.value[id] }
        const item = byId.get(id)
        // 固定值来自模块声明, 提交了也会被后端拒绝, 所以只提交可调模块的可见范围
        if (item && visibilityEditable(item)) patch.visibility = draftVisibility.value[id]
        payload[id] = patch
    }
    saving.value = true
    try
    {
        const data = await modulesApi.update(payload)
        modules.value = data.modules
        resetDraft(data.modules)
        // 前台的模块状态要重新拉一次, 侧栏与后台菜单才会立刻跟随
        await moduleStore.load(true)
        ElMessage.success('模块开关已保存')
    } catch
    {
        // 拦截器已提示(例如试图禁用核心模块)
        await load()
    } finally
    {
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
                <span v-if="dirtyIds.length" class="muted">有 {{ dirtyIds.length }} 项未保存的改动</span>
            </div>
            <div class="admin-toolbar-actions">
                <el-button :icon="Refresh" :loading="loading" @click="load">重新载入</el-button>
                <el-button type="primary" :loading="saving" :disabled="!dirtyIds.length" @click="save">保存</el-button>
            </div>
        </div>

        <section v-for="group in groups" :key="group.key" class="card module-group">
            <h3>{{ group.name }}</h3>

            <div
                v-for="item in group.items"
                :key="item.id"
                class="module-row"
                :class="{ 'is-disabled': !item.available }"
            >
                <div class="module-head">
                    <div class="module-title">
                        <span class="module-name" :title="`${item.id} · ${item.description}`">{{ item.name }}</span>
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
                                (value: string | number | boolean | undefined) =>
                                    (draftVisibility[item.id] = String(value))
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

                        <el-tooltip
                            :disabled="!item.locked"
                            content="核心模块被其它能力依赖, 不允许禁用"
                            placement="top"
                        >
                            <el-switch
                                :model-value="draftEnabled[item.id]"
                                :disabled="item.locked"
                                :aria-label="`${draftEnabled[item.id] ? '禁用' : '启用'}${item.name}`"
                                @update:model-value="
                                    (value: string | number | boolean) => (draftEnabled[item.id] = Boolean(value))
                                "
                            />
                        </el-tooltip>
                    </div>
                </div>

            </div>
        </section>
    </div>
</template>

<style scoped>
.module-group
{
    margin-bottom: 16px;
}

/* 分类标题与卡片内其它区块保持同一节奏 */
.module-group > h3
{
    margin: 0 0 var(--space-4);
    font-size: 17px;
    font-weight: 650;
}

.module-row
{
    padding: 14px 0;
    border-top: 1px solid var(--border);
}

.module-row:first-of-type
{
    border-top: none;
    padding-top: 0;
}

/* 不可用的模块(自己被禁用或依赖未启用)整行压暗, 一眼能看出当前没有生效 */
.module-row.is-disabled
{
    opacity: 0.62;
}

.module-head
{
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    flex-wrap: wrap;
}

/* 右侧控件: 可见范围 + 启用开关(核心模块没有可见范围控件, 用一段文字占位) */
.module-controls
{
    display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
}

.module-visibility-fixed
{
    font-size: 12.5px;
}

.module-title
{
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
    min-width: 0;
}

.module-name
{
    font-size: 15px;
    font-weight: 600;
    color: var(--text);
}

</style>
