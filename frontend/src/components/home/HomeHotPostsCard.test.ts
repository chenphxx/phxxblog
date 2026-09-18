import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

/**
 * 热门文章模块的用例。
 *
 * 它是首页的辅助模块, 取值口径与失败行为都在这里: 固定取 7 条, 失败时保持空列表
 * (拦截器已经提示过错误), 不能把异常抛给首页的 onMounted。
 */

const hotMock = vi.fn()
vi.mock('@/api', () => ({
  postApi: { hot: (...args: unknown[]) => hotMock(...args) },
}))

import HomeHotPostsCard from '@/components/home/HomeHotPostsCard.vue'

/** 榜单样式在 PostDetailView.test 里没有覆盖, 这里只关心取数与容错, 用桩换掉 */
vi.mock('@/components/HotPostsCard.vue', () => ({
  default: {
    name: 'HotPostsCard',
    props: { posts: { type: Array, required: true } },
    template: '<ol class="hot-stub"><li v-for="p in posts" :key="p.id">{{ p.title }}</li></ol>',
  },
}))

function render() {
  return mount(HomeHotPostsCard)
}

describe('HomeHotPostsCard', () => {
  beforeEach(() => {
    hotMock.mockReset()
  })

  it('挂载时按 7 条取数并展示', async () => {
    hotMock.mockResolvedValue([
      { id: 1, title: '热门一' },
      { id: 2, title: '热门二' },
    ])
    const wrapper = render()
    await flushPromises()

    expect(hotMock).toHaveBeenCalledWith(7)
    expect(wrapper.findAll('.hot-stub li')).toHaveLength(2)
  })

  it('取数失败时保持空列表且不抛错', async () => {
    hotMock.mockRejectedValue(new Error('boom'))
    const wrapper = render()
    await flushPromises()

    expect(wrapper.findAll('.hot-stub li')).toHaveLength(0)
  })

  it('refresh() 重新取数(阅读量会随访问变化)', async () => {
    hotMock.mockResolvedValue([])
    const wrapper = render()
    await flushPromises()

    await (wrapper.vm as unknown as { refresh: () => Promise<void> }).refresh()
    expect(hotMock).toHaveBeenCalledTimes(2)
  })
})
