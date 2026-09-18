<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { userApi } from '@/api'
import type { Role, User } from '@/types'
import { useAuthStore } from '@/stores/auth'
import { usePagedList } from '@/composables/usePagedList'

const auth = useAuthStore()

const roles = ref<Role[]>([])
const keyword = ref('')
/**
 * 列表分页与取数。
 * 角色列表跟着每次加载一起取: 用户对话框要选角色, 只在挂载时取一次的话,
 * 在别处改过角色后这里拿到的还是旧的。
 */
const { items: users, total, page, pageSize, loading, load, reset } = usePagedList<User>({
  fetch: async (page, pageSize) => {
    const [userData, roleData] = await Promise.all([
      userApi.list({ page, page_size: pageSize, keyword: keyword.value || undefined }),
      userApi.roles(),
    ])
    roles.value = roleData
    return userData
  },
})

const dialog = ref(false)
const resetDialog = ref(false)
const resetForm = ref({ id: 0, username: '', password: '' })
const form = ref({
  id: 0,
  username: '',
  email: '',
  password: '',
  nickname: '',
  roles: [] as string[],
  status: 1,
})

function openDialog(user?: User) {
  form.value = user
    ? {
        id: user.id,
        username: user.username,
        email: user.email,
        password: '',
        nickname: user.nickname,
        roles: user.role_codes,
        status: user.status,
      }
    : { id: 0, username: '', email: '', password: '', nickname: '', roles: [], status: 1 }
  dialog.value = true
}

async function save() {
  const payload = {
    username: form.value.username,
    nickname: form.value.nickname,
    email: form.value.email,
    roles: form.value.roles,
    status: form.value.status,
  }
  if (form.value.id) {
    await userApi.update(form.value.id, payload)
    // 改的可能就是当前登录账号: 同步一次会话里的用户信息, 让个人资料页立刻生效
    if (form.value.id === auth.user?.id) {
      await auth.fetchMe().catch(() => {})
    }
  } else {
    await userApi.create({
      username: form.value.username,
      email: form.value.email,
      password: form.value.password,
      nickname: form.value.nickname,
      roles: form.value.roles,
    })
  }
  ElMessage.success('保存成功')
  dialog.value = false
  load()
}

async function remove(user: User) {
  await ElMessageBox.confirm(`删除用户「${user.username}」?`, '确认', { type: 'warning' })
  await userApi.remove(user.id)
  ElMessage.success('删除成功')
  load()
}

function openReset(user: User) {
  resetForm.value = { id: user.id, username: user.username, password: '' }
  resetDialog.value = true
}

async function resetPassword() {
  if (!resetForm.value.password) {
    ElMessage.warning('请输入新密码')
    return
  }
  if (resetForm.value.password.length < 6) {
    ElMessage.warning('密码至少 6 位')
    return
  }
  await userApi.resetPassword(resetForm.value.id, resetForm.value.password)
  ElMessage.success('密码已重置')
  resetDialog.value = false
}
</script>

<template>
  <div>
    <h2>用户管理</h2>

    <div class="admin-toolbar">
      <div class="admin-toolbar-actions">
        <el-input
          v-model="keyword"
          placeholder="搜索用户名/昵称/邮箱"
          clearable
          @keyup.enter="reset()"
          @clear="reset()"
        />
        <el-button @click="reset()">搜索</el-button>
        <el-button type="primary" @click="openDialog()">新增用户</el-button>
      </div>
    </div>

    <div class="card">
      <el-table :data="users" v-loading="loading">
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="username" label="用户名" width="120" />
        <el-table-column prop="nickname" label="昵称" width="120" />
        <el-table-column prop="email" label="邮箱" min-width="180" />
        <el-table-column label="角色" width="180">
          <template #default="{ row }">
            <el-tag v-for="code in row.role_codes" :key="code" size="small" style="margin-right: 4px">
              {{ code }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag size="small" :type="row.status === 1 ? 'success' : 'danger'">
              {{ row.status === 1 ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="250">
          <template #default="{ row }">
            <!-- el-table 插槽的 row 是 DefaultRow, 显式断言成实际行类型 -->
            <div class="op-row">
              <el-button size="small" @click="openDialog(row as User)">编辑</el-button>
              <el-button size="small" type="warning" @click="openReset(row as User)">重置密码</el-button>
              <el-button size="small" type="danger" @click="remove(row as User)">删除</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination
        v-if="total > pageSize"
        v-model:current-page="page"
        :page-size="pageSize"
        :total="total"
        layout="prev, pager, next, total"
        style="justify-content: center; margin-top: 16px"
      />
    </div>

    <el-dialog v-model="dialog" :title="form.id ? '编辑用户' : '新增用户'" width="480px">
      <el-form label-position="top">
        <el-form-item label="用户名">
          <el-input v-model="form.username" />
        </el-form-item>
        <el-form-item label="邮箱"><el-input v-model="form.email" /></el-form-item>
        <el-form-item v-if="!form.id" label="密码">
          <el-input v-model="form.password" type="password" show-password />
        </el-form-item>
        <el-form-item label="昵称"><el-input v-model="form.nickname" /></el-form-item>
        <el-form-item label="角色">
          <el-select v-model="form.roles" multiple style="width: 100%">
            <el-option v-for="role in roles" :key="role.code" :label="`${role.name} (${role.code})`" :value="role.code" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="form.status" :active-value="1" :inactive-value="0" active-text="启用" inactive-text="禁用" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="resetDialog" title="重置密码" width="420px">
      <el-form label-position="top" @submit.prevent>
        <el-form-item label="用户名">
          <el-input :model-value="resetForm.username" disabled />
        </el-form-item>
        <el-form-item label="新密码">
          <el-input
            v-model="resetForm.password"
            type="password"
            show-password
            placeholder="至少 6 位"
            @keyup.enter="resetPassword"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="resetDialog = false">取消</el-button>
        <el-button type="primary" @click="resetPassword">确认重置</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.op-row {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: nowrap;
  white-space: nowrap;
}
.op-row .el-button {
  margin-left: 0;
}
</style>
