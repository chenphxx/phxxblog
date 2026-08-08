<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { categoryApi, mediaApi, postApi, tagApi } from '@/api'
import type { Category, PostDetail, Tag } from '@/types'
import VditorEditor from '@/components/VditorEditor.vue'

const route = useRoute()
const router = useRouter()
const isEdit = ref(Boolean(route.params.id))
const postId = ref(Number(route.params.id) || 0)
const categories = ref<Category[]>([])
const tags = ref<Tag[]>([])
const saving = ref(false)
const uploadingCover = ref(false)

const form = ref({
  title: '',
  slug: '',
  summary: '',
  content_md: '',
  cover_image: '',
  category_id: null as number | null,
  tag_ids: [] as number[],
  status: 0,
  public_visible: true,
})

async function loadOptions() {
  categories.value = await categoryApi.list()
  tags.value = await tagApi.list()
}

async function loadPost() {
  if (!isEdit.value) return
  const post = (await postApi.detail(postId.value)) as PostDetail
  form.value = {
    title: post.title,
    slug: post.slug,
    summary: post.summary || '',
    content_md: post.content_md,
    cover_image: post.cover_image || '',
    category_id: post.category?.id || null,
    tag_ids: post.tags.map((t) => t.id),
    status: post.status,
    public_visible: post.status !== 3,
  }
}

async function createCategory(name: string) {
  const created = await categoryApi.create({ name, slug: name })
  categories.value.push(created)
  return created.id
}

async function createTag(name: string) {
  const created = await tagApi.create({ name, slug: name })
  tags.value.push(created)
  return created.id
}

async function onCategoryChange(value: unknown) {
  if (typeof value === 'string' && value.trim()) {
    form.value.category_id = await createCategory(value.trim())
    ElMessage.success('分类已创建')
  }
}

async function onTagsChange(values: unknown) {
  if (!Array.isArray(values)) return
  const ids: number[] = []
  for (const value of values) {
    if (typeof value === 'string' && value.trim()) {
      ids.push(await createTag(value.trim()))
    } else if (typeof value === 'number') {
      ids.push(value)
    }
  }
  form.value.tag_ids = ids
}

async function uploadCover(options: { file: File }) {
  uploadingCover.value = true
  try {
    const media = await mediaApi.upload(options.file)
    form.value.cover_image = media.url
    ElMessage.success('封面已上传')
  } finally {
    uploadingCover.value = false
  }
}

async function save(targetStatus?: number) {
  if (!form.value.title.trim()) {
    ElMessage.warning('请填写标题')
    return
  }
  saving.value = true
  try {
  const payload = {
    ...form.value,
    status: targetStatus ?? (form.value.public_visible ? 2 : 3),
  }
    if (isEdit.value) {
      await postApi.update(postId.value, payload)
    } else {
      const created = await postApi.create(payload)
      postId.value = created.id
      isEdit.value = true
    }
    ElMessage.success('保存成功')
    router.push('/admin/posts')
  } finally {
    saving.value = false
  }
}

function cancel() {
  if (isEdit.value) {
    router.push(`/post/${postId.value}`)
  } else {
    router.push('/admin/posts')
  }
}

async function removePost() {
  await ElMessageBox.confirm('确定删除这篇文章吗? 将移入回收站, 可在文章管理中恢复。', '删除确认', {
    type: 'warning',
    confirmButtonText: '删除',
  })
  await postApi.trash(postId.value)
  ElMessage.success('已删除')
  router.push('/admin/posts')
}

onMounted(async () => {
  await loadOptions()
  await loadPost()
})
</script>

<template>
  <div>
    <div class="toolbar">
      <h2 style="margin: 0">{{ isEdit ? '编辑文章' : '新建文章' }}</h2>
      <div>
        <el-button @click="cancel">取消</el-button>
        <el-button :loading="saving" @click="save(0)">存草稿</el-button>
        <el-button type="primary" :loading="saving" @click="save()">保存</el-button>
        <el-button v-if="isEdit" type="danger" plain @click="removePost">删除</el-button>
      </div>
    </div>

    <div class="card" style="margin-top: 16px">
      <el-form label-position="top">
        <el-row :gutter="16">
          <el-col :span="16">
            <el-form-item label="标题">
              <el-input v-model="form.title" placeholder="文章标题" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="别名(slug, 留空自动生成)">
              <el-input v-model="form.slug" placeholder="post-xxxx" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="摘要">
          <el-input v-model="form.summary" type="textarea" :rows="2" maxlength="500" show-word-limit />
        </el-form-item>

        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="分类">
              <el-select
                v-model="form.category_id"
                filterable
                allow-create
                default-first-option
                :reserve-keyword="false"
                clearable
                placeholder="选择或输入新分类"
                style="width: 100%"
                @change="onCategoryChange"
              >
                <el-option v-for="cat in categories" :key="cat.id" :label="cat.name" :value="cat.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="标签">
              <el-select
                v-model="form.tag_ids"
                multiple
                filterable
                allow-create
                default-first-option
                :reserve-keyword="false"
                clearable
                placeholder="选择或输入新标签"
                style="width: 100%"
                @change="onTagsChange"
              >
                <el-option v-for="tag in tags" :key="tag.id" :label="tag.name" :value="tag.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="是否公开可见">
              <el-switch
                v-model="form.public_visible"
                active-text="公开可见"
                inactive-text="仅管理员可见"
                inline-prompt
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="封面图 URL">
          <div style="display: flex; gap: 12px; width: 100%">
            <el-input v-model="form.cover_image" placeholder="https://... 或 /assets/uploads/..." style="flex: 1" />
            <el-upload :show-file-list="false" :http-request="uploadCover" accept="image/*">
              <el-button :loading="uploadingCover">本地上传</el-button>
            </el-upload>
          </div>
        </el-form-item>

        <el-form-item label="正文(Markdown)">
          <VditorEditor v-model="form.content_md" />
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<style scoped>
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
}
</style>
