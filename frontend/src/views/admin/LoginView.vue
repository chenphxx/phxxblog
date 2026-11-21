<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { authApi, settingsApi } from '@/api'
import { useAuthStore } from '@/stores/auth'
import { useModulesStore } from '@/stores/modules'
import ThemeToggle from '@/components/ThemeToggle.vue'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const form = ref({ username: 'admin', password: '' })
const loading = ref(false)
const siteName = ref('phxxblog')
const siteIcon = ref('')

async function login()
{
    if (!form.value.username || !form.value.password)
    {
        ElMessage.warning('请输入用户名和密码')
        return
    }
    loading.value = true
    try
    {
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
    } catch
    {
        // 拦截器已提示
    } finally
    {
        loading.value = false
    }
}

onMounted(() =>
{
    settingsApi
        .public()
        .then((data) =>
        {
            siteName.value = data.site_name || data.site_title || 'phxxblog'
            siteIcon.value = data.site_icon
            document.title = data.site_title || data.site_name || 'phxxblog'
        })
        .catch(() =>
        {})
})
</script>

<template>
    <div class="login-page">
        <router-link to="/" class="login-back">
            <span aria-hidden="true">←</span>
            返回前台
        </router-link>

        <div class="login-shell">
            <aside class="login-brand-panel">
                <div class="login-brand">
                    <span class="login-brand-mark" aria-hidden="true">
                        <img v-if="siteIcon" :src="siteIcon" alt="" />
                        <template v-else>PX</template>
                    </span>
                    <span class="login-brand-copy">
                        <strong>{{ siteName }}</strong>
                        <span>Content workspace</span>
                    </span>
                </div>

                <div class="login-statement">
                    <span>Editorial control</span>
                    <h1>让内容保持清晰，<br />让管理保持安静。</h1>
                    <p>发布文章、整理内容、查看访问数据，并在同一套工作流中完成站点维护。</p>
                </div>
            </aside>

            <main class="login-card">
                <div class="login-header">
                    <div class="login-header-copy">
                        <span>Sign in</span>
                        <h2>登录管理后台</h2>
                        <p>使用管理员账号继续</p>
                    </div>
                    <ThemeToggle />
                </div>

                <el-form class="login-form" label-position="top" @submit.prevent="login">
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
                    <el-button class="login-submit" type="primary" :loading="loading" @click="login">登录</el-button>
                </el-form>

                <p class="login-footer">初始管理员为 admin，初始密码见后端 seed 输出。首次登录后请及时修改密码。</p>
            </main>
        </div>
    </div>
</template>
