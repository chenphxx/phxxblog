<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { usePostEditor } from '@/composables/usePostEditor'
import PostFormFields from '@/components/PostFormFields.vue'

const router = useRouter()
const formRef = ref<InstanceType<typeof PostFormFields> | null>(null)
const editor = usePostEditor({
  // 后台编辑器点"取消"回到文章管理列表
  cancelFallback: () => router.push('/admin/posts'),
})

/** 保存前先把编辑器里的正文同步进表单(理由见 PostFormFields.syncContent) */
function save(targetStatus?: number) {
  formRef.value?.syncContent()
  return editor.save(targetStatus)
}
</script>

<template>
  <div>
    <h2>{{ editor.isEdit ? '编辑文章' : '新建文章' }}</h2>

    <div class="admin-toolbar">
      <div class="admin-toolbar-actions">
        <el-button @click="editor.cancel">取消</el-button>
        <el-button :loading="editor.saving" @click="save(0)">存草稿</el-button>
        <el-button type="primary" :loading="editor.saving" @click="save()">保存</el-button>
        <el-button v-if="editor.isEdit" type="danger" plain @click="editor.removePost">删除</el-button>
      </div>
    </div>

    <div class="card">
      <PostFormFields ref="formRef" :editor="editor" />
    </div>
  </div>
</template>
