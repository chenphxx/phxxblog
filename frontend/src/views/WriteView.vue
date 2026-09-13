<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { usePostEditor } from '@/composables/usePostEditor'
import PostFormFields from '@/components/PostFormFields.vue'

const router = useRouter()
const formRef = ref<InstanceType<typeof PostFormFields> | null>(null)
const editor = usePostEditor({
  // 从博客页进入时"取消"应回到上一页, 而不是跳去后台
  cancelFallback: () => router.back(),
  removeConfirmText: '确定删除这篇文章吗? 将移入回收站, 可在后台恢复。',
})

/** 保存前先把编辑器里的正文同步进表单(理由见 PostFormFields.syncContent) */
function save(targetStatus?: number) {
  formRef.value?.syncContent()
  return editor.save(targetStatus)
}
</script>

<template>
  <div class="page-container">
    <div class="write-header">
      <div>
        <p class="eyebrow" style="margin: 0 0 4px">editor — {{ editor.isEdit ? '编辑文章' : '写文章' }}</p>
        <h1 style="margin: 0">{{ editor.isEdit ? '编辑文章' : '写文章' }}</h1>
      </div>
      <div>
        <el-button @click="editor.cancel">取消</el-button>
        <el-button :loading="editor.saving" @click="save(0)">保存草稿</el-button>
        <el-button :loading="editor.saving" @click="save(1)">提交审核</el-button>
        <el-button type="success" :loading="editor.saving" @click="save()">
          {{ editor.form.public_visible ? '发布' : '保存为私密' }}
        </el-button>
        <el-button v-if="editor.isEdit" type="danger" plain @click="editor.removePost">删除</el-button>
      </div>
    </div>

    <div class="card" style="margin-top: 16px">
      <PostFormFields ref="formRef" :editor="editor" />
    </div>
  </div>
</template>

<style scoped>
.write-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
}
</style>
