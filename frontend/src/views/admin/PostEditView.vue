<script setup lang="ts">
import { useRouter } from 'vue-router'
import { usePostEditor } from '@/composables/usePostEditor'
import PostFormFields from '@/components/PostFormFields.vue'

const router = useRouter()
const editor = usePostEditor({
  // 后台编辑器点"取消"回到文章管理列表
  cancelFallback: () => router.push('/admin/posts'),
})
</script>

<template>
  <div>
    <div class="toolbar">
      <h2 style="margin: 0">{{ editor.isEdit ? '编辑文章' : '新建文章' }}</h2>
      <div>
        <el-button @click="editor.cancel">取消</el-button>
        <el-button :loading="editor.saving" @click="editor.save(0)">存草稿</el-button>
        <el-button type="primary" :loading="editor.saving" @click="editor.save()">保存</el-button>
        <el-button v-if="editor.isEdit" type="danger" plain @click="editor.removePost">删除</el-button>
      </div>
    </div>

    <div class="card" style="margin-top: 16px">
      <PostFormFields :editor="editor" />
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
