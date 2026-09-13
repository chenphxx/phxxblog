<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { Search } from '@element-plus/icons-vue'
import { categoryApi, postApi, searchApi, tagApi } from '@/api'
import type { Category, PostItem, Tag } from '@/types'
import PostCard from '@/components/PostCard.vue'

const route = useRoute()
const keyword = ref((route.query.q as string) || '')
const categoryId = ref(route.query.category ? Number(route.query.category) : null)
const tagId = ref(route.query.tag ? Number(route.query.tag) : null)
const categories = ref<Category[]>([])
const tags = ref<Tag[]>([])
const posts = ref<PostItem[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 10
const loading = ref(false)
const dateRange = ref<[string, string] | null>(null)

/**
 * 从 URL 查询参数回填筛选条件并重新检索。
 *
 * 为什么必须有这个 watch:
 *   本组件被 SiteLayout 的 <keep-alive include="...SearchView"> 缓存, 因此
 *   在搜索页内点击另一个分类/标签链接时,**组件实例不会重新创建**, setup 与
 *   onMounted 都不会再跑。以前只在 setup 里读一次 route.query, 结果就是
 *   URL 变了、列表还是上一个分类的内容。
 */
function syncFromQuery() {
  const q = route.query
  keyword.value = (q.q as string) || ''
  categoryId.value = q.category ? Number(q.category) : null
  tagId.value = q.tag ? Number(q.tag) : null
  page.value = 1
}

watch(
  () => route.fullPath,
  () => {
    // 仅在本路由内处理; 离开该页时不必发请求
    if (route.name !== 'search') return
    syncFromQuery()
    search()
  }
)

async function search() {
  loading.value = true
  const start_date = dateRange.value?.[0] || undefined
  const end_date = dateRange.value?.[1] || undefined
  try {
    if (categoryId.value || tagId.value) {
      const data = await postApi.list({
        page: page.value,
        page_size: pageSize,
        category: categoryId.value || undefined,
        tag: tagId.value || undefined,
        keyword: keyword.value.trim() || undefined,
        start_date,
        end_date,
      })
      posts.value = data.items
      total.value = data.total
    } else if (keyword.value.trim()) {
      const data = await searchApi.search(keyword.value.trim(), {
        page: page.value,
        page_size: pageSize,
        start_date,
        end_date,
      })
      posts.value = data.items
      total.value = data.total
    } else {
      const data = await postApi.list({ page: page.value, page_size: pageSize, start_date, end_date })
      posts.value = data.items
      total.value = data.total
    }
  } finally {
    loading.value = false
  }
}

watch(page, search)
onMounted(async () => {
  ;[categories.value, tags.value] = await Promise.all([categoryApi.list(), tagApi.list()])
  search()
})
</script>

<template>
  <div class="page-container">
    <p class="eyebrow" style="margin: 0 0 4px">posts — 全部文章</p>
    <h1 style="margin: 0 0 16px">全部文章</h1>

    <div class="search-bar">
      <el-input
        v-model="keyword"
        placeholder="输入关键词搜索文章..."
        :prefix-icon="Search"
        clearable
        @keyup.enter="page = 1; search()"
        @clear="page = 1; search()"
      />
      <el-select v-model="categoryId" placeholder="按分类筛选" clearable style="width: 180px" @change="page = 1; search()">
        <el-option v-for="cat in categories" :key="cat.id" :label="`${cat.name} (${cat.post_count})`" :value="cat.id" />
      </el-select>
      <el-select v-model="tagId" placeholder="按标签筛选" clearable style="width: 180px" @change="page = 1; search()">
        <el-option v-for="tag in tags" :key="tag.id" :label="`#${tag.name} (${tag.post_count})`" :value="tag.id" />
      </el-select>
      <el-date-picker
        v-model="dateRange"
        type="daterange"
        value-format="YYYY-MM-DD"
        range-separator="至"
        start-placeholder="开始日期"
        end-placeholder="结束日期"
        style="width: 260px"
        @change="page = 1; search()"
      />
      <el-button type="primary" @click="page = 1; search()">搜索</el-button>
    </div>

    <div v-loading="loading" style="margin-top: 20px; min-height: 100px">
      <PostCard v-for="post in posts" :key="post.id" :post="post" />
      <el-empty v-if="!loading && posts.length === 0" description="没有找到相关文章" />
      <el-pagination
        v-if="total > pageSize"
        v-model:current-page="page"
        :page-size="pageSize"
        :total="total"
        layout="prev, pager, next"
        style="justify-content: center; margin-top: 20px"
      />
    </div>
  </div>
</template>

<style scoped>
.search-bar {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}
.search-bar .el-input {
  flex: 1;
  min-width: 220px;
}
</style>
