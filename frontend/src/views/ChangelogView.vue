<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { miscApi } from '@/api'
import MarkdownView from '@/components/MarkdownView.vue'
import VditorEditor from '@/components/VditorEditor.vue'
import { useAuthStore } from '@/stores/auth'

const content = ref('')
const loading = ref(true)
const saving = ref(false)
const editing = ref(false)
const auth = useAuthStore()

/**
 * 是否能编辑更新日志
 * 保存接口要求 changelog:manage 权限, 而项目里只有管理员角色持有它 - 前台按管理员
 * 身份显示编辑入口; 更新日志配成公开时访客仍能阅读, 但看不到编辑按钮
 */
const canEdit = computed(() => auth.user?.role_codes.includes('admin') ?? false)

async function load() {
  loading.value = true
  try {
    content.value = (await miscApi.changelog()).content
  } finally {
    loading.value = false
  }
}

function startEdit() {
  editing.value = true
}

function cancelEdit() {
  editing.value = false
  load()
}

async function save() {
  saving.value = true
  try {
    await miscApi.updateChangelog(content.value)
    ElMessage.success('更新日志已保存')
    editing.value = false
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<template>
  <div v-loading="loading" class="page-container">
    <div class="changelog-header">
      <div>
        <p class="eyebrow" style="margin: 0 0 4px">changelog — 更新日志</p>
        <h1 style="margin: 0">更新日志</h1>
      </div>
      <div v-if="!editing && canEdit">
        <el-button type="primary" @click="startEdit">编辑</el-button>
      </div>
      <div v-else>
        <el-button @click="cancelEdit">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">保存</el-button>
      </div>
    </div>

    <template v-if="editing">
      <div class="card" style="margin-top: 16px">
        <VditorEditor v-model="content" :height="700" />
      </div>
    </template>
    <template v-else>
      <MarkdownView :content="content" />
    </template>
  </div>
</template>

<style scoped>
.changelog-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
</style>
