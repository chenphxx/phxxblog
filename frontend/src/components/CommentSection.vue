<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { commentApi } from '@/api'
import { useAuthStore } from '@/stores/auth'
import type { CommentItem } from '@/types'
import CommentNode from './CommentNode.vue'

const props = defineProps<{ postId: number }>()
const auth = useAuthStore()

const comments = ref<CommentItem[]>([])
const loading = ref(false)
const form = ref({
  content: '',
  author_name: '',
  author_email: '',
  parent_id: null as number | null,
})
const replyingTo = ref<CommentItem | null>(null)

// 编辑状态
const editDialog = ref(false)
const editContent = ref('')
const editingComment = ref<CommentItem | null>(null)
const savingEdit = ref(false)

async function load() {
  loading.value = true
  try {
    comments.value = await commentApi.list(props.postId)
  } finally {
    loading.value = false
  }
}

async function submit() {
  if (!form.value.content.trim()) {
    ElMessage.warning('请输入评论内容')
    return
  }
  try {
    await commentApi.create(props.postId, {
      content: form.value.content.trim(),
      parent_id: form.value.parent_id,
      author_name: auth.user ? undefined : form.value.author_name,
      author_email: auth.user ? undefined : form.value.author_email,
    })
    ElMessage.success('评论成功')
    form.value.content = ''
    form.value.parent_id = null
    replyingTo.value = null
    load()
  } catch {
    // 错误提示由拦截器统一处理
  }
}

function reply(comment: CommentItem) {
  replyingTo.value = comment
  form.value.parent_id = comment.id
  document.getElementById('comment-form')?.scrollIntoView({ behavior: 'smooth' })
}

function cancelReply() {
  replyingTo.value = null
  form.value.parent_id = null
}

function openEdit(comment: CommentItem) {
  editingComment.value = comment
  editContent.value = comment.content
  editDialog.value = true
}

async function saveEdit() {
  if (!editingComment.value || !editContent.value.trim()) {
    ElMessage.warning('评论内容不能为空')
    return
  }
  savingEdit.value = true
  try {
    await commentApi.update(editingComment.value.id, { content: editContent.value.trim() })
    ElMessage.success('评论已更新')
    editDialog.value = false
    load()
  } finally {
    savingEdit.value = false
  }
}

async function removeComment(comment: CommentItem) {
  await ElMessageBox.confirm('确定删除这条评论吗? 其下的回复会一并删除。', '删除确认', {
    type: 'warning',
    confirmButtonText: '删除',
  })
  await commentApi.remove(comment.id)
  ElMessage.success('评论已删除')
  load()
}

onMounted(load)
</script>

<template>
  <div class="comment-section card">
    <h3>评论 ({{ comments.length }})</h3>

    <!-- 发表评论 -->
    <div id="comment-form" class="comment-form">
      <el-alert
        v-if="replyingTo"
        :title="`正在回复 @${replyingTo.author_name || '匿名'}`"
        type="info"
        closable
        @close="cancelReply"
        style="margin-bottom: 12px"
      />
      <div v-if="!auth.user" class="guest-fields">
        <el-input v-model="form.author_name" placeholder="昵称(必填)" style="max-width: 200px" />
        <el-input v-model="form.author_email" placeholder="邮箱(选填)" style="max-width: 240px" />
      </div>
      <el-input
        v-model="form.content"
        type="textarea"
        :rows="3"
        placeholder="友善评论, 支持链接/图片/附件描述..."
        maxlength="2000"
        show-word-limit
      />
      <div class="form-actions">
        <el-button type="primary" @click="submit">发表评论</el-button>
      </div>
    </div>

    <!-- 评论列表(递归渲染任意层级回复) -->
    <div v-loading="loading" class="comment-list">
      <div v-if="comments.length === 0" class="muted" style="padding: 16px 0">还没有评论, 来抢沙发吧~</div>
      <CommentNode
        v-for="comment in comments"
        :key="comment.id"
        :comment="comment"
        :depth="0"
        @reply="reply"
        @edit="openEdit"
        @delete="removeComment"
      />
    </div>

    <!-- 编辑评论 -->
    <el-dialog v-model="editDialog" title="编辑评论" width="520px">
      <el-input v-model="editContent" type="textarea" :rows="4" maxlength="2000" show-word-limit />
      <template #footer>
        <el-button @click="editDialog = false">取消</el-button>
        <el-button type="primary" :loading="savingEdit" @click="saveEdit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.comment-section {
  margin-top: 24px;
}
.comment-form {
  margin-bottom: 20px;
}
.guest-fields {
  display: flex;
  gap: 12px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}
.form-actions {
  margin-top: 12px;
  text-align: right;
}
</style>
