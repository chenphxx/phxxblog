<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { authApi } from '@/api'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const profileForm = ref({ username: '', nickname: '' })
const passwordForm = ref({ old_password: '', new_password: '', confirm: '' })
const emailForm = ref({ email: '' })
const savingProfile = ref(false)
const savingPwd = ref(false)
const savingEmail = ref(false)

async function saveProfile() {
  if (!profileForm.value.username.trim()) {
    ElMessage.warning('用户名不能为空')
    return
  }
  savingProfile.value = true
  try {
    await authApi.updateProfile({
      username: profileForm.value.username.trim(),
      nickname: profileForm.value.nickname.trim(),
    })
    ElMessage.success('资料已更新')
    await auth.fetchMe()
  } finally {
    savingProfile.value = false
  }
}

async function changePassword() {
  if (passwordForm.value.new_password !== passwordForm.value.confirm) {
    ElMessage.warning('两次输入的密码不一致')
    return
  }
  savingPwd.value = true
  try {
    await authApi.changePassword({
      old_password: passwordForm.value.old_password,
      new_password: passwordForm.value.new_password,
    })
    ElMessage.success('密码修改成功, 下次登录请使用新密码')
    passwordForm.value = { old_password: '', new_password: '', confirm: '' }
  } finally {
    savingPwd.value = false
  }
}

async function changeEmail() {
  savingEmail.value = true
  try {
    await authApi.changeEmail(emailForm.value)
    ElMessage.success('邮箱修改成功')
    auth.fetchMe()
  } finally {
    savingEmail.value = false
  }
}

onMounted(() => {
  profileForm.value.username = auth.user?.username || ''
  profileForm.value.nickname = auth.user?.nickname || ''
})
</script>

<template>
  <div>
    <h2>个人资料</h2>

    <div class="card" style="margin-bottom: 20px">
      <h3>账号信息</h3>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="用户名">{{ auth.user?.username }}</el-descriptions-item>
        <el-descriptions-item label="昵称">{{ auth.user?.nickname }}</el-descriptions-item>
        <el-descriptions-item label="邮箱">{{ auth.user?.email }}</el-descriptions-item>
        <el-descriptions-item label="角色">
          <el-tag v-for="code in auth.user?.role_codes" :key="code" size="small" style="margin-right: 4px">
            {{ code }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="注册时间">{{ auth.user?.created_at.slice(0, 10) }}</el-descriptions-item>
      </el-descriptions>
    </div>

    <div class="card" style="margin-bottom: 20px">
      <h3>修改用户名/昵称</h3>
      <el-form label-position="top" style="max-width: 360px">
        <el-form-item label="用户名">
          <el-input v-model="profileForm.username" placeholder="用户名" />
        </el-form-item>
        <el-form-item label="昵称">
          <el-input v-model="profileForm.nickname" placeholder="昵称" />
        </el-form-item>
        <el-button type="primary" :loading="savingProfile" @click="saveProfile">保存资料</el-button>
      </el-form>
    </div>

    <div class="card" style="margin-bottom: 20px">
      <h3>修改邮箱</h3>
      <el-form label-position="top" style="max-width: 360px">
        <el-form-item label="新邮箱">
          <el-input v-model="emailForm.email" :placeholder="auth.user?.email" />
        </el-form-item>
        <el-button type="primary" :loading="savingEmail" @click="changeEmail">保存邮箱</el-button>
      </el-form>
    </div>

    <div class="card">
      <h3>修改密码</h3>
      <el-form label-position="top" style="max-width: 360px">
        <el-form-item label="原密码">
          <el-input v-model="passwordForm.old_password" type="password" show-password />
        </el-form-item>
        <el-form-item label="新密码">
          <el-input v-model="passwordForm.new_password" type="password" show-password />
        </el-form-item>
        <el-form-item label="确认新密码">
          <el-input v-model="passwordForm.confirm" type="password" show-password />
        </el-form-item>
        <el-button type="primary" :loading="savingPwd" @click="changePassword">修改密码</el-button>
      </el-form>
    </div>
  </div>
</template>
