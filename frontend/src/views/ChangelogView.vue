<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { miscApi } from '@/api'
import MarkdownView from '@/components/MarkdownView.vue'
import VditorEditor from '@/components/VditorEditor.vue'

const content = ref('')
const loading = ref(true)
const saving = ref(false)
const editing = ref(false)

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
  <div class="page-container" v-loading="loading">
    <div class="changelog-header">
      <h1 style="margin: 0">更新日志</h1>
      <div v-if="!editing">
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
