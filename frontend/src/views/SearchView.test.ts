import { flushPromises, mount } from '@vue/test-utils'
import { createMemoryHistory, createRouter } from 'vue-router'
import { beforeEach, describe, expect, it, vi } from 'vitest'

/**
 * SearchView 的回归测试。
 *
 * 背景(这次修的 bug):
 *   该组件被 SiteLayout 的 <keep-alive> 缓存, 因此在搜索页内点击另一个分类/标签时
 *   组件实例不会重建, setup 与 onMounted 都不会再跑。旧实现只在 setup 里读一次
 *   route.query, 于是 URL 变了、列表还是上一个分类的内容。
 *
 * 这里用一个真实 router + 反复 push 不同 query 来复现那个场景:
 *   如果组件不响应 route 变化, 第二次的条目数就不会更新, 测试会失败。
 */

// ---------- 把接口层替换成可预测的假数据 ----------
const listMock = vi.fn()
vi.mock('@/api', () => ({
  categoryApi: { list: () => Promise.resolve([]) },
  tagApi: { list: () => Promise.resolve([]) },
  postApi: { list: (...args: unknown[]) => listMock(...args) },
  searchApi: { search: (...args: unknown[]) => listMock(...args) },
}))

// 把 PostCard 换成一个极简桩: 测试只关心"渲染了哪些文章", 不关心卡片内部
vi.mock('@/components/PostCard.vue', () => ({
  default: {
    name: 'PostCard',
    props: { post: { type: Object, required: true } },
    template: '<div class="post-stub">{{ post.title }}</div>',
  },
}))

import SearchView from '@/views/SearchView.vue'

/** 让接口按 category 返回可区分的条目 */
function makePosts(category: string | undefined, count: number) {
  return Array.from({ length: count }, (_, i) => ({
    id: i + 1,
    title: `${category ?? 'all'}-${i + 1}`,
    slug: `s-${i}`,
    status: 2,
    views: 0,
    likes_count: 0,
    word_count: 10,
    reading_minutes: 1,
    created_at: '2026-09-14T00:00:00',
    updated_at: '2026-09-14T00:00:00',
    tags: [],
  }))
}

function makeRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/', name: 'home', component: { template: '<div/>' } },
      { path: '/search', name: 'search', component: SearchView },
    ],
  })
}

/** Element Plus 组件在测试里无关紧要, 统一桩掉; v-loading 是全局指令, 也要给个空实现 */
const globalStubs = {
  'el-input': true,
  'el-select': true,
  'el-option': true,
  'el-date-picker': true,
  'el-button': true,
  'el-pagination': true,
  'el-empty': true,
}
const globalDirectives = { loading: () => {} }

describe('SearchView 响应 route.query 变化', () => {
  beforeEach(() => {
    listMock.mockReset()
  })

  it('先进 /search?category=1, 再切到 category=2 时列表必须跟着变', async () => {
    listMock.mockImplementation((params: { category?: number }) =>
      Promise.resolve({ items: makePosts(String(params.category), params.category === 2 ? 3 : 5), total: 0, page: 1, page_size: 10 }),
    )

    const router = makeRouter()
    await router.push('/search?category=1')
    await router.isReady()

    const wrapper = mount(SearchView, { global: { plugins: [router], stubs: globalStubs, directives: globalDirectives } })
    await flushPromises()

    expect(wrapper.findAll('.post-stub')).toHaveLength(5)
    expect(wrapper.text()).toContain('1-1')

    // 同一个组件实例内切 query —— 等同于 keep-alive 场景下点击另一个分类标签
    await router.push('/search?category=2')
    await flushPromises()

    expect(wrapper.findAll('.post-stub')).toHaveLength(3)
    expect(wrapper.text()).toContain('2-1')
    expect(wrapper.text()).not.toContain('1-1')
  })

  it('切 query 时把页码重置回第 1 页', async () => {
    listMock.mockImplementation(() => Promise.resolve({ items: makePosts('x', 1), total: 100, page: 1, page_size: 10 }))

    const router = makeRouter()
    await router.push('/search?category=1')
    await router.isReady()

    const wrapper = mount(SearchView, { global: { plugins: [router], stubs: globalStubs, directives: globalDirectives } })
    await flushPromises()

    // 模拟用户翻到第 2 页
    const vm = wrapper.vm as unknown as { page: number }
    vm.page = 2
    await flushPromises()
    expect(listMock).toHaveBeenLastCalledWith(expect.objectContaining({ page: 2 }))

    // 切换分类后应回到第 1 页
    await router.push('/search?category=9')
    await flushPromises()
    expect(listMock).toHaveBeenLastCalledWith(expect.objectContaining({ page: 1, category: 9 }))
  })

  it('只带关键词时走搜索接口', async () => {
    listMock.mockImplementation(() => Promise.resolve({ items: makePosts('kw', 2), total: 2, page: 1, page_size: 10 }))

    const router = makeRouter()
    await router.push('/search?q=vue')
    await router.isReady()

    mount(SearchView, { global: { plugins: [router], stubs: globalStubs, directives: globalDirectives } })
    await flushPromises()

    expect(listMock).toHaveBeenCalled()
    // 搜索接口的第二个参数是分页选项
    expect(listMock.mock.calls[0][0]).toBe('vue')
  })
})
