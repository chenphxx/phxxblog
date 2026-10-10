<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { authApi } from '@/api'
import { useAuthStore } from '@/stores/auth'
import { useModulesStore } from '@/stores/modules'
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
    /*
     * 模块状态是按访问者生成的("仅管理员可见"的模块只对管理员下发): 必须先等它按新身份
     * 刷新完再跳后台, 否则路由守卫会拿上一个身份(匿名)的模块集合判定, 把后台页面挡回去
     */
    await useModulesStore().load(true)
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
    <!-- 登录页也要能回到前台: 直接落在 /admin/login 时没有其它出口 -->
    <router-link to="/" class="login-back">
      <span aria-hidden="true">←</span>
      返回前台
    </router-link>

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
          <el-input
            v-model="form.password"
            type="password"
            show-password
            placeholder="请输入密码"
            @keyup.enter="login"
          />
        </el-form-item>
        <el-button type="primary" style="width: 100%" :loading="loading" @click="login">登 录</el-button>
      </el-form>
      <div class="login-footer muted">初始管理员: admin, 初始密码见后端 seed 输出(首次登录后请修改)</div>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  position: relative;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
}

/* 左上角的返回入口: 与卡片同级, 不参与卡片内的纵向排版 */
.login-back {
  position: absolute;
  top: var(--space-6);
  left: var(--space-6);
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border: 1px solid var(--border);
  border-radius: var(--radius-chip);
  background: var(--card-bg);
  color: var(--muted);
  font-size: 13px;
  transition:
    color var(--dur) var(--ease),
    border-color var(--dur) var(--ease);
}

.login-back:hover {
  color: var(--text);
  border-color: var(--border-strong);
  text-decoration: none;
}

@media (max-width: 640px) {
  .login-back {
    top: var(--space-4);
    left: var(--space-4);
  }
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
