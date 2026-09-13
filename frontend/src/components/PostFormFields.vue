<script setup lang="ts">
/**
 * 文章表单字段(标题/别名/摘要/分类/标签/可见性/封面/正文)。
 *
 * WriteView 与 admin/PostEditView 共用: 状态由 usePostEditor 持有并通过 editor 传入,
 * 本组件只负责渲染与事件转发, 不持有任何表单状态。
 * editor 是稳定的 reactive 对象, 因此这里直接引用 props.editor 而不是解构。
 */
import { ref } from 'vue'
import type { PostEditorState } from '@/composables/usePostEditor'
import VditorEditor from '@/components/VditorEditor.vue'

const props = defineProps<{ editor: PostEditorState }>()
const editor = props.editor

const contentEditor = ref<InstanceType<typeof VditorEditor> | null>(null)

/**
 * 取正文的"当前真相"并写回表单。
 *
 * 保存前必须调用: 中文输入法组字期间 Vditor 不回调 input, v-model 可能落后于编辑器,
 * 直接用 form.content_md 会丢掉最后输入的内容(见 VditorEditor.getValue 的说明)。
 */
function syncContent() {
  const value = contentEditor.value?.getValue()
  if (typeof value === 'string') {
    editor.form.content_md = value
  }
}

defineExpose({ syncContent })
</script>

<template>
  <el-form label-position="top">
    <el-row :gutter="16">
      <el-col :span="16">
        <el-form-item label="标题">
          <el-input v-model="editor.form.title" placeholder="文章标题" maxlength="200" show-word-limit />
        </el-form-item>
      </el-col>
      <el-col :span="8">
        <el-form-item label="别名(留空自动生成)">
          <el-input v-model="editor.form.slug" placeholder="post-xxxx" />
        </el-form-item>
      </el-col>
    </el-row>

    <el-form-item label="摘要">
      <el-input v-model="editor.form.summary" type="textarea" :rows="2" maxlength="500" show-word-limit />
    </el-form-item>

    <el-row :gutter="16">
      <el-col :span="8">
        <el-form-item label="分类(可输入新增)">
          <el-select
            v-model="editor.form.category_id"
            filterable
            allow-create
            default-first-option
            :reserve-keyword="false"
            clearable
            placeholder="选择或输入新分类"
            style="width: 100%"
            @change="editor.onCategoryChange"
          >
            <el-option v-for="cat in editor.categories" :key="cat.id" :label="cat.name" :value="cat.id" />
          </el-select>
        </el-form-item>
      </el-col>
      <el-col :span="8">
        <el-form-item label="标签(可输入新增)">
          <el-select
            v-model="editor.form.tag_ids"
            multiple
            filterable
            allow-create
            default-first-option
            :reserve-keyword="false"
            clearable
            placeholder="选择或输入新标签"
            style="width: 100%"
            @change="editor.onTagsChange"
          >
            <el-option v-for="tag in editor.tags" :key="tag.id" :label="tag.name" :value="tag.id" />
          </el-select>
        </el-form-item>
      </el-col>
      <el-col :span="8">
        <el-form-item label="是否公开可见">
          <el-switch
            v-model="editor.form.public_visible"
            active-text="公开可见"
            inactive-text="仅管理员可见"
            inline-prompt
          />
        </el-form-item>
      </el-col>
    </el-row>

    <el-form-item label="封面图(可上传或填写 URL)">
      <div class="cover-row">
        <el-input v-model="editor.form.cover_image" placeholder="/assets/uploads/... 或 https://..." style="flex: 1" />
        <el-upload :show-file-list="false" :http-request="editor.uploadCover" accept="image/*">
          <el-button :loading="editor.uploadingCover">本地上传</el-button>
        </el-upload>
      </div>
    </el-form-item>

    <el-form-item label="正文(Markdown, 支持图片/视频/附件/代码高亮)">
      <VditorEditor ref="contentEditor" v-model="editor.form.content_md" />
    </el-form-item>
  </el-form>
</template>

<style scoped>
.cover-row {
  display: flex;
  gap: 12px;
  width: 100%;
}
</style>
