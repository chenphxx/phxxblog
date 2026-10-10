<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { mediaApi, modulesApi, settingsApi } from '@/api'
import { useModulesStore } from '@/stores/modules'
import type { ModuleInfo, ModuleSettingValue } from '@/types'
import ModuleSettingField from './settings/ModuleSettingField.vue'
import SiteBasicCard from './settings/SiteBasicCard.vue'
import UploadCard from './settings/UploadCard.vue'

/** 单文件上传上限(MB)的默认值, 与后端 core/settings_schema.py 保持一致 */
const UPLOAD_SIZE_DEFAULT_MB = 100

const moduleStore = useModulesStore()

/*
 * 表单状态由页面独占(各卡片只读写自己那几个字段), 这样"未保存修改"的判定
 * 与保存时的整体提交都只有一个来源
 */
const form = ref({
  site_name: '',
  site_title: '',
  site_desc: '',
  site_icon: '',
  site_bio: '',
  max_upload_size_mb: UPLOAD_SIZE_DEFAULT_MB,
})
/** 最近一次载入/保存后的表单快照, 与当前表单对比即可判断是否有未保存的修改 */
const snapshot = ref(JSON.stringify(form.value))
const saving = ref(false)
const uploadingIcon = ref(false)

/** 模块清单(含各自的配置项定义与当前值)与它们的配置草稿 */
const modules = ref<ModuleInfo[]>([])
const draftSettings = ref<Record<string, Record<string, ModuleSettingValue>>>({})

/**
 * 需要在这里展示的模块
 *
 * 只列"已启用且声明了配置项"的功能: 没参数的功能(如看板娘)在系统设置里无事可做,
 * 被禁用的功能也不该出现它的参数 - 开关都在"模块管理"里
 */
const configurableModules = computed(() => modules.value.filter((item) => item.enabled && item.settings.length > 0))

/** 序列化当前表单, 用于和快照比较 */
function currentSnapshot(): string {
  return JSON.stringify(form.value)
}

/**
 * 两个配置值是否相同
 *
 * 行列表要按内容比较: 编辑一次就换了引用, 只比引用会让"有未保存的改动"一直亮着
 */
function sameSettingValue(a: ModuleSettingValue | undefined, b: ModuleSettingValue | undefined): boolean {
  if (Array.isArray(a) || Array.isArray(b)) return JSON.stringify(a) === JSON.stringify(b)
  return a === b
}

/** 配置被改过的模块 id(保存时只提交这些) */
const dirtyModuleIds = computed(() =>
  configurableModules.value
    .filter((item) =>
      item.settings.some((setting) => !sameSettingValue(draftSettings.value[item.id]?.[setting.key], setting.value)),
    )
    .map((item) => item.id),
)

/** 是否存在未保存的修改 */
const dirty = computed(() => currentSnapshot() !== snapshot.value || dirtyModuleIds.value.length > 0)

/** 把后端返回的模块清单写进草稿 */
function resetModuleDraft(list: ModuleInfo[]) {
  modules.value = list
  draftSettings.value = Object.fromEntries(
    list.map((item) => [item.id, Object.fromEntries(item.settings.map((setting) => [setting.key, setting.value]))]),
  )
}

/**
 * 写入某项模块配置的草稿值
 *
 * @param id 模块 id
 * @param key 配置键
 * @param value 新值
 */
function updateSetting(id: string, key: string, value: ModuleSettingValue) {
  draftSettings.value[id] = { ...draftSettings.value[id], [key]: value }
}

async function load() {
  const [settings, moduleData] = await Promise.all([settingsApi.all(), modulesApi.admin()])
  /*
   * 原地更新而不是整体替换: 各子卡片拿到的是同一个表单对象,
   * 替换对象会让它们继续指向旧值(表现为卡片里全是空的)
   */
  Object.assign(form.value, {
    site_name: settings.site_name || '',
    site_title: settings.site_title || '',
    site_desc: settings.site_desc || '',
    site_icon: settings.site_icon || '',
    site_bio: settings.site_bio || '',
    max_upload_size_mb: Number(settings.max_upload_size_mb) || UPLOAD_SIZE_DEFAULT_MB,
  })
  snapshot.value = currentSnapshot()
  resetModuleDraft(moduleData.modules)
}

