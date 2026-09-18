import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

/**
 * 历史上的今天卡片的用例。
 *
 * 拆成独立模块后, "什么时候取数, 失败时显示什么" 由这个组件自己负责, 所以这里断言:
 *   - 挂载即取数(首页不再替它取)
 *   - refresh() 会重新取数(首页 keep-alive 重新激活时调的就是它)
 *   - 取数失败时不能停在加载态, 要按空状态展示(数据源是第三方接口)
 */

const historyMock = vi.fn()
vi.mock('@/api', () => ({
  miscApi: { historyToday: () => historyMock() },
}))

import HomeHistoryCard from '@/components/home/HomeHistoryCard.vue'

/** 组件里用到的 Element Plus 组件与指令在测试里只需占位 */
const stubs = {
  'el-button': { props: ['loading'], template: '<button class="refresh" @click="$emit(\'click\')"><slot /></button>' },
  'el-empty': { props: ['description'], template: '<div class="empty">{{ description }}</div>' },
}

function render() {
  return mount(HomeHistoryCard, { global: { stubs } })
}

describe('HomeHistoryCard', () => {
  beforeEach(() => {
    historyMock.mockReset()
  })

  it('挂载时取一次, 有条目时按年份与描述渲染', async () => {
    historyMock.mockResolvedValue({
      date: '09-18',
      events: [{ year: 1990, title: '某事件', description: '描述', category: '语言', tags: ['C'] }],
    })

    const wrapper = render()
    await flushPromises()

    expect(historyMock).toHaveBeenCalledTimes(1)
    expect(wrapper.text()).toContain('1990')
    expect(wrapper.text()).toContain('某事件')
    expect(wrapper.text()).toContain('09-18')
  })

  it('refresh() 重新取数(首页重新激活时用)', async () => {
    historyMock.mockResolvedValue({ date: '09-18', events: [] })
    const wrapper = render()
    await flushPromises()

    await (wrapper.vm as unknown as { refresh: () => Promise<void> }).refresh()
    expect(historyMock).toHaveBeenCalledTimes(2)
  })

  it('取数失败按空状态展示, 不停在加载态', async () => {
    historyMock.mockRejectedValue(new Error('boom'))
    const wrapper = render()
    await flushPromises()

    expect(wrapper.find('.empty').exists()).toBe(true)
    expect(wrapper.text()).toContain('暂无历史上的今天数据')
  })
})
