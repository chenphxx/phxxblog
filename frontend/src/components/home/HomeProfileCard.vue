<script setup lang="ts">
import type { Category, PublicSettings } from '@/types'
import { chipStyle } from '@/utils/chipColor'
import { faviconOf, linkName, onFaviconError } from '@/utils/linkIcon'

/**
 * @brief 首页的个人介绍区
 *
 * 内容来自后台设置与分类接口, 自己不取数; 头像点击改成事件抛给首页 - 头像弹窗改的是
 * 页面级设置(site_avatar), 由首页统一持有更合适
 *
 * 只负责介绍区本身, 外层的白色面板由首页提供(见 HomeView 的 .panel)
 */
defineProps<{
  settings: PublicSettings | null
  categories: Category[]
}>()

defineEmits<{ (e: 'open-avatar'): void }>()
</script>

<template>
  <div class="profile">
    <!-- 头像可点击查看大图: el-avatar 渲染成 span, 不加 role/tabindex 的话
       键盘用户无法触发, 屏幕阅读器也不知道它是个按钮 -->
    <el-avatar
      :size="76"
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

    <div class="profile-body">
      <h1 class="profile-name">{{ settings?.site_name || 'phxxblog' }}</h1>
      <p v-if="settings?.site_bio" class="profile-bio">{{ settings.site_bio }}</p>

      <div v-if="settings?.social_links?.length || settings?.tech_tags?.length" class="profile-row">
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

        <span v-for="tag in settings?.tech_tags || []" :key="tag" class="tech-tag">{{ tag }}</span>
      </div>
    </div>
  </div>

  <div v-if="categories.length" class="profile-categories">
    <router-link
      v-for="cat in categories"
      :key="cat.id"
      :to="`/search?category=${cat.id}`"
      class="chip category-chip"
      :style="chipStyle(cat.name, cat.color)"
    >
      {{ cat.name }} ({{ cat.post_count }})
    </router-link>
  </div>
</template>

<style scoped>
.profile {
  display: flex;
  align-items: flex-start;
  gap: var(--space-5);
}

.clickable-avatar {
  cursor: pointer;
  flex-shrink: 0;
}

/* 键盘用户也需要看到焦点位置(头像已加 tabindex="0") */
.clickable-avatar:focus-visible {
  outline: 2px solid var(--primary);
  outline-offset: 3px;
  border-radius: 50%;
}

.profile-body {
  min-width: 0;
}

.profile-name {
  margin: 0;
  font-size: 26px;
  font-weight: 650;
  letter-spacing: -0.03em;
  line-height: 1.2;
}

.profile-bio {
  margin: var(--space-2) 0 0;
  color: var(--muted);
  font-size: 14.5px;
  line-height: 1.7;
}

.profile-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: var(--space-4);
}

.social-link {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 3px 10px;
  border: 1px solid var(--border);
  border-radius: var(--radius-chip);
  color: var(--text);
  font-size: 12.5px;
  transition:
    border-color var(--dur) var(--ease),
    color var(--dur) var(--ease);
}

.social-link:hover {
  border-color: var(--border-strong);
  color: var(--link);
  text-decoration: none;
}

.social-icon {
  width: 15px;
  height: 15px;
}

/* 技术标签降级为纯文字, 不再每个都套一层底色 */
.tech-tag {
  color: var(--muted);
  font-size: 12.5px;
}

.tech-tag + .tech-tag::before {
  content: '·';
  margin-right: 8px;
  color: var(--border-strong);
}

.profile-categories {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: var(--space-5);
}

.category-chip {
  font-size: 12.5px;
  padding: 3px 11px;
}

@media (max-width: 640px) {
  .profile {
    flex-direction: column;
    align-items: center;
    text-align: center;
  }
}
</style>