async function uploadIcon(file: File) {
  uploadingIcon.value = true
  try {
    const media = await mediaApi.upload(file)
    form.value.site_icon = media.url
    ElMessage.success('图标已上传')
  } finally {
    uploadingIcon.value = false
  }
}

async function save() {
  saving.value = true
  try {
    await settingsApi.update({
      ...form.value,
      max_upload_size_mb: Number(form.value.max_upload_size_mb) || UPLOAD_SIZE_DEFAULT_MB,
    })
    // 模块参数走模块接口: 与站点级设置分开保存, 校验规则也归各自的模块
    const ids = dirtyModuleIds.value
    if (ids.length) {
      const payload = Object.fromEntries(ids.map((id) => [id, { settings: draftSettings.value[id] }]))
      const data = await modulesApi.update(payload)
      // 用服务端返回的值回填草稿: 行列表会被补齐列, 回填后界面与库里一致
      resetModuleDraft(data.modules)
      // 前台按"公开模块状态"渲染, 不强制刷新的话同一个会话里前台还是旧配置,
      // 表现就是"后台保存了但前台没变化"
      await moduleStore.load(true)
    }
    snapshot.value = currentSnapshot()
    ElMessage.success('设置已保存')
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<template>
  <div>
    <h2>系统设置</h2>

    <!-- 页眉与其它后台页保持一致: h2 独占一行, 下面是"左侧说明 + 右侧操作"的工具条 -->
    <div class="admin-toolbar">
      <div class="admin-toolbar-filters">
        <span class="muted">
          <template v-if="dirty">有未保存的修改</template>
          <template v-else>所有修改都已保存</template>
        </span>
      </div>
      <div class="admin-toolbar-actions">
        <el-button type="primary" :loading="saving" @click="save">保存设置</el-button>
      </div>
    </div>

    <div class="settings-cards">
      <SiteBasicCard :form="form" :uploading-icon="uploadingIcon" :upload-icon="uploadIcon" />

      <p v-if="configurableModules.length" class="muted settings-hint">
        下面几块是已启用功能的参数; 功能的开启与关闭在
        <router-link to="/admin/modules">模块管理</router-link> 里调整
      </p>

      <!-- 每个已启用且声明了参数的功能一块, 顺序与模块管理一致(分类 -> id) -->
      <section v-for="item in configurableModules" :key="item.id" class="card">
        <h3>
          {{ item.name }} <code class="module-id">{{ item.id }}</code>
        </h3>
        <p class="muted section-hint">{{ item.description }}</p>
        <div class="module-settings-grid">
          <ModuleSettingField
            v-for="setting in item.settings"
            :key="setting.key"
            :setting="setting"
            :value="draftSettings[item.id]?.[setting.key]"
            @update:value="(value: ModuleSettingValue) => updateSetting(item.id, setting.key, value)"
          />
        </div>
      </section>

      <UploadCard :form="form" />
    </div>
  </div>
</template>

<style scoped>
/* 每张卡片一个配置域, 卡片间距与个人资料页保持一致 */
.settings-cards {
  display: grid;
  gap: 20px;
}

.settings-hint {
  margin: 0;
  font-size: 13px;
}

.module-id {
  font-family: var(--font-mono);
  font-size: 11.5px;
  color: var(--muted);
  background: var(--code-bg);
  border-radius: var(--radius-chip);
  padding: 1px 7px;
}

/* 模块参数: 与页面其它卡片一致的两列排布(多行文本与行列表由字段组件自己占满整行) */
.module-settings-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 12px 24px;
}
</style>
