<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { chronicleApi, mediaApi } from '@/api'
import VditorEditor from '@/components/VditorEditor.vue'

const route = useRoute()
const router = useRouter()
const editorRef = ref<InstanceType<typeof VditorEditor> | null>(null)
const loading = ref(false)
const saving = ref(false)
const uploadingCover = ref(false)

const form = reactive({
  title: '',
  summary: '',
  cover_image: '',
  content_md: '',
})

const currentId = computed(() => Number(route.params.id) || 0)
const isEdit = computed(() => currentId.value > 0)

function resetForm() {
  form.title = ''
  form.summary = ''
  form.cover_image = ''
  form.content_md = ''
}

async function load() {
  if (!isEdit.value) {
    resetForm()
    return
  }
  loading.value = true
  try {
    const item = await chronicleApi.detail(currentId.value)
    form.title = item.title
    form.summary = item.summary
    form.cover_image = item.cover_image || ''
    form.content_md = item.content_md
  } finally {
    loading.value = false
  }
}

watch(currentId, load, { immediate: true })

async function uploadCover(options: { file: File }) {
  uploadingCover.value = true
  try {
    const media = await mediaApi.upload(options.file)
    form.cover_image = media.url
    ElMessage.success('封面上传成功')
  } finally {
    uploadingCover.value = false
  }
}

async function save() {
  // 中文输入法组字期间 v-model 可能落后于编辑器, 保存时直接读取编辑器内容
  form.content_md = editorRef.value?.getValue() ?? form.content_md
  if (!form.title.trim()) {
    ElMessage.warning('请填写纪事标题')
    return
  }
  if (!form.summary.trim()) {
    ElMessage.warning('请填写卡片概览')
    return
  }
  if (!form.content_md.trim()) {
    ElMessage.warning('请填写纪事正文')
    return
  }

  saving.value = true
  try {
    const payload = {
      title: form.title.trim(),
      summary: form.summary.trim(),
      cover_image: form.cover_image.trim() || null,
      content_md: form.content_md,
    }
    if (isEdit.value) await chronicleApi.update(currentId.value, payload)
    else await chronicleApi.create(payload)
    ElMessage.success('纪事已保存')
    router.push('/admin/chronicles')
  } finally {
    saving.value = false
  }
}

async function remove() {
  await ElMessageBox.confirm(`确定删除《${form.title}》吗? 该操作不可恢复。`, '删除纪事', {
    type: 'warning',
    confirmButtonText: '删除',
  })
  await chronicleApi.remove(currentId.value)
  ElMessage.success('已删除')
  router.push('/admin/chronicles')
}
</script>

<template>
  <div v-loading="loading" class="edit-page">
    <h2>{{ isEdit ? '编辑纪事' : '新增纪事' }}</h2>

    <div class="admin-toolbar">
      <div class="admin-toolbar-filters">
        <span class="muted">用封面、标题与概览组织杂志卡片, 正文支持 Markdown</span>
      </div>
      <div class="admin-toolbar-actions">
        <el-button @click="router.push('/admin/chronicles')">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">保存纪事</el-button>
        <el-button v-if="isEdit" type="danger" plain @click="remove">删除</el-button>
      </div>
    </div>

    <div class="card edit-card">
      <el-form label-position="top">
        <el-form-item label="标题">
          <el-input v-model="form.title" placeholder="给这段纪事一个标题" maxlength="200" show-word-limit />
        </el-form-item>

        <el-form-item label="卡片概览">
          <el-input
            v-model="form.summary"
            type="textarea"
            :rows="3"
            placeholder="用一两句话概括人物或事件, 将显示在前台卡片中"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="封面图(可上传或填写 URL)">
          <div class="cover-field">
            <div class="cover-input-row">
              <el-input v-model="form.cover_image" placeholder="/assets/uploads/... 或 https://..." />
              <el-upload :show-file-list="false" :http-request="uploadCover" accept="image/*">
                <el-button :loading="uploadingCover">本地上传</el-button>
              </el-upload>
            </div>
            <div v-if="form.cover_image" class="cover-preview">
              <img :src="form.cover_image" alt="纪事封面预览" />
            </div>
          </div>
        </el-form-item>

        <el-form-item class="content-field" label="正文(Markdown, 支持图片/视频/附件/代码高亮)">
          <VditorEditor ref="editorRef" v-model="form.content_md" />
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<style scoped>
.edit-page {
  display: flex;
  min-height: 100%;
  flex-direction: column;
}

.edit-card {
  display: flex;
  flex: 1;
  flex-direction: column;
}

.el-form {
  display: flex;
  flex: 1;
  flex-direction: column;
}

.content-field,
.content-field :deep(.el-form-item__content) {
  display: flex;
  flex: 1;
  flex-direction: column;
}

.cover-field {
  display: flex;
  width: 100%;
  flex-direction: column;
  gap: var(--space-3);
}

.cover-input-row {
  display: flex;
  width: 100%;
  gap: var(--space-3);
}

.cover-input-row .el-input {
  flex: 1;
}

.cover-preview {
  width: min(100%, 560px);
  aspect-ratio: 16 / 8;
  overflow: hidden;
  border: 1px solid var(--border);
  border-radius: var(--radius-control);
  background: var(--code-bg);
}

.cover-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

@media (max-width: 600px) {
  .cover-input-row {
    flex-direction: column;
  }
}
</style>
