<script setup lang="ts">
import { faviconOf, linkName, onFaviconError } from '@/utils/linkIcon'

/**
 * @brief 首页左侧的常用网站卡片
 *
 * 只在管理员访问时由首页渲染(站长自己用的快捷入口), 自身不取数。
 */
defineProps<{ links: { name: string; url: string }[] }>()
</script>

<template>
  <aside class="card site-links-card">
    <h3>常用网站</h3>
    <a
      v-for="link in links"
      :key="link.url"
      :href="link.url"
      target="_blank"
      rel="noopener noreferrer"
      class="site-link"
    >
      <img
        v-if="faviconOf(link.url)"
        :src="faviconOf(link.url)"
        alt=""
        class="site-link-icon"
        @error="onFaviconError($event, link.url)"
      />
      <span>{{ linkName(link) }}</span>
    </a>
  </aside>
</template>

<style scoped>
.site-links-card {
  padding: 16px;
  text-align: left;
}
.site-links-card h3 {
  margin: 0 0 12px;
  font-size: 15px;
}
.site-link {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 0;
  color: var(--text);
  font-size: 14px;
  text-decoration: none;
}
.site-link:hover {
  color: var(--primary);
}
.site-link-icon {
  width: 20px;
  height: 20px;
  border-radius: 4px;
  flex-shrink: 0;
}
</style>
