import { flushPromises, mount } from '@vue/test-utils'
import { createPinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

/**
 * 首页模块开关的用例。
 *
 * 背景(这次拆分的目的之一):
 *   以前首页在 onMounted 里用 if 判断着给自己的每个模块发请求, 模板里再各写一次 v-if,
 *   开关散落在两处; 现在"关掉的模块不挂载"就是唯一的事实来源 —— 不挂载自然不发请求。
 *   这里断言的就是这条约定: 关掉哪个开关, 对应接口就一次都不能被调到
 *   (请求了却被忽略是看不见的浪费, 只有断言请求次数才能发现)。
 */

const publicMock = vi.fn()
const hotMock = vi.fn()
const sayingMock = vi.fn()
const historyMock = vi.fn()
const contributionsMock = vi.fn()
const listMock = vi.fn()

vi.mock('@/api', () => ({
  settingsApi: { public: () => publicMock(), update: () => Promise.resolve({}) },
  categoryApi: { list: () => Promise.resolve([]) },
  postApi: {
    list: (...args: unknown[]) => listMock(...args),
    hot: (...args: unknown[]) => hotMock(...args),
  },
  statsApi: { contributions: (...args: unknown[]) => contributionsMock(...args) },
  miscApi: {
    saying: (...args: unknown[]) => sayingMock(...args),
    historyToday: () => historyMock(),
  },
  mediaApi: { upload: () => Promise.resolve({ url: '/x.png' }) },
}))

vi.mock('@/components/PostCard.vue', () => ({
  default: {
    name: 'PostCard',
    props: { post: { type: Object, required: true } },
    template: '<div class="post-stub">{{ post.title }}</div>',
  },
}))
vi.mock('@/components/MarkdownView.vue', () => ({
  default: { name: 'MarkdownView', props: ['content'], template: '<div class="md-stub" />' },
}))
vi.mock('@/components/ContributionsChart.vue', () => ({
  default: { name: 'ContributionsChart', props: ['points', 'years', 'year'], template: '<div class="chart-stub" />' },
}))
vi.mock('@/components/MetaIcon.vue', () => ({
  default: { name: 'MetaIcon', props: ['name'], template: '<i class="icon-stub" />' },
}))

import HomeView from '@/views/HomeView.vue'

const stubs = {
  'el-avatar': { props: ['src', 'size'], template: '<span><slot /></span>' },
  'el-tag': { template: '<span><slot /></span>' },
  'el-button': { template: '<button><slot /></button>' },
  'el-empty': { props: ['description'], template: '<div class="el-empty">{{ description }}</div>' },
  'el-dialog': { template: '<div><slot /><slot name="footer" /></div>' },
  'el-image': { template: '<div><slot name="error" /></div>' },
  'el-divider': { template: '<div><slot /></div>' },
  'el-input': { template: '<input />' },
  'el-upload': { template: '<div><slot /></div>' },
  'el-pagination': { template: '<div class="pager" />' },
  RouterLink: { props: ['to'], template: '<a><slot /></a>' },
}

/** 后台的模块开关: 只写需要关掉的那几个(后端把开关统一转成了布尔值, 见 /settings/public) */
function settings(overrides: Record<string, boolean> = {}) {
  return {
    site_name: 'phxxblog',
    social_links: [],
    website_links: [],
    tech_tags: [],
    show_readme: true,
    show_contributions: true,
    show_history: true,
    show_session: true,
    ...overrides,
  }
}

async function render(overrides: Record<string, boolean> = {}) {
  publicMock.mockResolvedValue(settings(overrides))
  const wrapper = mount(HomeView, {
    global: { plugins: [createPinia()], stubs, directives: { loading: () => {} } },
  })
  await flushPromises()
  await flushPromises()
  return wrapper
}

describe('HomeView 的模块开关', () => {
  beforeEach(() => {
    // jsdom 没有实现 scrollIntoView, 而首页翻页后要用它把列表滚回顶部
    Element.prototype.scrollIntoView = vi.fn()
    publicMock.mockReset().mockResolvedValue(settings({}))
    hotMock.mockReset().mockResolvedValue([])
    sayingMock.mockReset().mockResolvedValue({ text: '一言' })
    historyMock.mockReset().mockResolvedValue({ date: '09-18', events: [] })
    contributionsMock.mockReset().mockResolvedValue([])
    listMock.mockReset().mockResolvedValue({ items: [], total: 0, page: 1, page_size: 10 })
  })

  it('开关全开时每个模块各请求一次', async () => {
    const wrapper = await render()

    expect(listMock).toHaveBeenCalledTimes(1)
    expect(hotMock).toHaveBeenCalledTimes(1)
    expect(sayingMock).toHaveBeenCalledTimes(1)
    expect(historyMock).toHaveBeenCalledTimes(1)
    expect(contributionsMock).toHaveBeenCalledTimes(1)
    expect(wrapper.find('.term-card').exists()).toBe(true)
    expect(wrapper.find('.history-card').exists()).toBe(true)
  })

  it('关掉某个开关后对应接口一次都不请求, 且不渲染该模块', async () => {
    const wrapper = await render({ show_session: false, show_history: false, show_contributions: false })

    expect(sayingMock).not.toHaveBeenCalled()
    expect(historyMock).not.toHaveBeenCalled()
    expect(contributionsMock).not.toHaveBeenCalled()
    expect(wrapper.find('.term-card').exists()).toBe(false)
    expect(wrapper.find('.history-card').exists()).toBe(false)
    expect(wrapper.find('.chart-stub').exists()).toBe(false)
    // 没有开关的模块照常
    expect(hotMock).toHaveBeenCalledTimes(1)
  })

  it('翻页时只重新取文章列表', async () => {
    const wrapper = await render()
    const vm = wrapper.vm as unknown as { page: number }
    vm.page = 2
    await flushPromises()

    expect(listMock).toHaveBeenCalledTimes(2)
    expect(hotMock).toHaveBeenCalledTimes(1)
    expect(historyMock).toHaveBeenCalledTimes(1)
  })
})
