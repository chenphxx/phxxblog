// @vitest-environment node
import { describe, expect, it, vi } from 'vitest'
import { nextTick } from 'vue'
import { usePagedList } from './usePagedList'

/**
 * usePagedList 的单元测试。
 *
 * 抽这个 composable 的动机是"翻页"与"按新条件重查"两条路径曾经各写各的,
 * 所以这里断言的就是这两条路径的请求次数与页码 —— 请求多一次少一次在界面上
 * 只表现为闪一下或者数据不对, 靠人眼很难发现:
 *   - load 写数据, 且失败也要复位 loading(否则页面一直转圈)
 *   - reset 在第 1 页时直接重载, 在别的页时回到第 1 页且只请求一次
 *   - onLoaded 每次加载都能拿到当页数据(首页靠它记录"最新一篇")
 */

/** 假接口: 每页返回一条"当前页码", 便于断言请求的是第几页 */
function paged(total = 5) {
  return vi.fn(async (page: number, pageSize: number) => ({
    items: [page],
    total,
    page,
    page_size: pageSize,
  }))
}

describe('usePagedList', () => {
  it('load 写入当页数据与总数, 并在结束后复位 loading', async () => {
    const fetch = paged()
    const list = usePagedList<number>({ fetch, autoLoad: false })

    expect(list.loading.value).toBe(false)
    const pending = list.load()
    expect(list.loading.value).toBe(true)
    await pending

    expect(fetch).toHaveBeenCalledWith(1, 10)
    expect(list.items.value).toEqual([1])
    expect(list.total.value).toBe(5)
    expect(list.loading.value).toBe(false)
  })

  it('请求失败时也要复位 loading(否则页面永远停在加载态)', async () => {
    const fetch = vi.fn(async () => {
      throw new Error('boom')
    })
    const list = usePagedList<number>({ fetch, autoLoad: false })

    await expect(list.load()).rejects.toThrow('boom')
    expect(list.loading.value).toBe(false)
  })

  it('reset 在第 1 页时直接重载, 不依赖 watch', async () => {
    const fetch = paged()
    const list = usePagedList<number>({ fetch, pageSize: 3, autoLoad: false })

    await list.reset()
    expect(fetch).toHaveBeenCalledTimes(1)
    expect(fetch).toHaveBeenCalledWith(1, 3)
  })

  it('翻页只请求一次, reset 回到第 1 页也只请求一次', async () => {
    const fetch = paged()
    const list = usePagedList<number>({ fetch, autoLoad: false })

    list.page.value = 2
    await nextTick()
    expect(fetch).toHaveBeenCalledTimes(1)
    expect(fetch).toHaveBeenLastCalledWith(2, 10)

    await list.reset()
    await nextTick()
    expect(list.page.value).toBe(1)
    expect(fetch).toHaveBeenCalledTimes(2)
    expect(fetch).toHaveBeenLastCalledWith(1, 10)
  })

  it('onLoaded 每次加载后都能拿到当页数据', async () => {
    const fetch = paged()
    const onLoaded = vi.fn()
    const list = usePagedList<number>({ fetch, autoLoad: false, onLoaded })

    await list.load()
    expect(onLoaded).toHaveBeenCalledWith([1])
  })
})
