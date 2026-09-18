<script setup lang="ts">
import type { Category, PublicSettings } from '@/types'
import { chipStyle } from '@/utils/chipColor'
import { faviconOf, linkName, onFaviconError } from '@/utils/linkIcon'

/**
 * @brief 首页左侧的个人资料卡片
 *
 * 内容来自后台设置与分类接口, 自己不取数; 头像点击改成事件抛给首页 —— 头像弹窗改的是
 * 页面级设置(site_avatar), 由首页统一持有更合适。
 */
defineProps<{
  settings: PublicSettings | null
  categories: Category[]
}>()

defineEmits<{ (e: 'open-avatar'): void }>()
</script>

<template>
  <aside class="profile-card card">
    <!-- 头像可点击查看大图: el-avatar 渲染成 span, 不加 role/tabindex 的话
       键盘用户无法触发, 屏幕阅读器也不知道它是个按钮 -->
    <el-avatar
      :size="96"
      :src="settings?.site_avatar || undefined"
      class="profile-avatar clickable-avatar"
      role="button"
      tabindex="0"
      aria-label="查看或更换头像"
      @click="$emit('open-avatar')"
      @keydown.enter.prevent="$emit('open-avatar')"
      @keydown.space.prevent="$emit('open-avatar')"
    >
      {{ (settings?.site_name || 'B')[0] }}
    </el-avatar>
    <h1 class="profile-name">{{ settings?.site_name || 'phxxblog' }}</h1>
    <p class="profile-bio">{{ settings?.site_bio || '' }}</p>

    <div class="profile-social">
      <a
        v-for="link in settings?.social_links || []"
        :key="link.url"
        :href="link.url"
        target="_blank"
        rel="noopener noreferrer"
        class="social-link"
        :title="linkName(link)"
      >
        <img
          v-if="faviconOf(link.url)"
          :src="faviconOf(link.url)"
          alt=""
          class="social-icon"
          @error="onFaviconError($event, link.url)"
        />
        <span>{{ linkName(link) }}</span>
      </a>
    </div>

    <div class="profile-tags">
      <el-tag v-for="tag in settings?.tech_tags || []" :key="tag" size="small" effect="plain" round>{{ tag }}</el-tag>
    </div>

    <div class="profile-categories">
      <router-link
        v-for="cat in categories"
        :key="cat.id"
        :to="`/search?category=${cat.id}`"
        class="category-chip chip"
        :style="chipStyle(cat.name, cat.color)"
      >
        {{ cat.name }} ({{ cat.post_count }})
      </router-link>
    </div>
  </aside>
</template>

<style scoped>
.profile-card {
  text-align: center;
  padding: 26px 18px 20px;
}
.profile-avatar {
  margin-bottom: 12px;
}
.clickable-avatar {
  cursor: pointer;
}
/* 键盘用户也需要看到焦点位置(头像已加 tabindex="0") */
.clickable-avatar:focus-visible {
  outline: 2px solid var(--primary);
  outline-offset: 3px;
  border-radius: 50%;
}
.profile-name {
  margin: 0 0 6px;
  font-size: 21px;
  font-weight: 700;
  letter-spacing: -0.01em;
}
.profile-bio {
  font-family: var(--font-mono);
  color: var(--muted);
  font-size: 12px;
  margin: 0 0 16px;
}
.profile-social {
  display: flex;
  justify-content: center;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 14px;
}
.social-link {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 10px;
  border: 1px solid var(--border);
  border-radius: 4px;
  color: var(--text);
  font-family: var(--font-mono);
  font-size: 11.5px;
  text-decoration: none;
}
.social-link:hover {
  border-color: var(--primary);
  color: var(--primary);
}
.social-icon {
  width: 16px;
  height: 16px;
}
.profile-tags {
  display: flex;
  justify-content: center;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 14px;
}
.profile-categories {
  border-top: 1px solid var(--border);
  padding-top: 12px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
}
.category-chip {
  font-size: 11.5px;
  padding: 2px 10px;
}
</style>
