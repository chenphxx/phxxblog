<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { userApi } from '@/api'
import type { Role, User } from '@/types'

const users = ref<User[]>([])
const roles = ref<Role[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 10
const keyword = ref('')
const loading = ref(false)

const dialog = ref(false)
const form = ref({
  id: 0,
  username: '',
  email: '',
  password: '',
  nickname: '',
  roles: [] as string[],
  status: 1,
})

async function load() {
  loading.value = true
  try {
    const [userData, roleData] = await Promise.all([
      userApi.list({ page: page.value, page_size: pageSize, keyword: keyword.value || undefined }),
      userApi.roles(),
    ])
    users.value = userData.items
    total.value = userData.total
    roles.value = roleData
  } finally {
    loading.value = false
  }
}

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
    nickname: form.value.nickname,
    email: form.value.email,
    roles: form.value.roles,
    status: form.value.status,
  }
  if (form.value.id) {
    await userApi.update(form.value.id, payload)
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

onMounted(load)
</script>

<template>
  <div>
    <div class="toolbar">
      <h2 style="margin: 0">用户管理</h2>
      <div>
        <el-input v-model="keyword" placeholder="搜索用户名/昵称/邮箱" style="max-width: 220px; margin-right: 8px" clearable @keyup.enter="page = 1; load()" @clear="page = 1; load()" />
        <el-button @click="page = 1; load()">搜索</el-button>
        <el-button type="primary" @click="openDialog()">新增用户</el-button>
      </div>
    </div>

    <div class="card" style="margin-top: 16px">
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
        <el-table-column label="操作" width="140">
          <template #default="{ row }">
            <el-button size="small" @click="openDialog(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="remove(row)">删除</el-button>
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
        @current-change="load"
      />
    </div>

    <el-dialog v-model="dialog" :title="form.id ? '编辑用户' : '新增用户'" width="480px">
      <el-form label-position="top">
        <el-form-item label="用户名">
          <el-input v-model="form.username" :disabled="Boolean(form.id)" />
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
