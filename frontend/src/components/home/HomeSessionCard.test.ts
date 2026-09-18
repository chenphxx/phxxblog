import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

/**
 * 终端会话卡片的用例。
 *
 * 卡片里有两类数据: "一言"(自己取)与文章总数/最新一篇(首页传进来的)。
 * 这里断言前者: 挂载即取、手动刷新时 force=true(绕过"每天只刷一次"的缓存),
 * 以及第三方接口失败时的兜底文案 —— 失败后不能停在"一言加载中..."。
 */

const sayingMock = vi.fn()
vi.mock('@/api', () => ({
  miscApi: { saying: (...args: unknown[]) => sayingMock(...args) },
}))

import type { PublicSettings } from '@/types'
import HomeSessionCard from '@/components/home/HomeSessionCard.vue'

const stubs = {
  'el-button': {
    props: ['loading', 'disabled'],
    template: '<button class="act" @click="$emit(\'click\')"><slot /></button>',
  },
  RouterLink: { props: ['to'], template: '<a><slot /></a>' },
}

/** 卡片只读设置里的站点名与简介, 这里给最小的一份就够 */
function render(settings: Record<string, unknown> = {}) {
  return mount(HomeSessionCard, {
    props: { settings: settings as unknown as PublicSettings, totalPosts: 12, latestPost: null },
    global: { stubs },
  })
}

describe('HomeSessionCard', () => {
  beforeEach(() => {
    sayingMock.mockReset()
  })

  it('挂载时取一言, 并把首页传进来的文章数渲染到终端里', async () => {
    sayingMock.mockResolvedValue({ text: '今天也要写代码' })
    const wrapper = render()
    await flushPromises()

    expect(sayingMock).toHaveBeenCalledWith(false)
    expect(wrapper.text()).toContain('今天也要写代码')
    expect(wrapper.text()).toContain('12')
  })

  it('点刷新时带 force=true, 跳过每天只刷一次的缓存', async () => {
    sayingMock.mockResolvedValue({ text: '第一句' })
    const wrapper = render()
    await flushPromises()

    sayingMock.mockResolvedValue({ text: '第二句' })
    await wrapper.findAll('.act')[1].trigger('click')
    await flushPromises()

    expect(sayingMock).toHaveBeenLastCalledWith(true)
    expect(wrapper.text()).toContain('第二句')
  })

  it('取一言失败时给出可重试的提示, 而不是停在加载中', async () => {
    sayingMock.mockRejectedValue(new Error('boom'))
    const wrapper = render()
    await flushPromises()

    expect(wrapper.text()).toContain('一言暂时走神了')
  })
})
