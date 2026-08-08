<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { categoryApi, tagApi } from '@/api'
import type { Category, Tag } from '@/types'

const tab = ref('category')
const categories = ref<Category[]>([])
const tags = ref<Tag[]>([])

const categoryForm = ref({ id: 0, name: '', slug: '', description: '', sort_order: 0 })
const categoryDialog = ref(false)
const tagForm = ref({ id: 0, name: '', slug: '' })
const tagDialog = ref(false)

async function load() {
  categories.value = await categoryApi.list()
  tags.value = await tagApi.list()
}

function openCategoryDialog(category?: Category) {
  categoryForm.value = category
    ? { id: category.id, name: category.name, slug: category.slug, description: category.description || '', sort_order: category.sort_order }
    : { id: 0, name: '', slug: '', description: '', sort_order: 0 }
  categoryDialog.value = true
}

async function saveCategory() {
  const payload = { ...categoryForm.value }
  if (payload.id) {
    await categoryApi.update(payload.id, payload)
  } else {
    await categoryApi.create(payload)
  }
  ElMessage.success('保存成功')
  categoryDialog.value = false
  load()
}

async function removeCategory(category: Category) {
  await ElMessageBox.confirm(`删除分类「${category.name}」? 文章将变为未分类。`, '确认', { type: 'warning' })
  await categoryApi.remove(category.id)
  ElMessage.success('删除成功')
  load()
}

function openTagDialog(tag?: Tag) {
  tagForm.value = tag ? { id: tag.id, name: tag.name, slug: tag.slug } : { id: 0, name: '', slug: '' }
  tagDialog.value = true
}

async function saveTag() {
  if (tagForm.value.id) {
    await tagApi.update(tagForm.value.id, tagForm.value)
  } else {
    await tagApi.create(tagForm.value)
  }
  ElMessage.success('保存成功')
  tagDialog.value = false
  load()
}

async function removeTag(tag: Tag) {
  await ElMessageBox.confirm(`删除标签「${tag.name}」?`, '确认', { type: 'warning' })
  await tagApi.remove(tag.id)
  ElMessage.success('删除成功')
  load()
}

onMounted(load)
</script>

<template>
  <div>
    <h2>分类与标签</h2>
    <el-tabs v-model="tab">
      <el-tab-pane label="分类" name="category">
        <div class="card">
          <div class="toolbar">
            <span class="muted">共 {{ categories.length }} 个分类</span>
            <el-button type="primary" @click="openCategoryDialog()">新增分类</el-button>
          </div>
          <el-table :data="categories">
            <el-table-column prop="name" label="名称" />
            <el-table-column prop="slug" label="别名" />
            <el-table-column prop="post_count" label="文章数" width="90" />
            <el-table-column prop="sort_order" label="排序" width="70" />
            <el-table-column prop="description" label="描述" min-width="160" show-overflow-tooltip />
            <el-table-column label="操作" width="140">
              <template #default="{ row }">
                <el-button size="small" @click="openCategoryDialog(row)">编辑</el-button>
                <el-button size="small" type="danger" @click="removeCategory(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-tab-pane>

      <el-tab-pane label="标签" name="tag">
        <div class="card">
          <div class="toolbar">
            <span class="muted">共 {{ tags.length }} 个标签</span>
            <el-button type="primary" @click="openTagDialog()">新增标签</el-button>
          </div>
          <el-table :data="tags">
            <el-table-column prop="name" label="名称" />
            <el-table-column prop="slug" label="别名" />
            <el-table-column prop="post_count" label="文章数" width="90" />
            <el-table-column label="操作" width="140">
              <template #default="{ row }">
                <el-button size="small" @click="openTagDialog(row)">编辑</el-button>
                <el-button size="small" type="danger" @click="removeTag(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-tab-pane>
    </el-tabs>

    <el-dialog v-model="categoryDialog" :title="categoryForm.id ? '编辑分类' : '新增分类'" width="480px">
      <el-form label-position="top">
        <el-form-item label="名称"><el-input v-model="categoryForm.name" /></el-form-item>
        <el-form-item label="别名"><el-input v-model="categoryForm.slug" /></el-form-item>
        <el-form-item label="描述"><el-input v-model="categoryForm.description" /></el-form-item>
        <el-form-item label="排序(小在前)"><el-input-number v-model="categoryForm.sort_order" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="categoryDialog = false">取消</el-button>
        <el-button type="primary" @click="saveCategory">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="tagDialog" :title="tagForm.id ? '编辑标签' : '新增标签'" width="420px">
      <el-form label-position="top">
        <el-form-item label="名称"><el-input v-model="tagForm.name" /></el-form-item>
        <el-form-item label="别名"><el-input v-model="tagForm.slug" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="tagDialog = false">取消</el-button>
        <el-button type="primary" @click="saveTag">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}
</style>
