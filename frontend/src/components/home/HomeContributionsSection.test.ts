import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

/**
 * 文章发布记录区块的用例。
 *
 * 这里的关键是年份筛选: 传错年份会拿到另一年的热力图, 界面上看不出来对错,
 * 所以断言的是"请求参数里的 year"与"失败后 loading 必须复位"。
 */

const contributionsMock = vi.fn()
vi.mock('@/api', () => ({
  statsApi: { contributions: (...args: unknown[]) => contributionsMock(...args) },
}))

import HomeContributionsSection from '@/components/home/HomeContributionsSection.vue'

vi.mock('@/components/ContributionsChart.vue', () => ({
  default: {
    name: 'ContributionsChart',
    props: ['points', 'years', 'year'],
    emits: ['update:year'],
    template:
      '<div class="chart-stub">{{ points.length }}|{{ year === null ? \'all\' : year }}' +
      '<button class="pick" @click="$emit(\'update:year\', 2024)" /></div>',
  },
}))

/**
 * 记录 v-loading 的取值: 断言"失败后必须复位"需要看得见这个状态,
 * 而 loading 是组件内部状态, 不该为了测试把它暴露出去。
 */
const loadingDirective = {
  mounted: (el: HTMLElement, binding: { value: boolean }) => el.setAttribute('data-loading', String(binding.value)),
  updated: (el: HTMLElement, binding: { value: boolean }) => el.setAttribute('data-loading', String(binding.value)),
}

function render() {
  return mount(HomeContributionsSection, { global: { directives: { loading: loadingDirective } } })
}

describe('HomeContributionsSection', () => {
  beforeEach(() => {
    contributionsMock.mockReset()
    contributionsMock.mockResolvedValue([])
  })

  it('挂载时按 52 周取数, 默认不带年份', async () => {
    const wrapper = render()
    await flushPromises()

    expect(contributionsMock).toHaveBeenCalledWith({ source: 'post', weeks: 52, year: undefined })
    expect(wrapper.find('.chart-stub').text()).toContain('all')
  })

  it('切换年份后按新年份重取', async () => {
    const wrapper = render()
    await flushPromises()

    await wrapper.find('.pick').trigger('click')
    await flushPromises()

    expect(contributionsMock).toHaveBeenLastCalledWith({ source: 'post', weeks: 52, year: 2024 })
  })

  it('取数失败后 loading 复位(否则区块一直转圈)', async () => {
    contributionsMock.mockRejectedValue(new Error('boom'))
    const wrapper = render()
    await flushPromises()

    expect(wrapper.get('[data-loading]').attributes('data-loading')).toBe('false')
    expect(wrapper.find('.chart-stub').text()).toContain('0')
  })
})
