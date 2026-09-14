<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { authApi } from '@/api'
import { useAuthStore } from '@/stores/auth'
import ThemeToggle from '@/components/ThemeToggle.vue'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const form = ref({ username: 'admin', password: '' })
const loading = ref(false)

async function login() {
  if (!form.value.username || !form.value.password) {
    ElMessage.warning('请输入用户名和密码')
    return
  }
  loading.value = true
  try {
    const result = await authApi.login(form.value)
    auth.setSession(result.tokens.access_token, result.tokens.refresh_token, result.user)
    ElMessage.success('登录成功')
    const redirect = (route.query.redirect as string) || '/admin/dashboard'
    router.push(redirect)
  } catch {
    // 拦截器已提示
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <div class="login-card card">
      <div class="login-header">
        <h2>博客管理后台</h2>
        <ThemeToggle />
      </div>
      <el-form label-position="top" @submit.prevent="login">
        <el-form-item label="用户名 / 邮箱">
          <el-input v-model="form.username" placeholder="admin" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="form.password" type="password" show-password placeholder="请输入密码" @keyup.enter="login" />
        </el-form-item>
        <el-button type="primary" style="width: 100%" :loading="loading" @click="login">登 录</el-button>
      </el-form>
      <div class="login-footer muted">
        默认管理员: admin / admin123456(首次登录后请修改)
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
}
.login-card {
  width: 380px;
  max-width: 100%;
}
.login-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}
.login-header h2 {
  margin: 0;
}
.login-footer {
  margin-top: 16px;
  text-align: center;
  font-size: 12px;
}
</style>
