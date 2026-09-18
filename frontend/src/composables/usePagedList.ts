/**
 * 列表分页的公共状态与请求逻辑(前台与后台共 8 个列表页)。
 *
 * 为什么抽出来: 每个列表页都各自写了一遍 items / total / page / loading +
 * load() + watch(page), 而且"翻页"与"按新条件重新查询"两种语义混在一起 ——
 * 有的页面把加载挂在 el-pagination 的 current-change 上, 有的用 watch(page),
 * 于是"筛选条件变化时要回到第 1 页"只能各写各的, 漏写就会停在上一个条件下
 * 越界的空页上。
 *
 * 统一后的约定:
 *  - 翻页: 分页器的 v-model 改 page, 这里自动请求, 模板不再需要 @current-change
 *  - 筛选条件变化: 调 reset(), 回到第 1 页重新查询
 *  - 增删改之后: 调 load(), 留在当前页刷新
 */
import { isRef, onMounted, ref, watch, type Ref } from 'vue'
import type { Page } from '@/types'

export interface PagedList<T> {
  items: Ref<T[]>
  total: Ref<number>
  page: Ref<number>
  pageSize: Ref<number>
  loading: Ref<boolean>
  /** 按当前页码与筛选条件加载一页 */
  load: () => Promise<void>
  /** 回到第 1 页重新加载(筛选条件变化时用) */
  reset: () => Promise<void>
}

export interface PagedListOptions<T> {
  /** 取一页数据; 筛选条件由调用方在闭包里读当前值 */
  fetch: (page: number, pageSize: number) => Promise<Page<T>>
  /** 每页数量, 固定值或 ref(媒体库要跟随栅格容量变化) */
  pageSize?: number | Ref<number>
  /** 挂载后自动加载第 1 页, 默认开启 */
  autoLoad?: boolean
  /** 每次加载成功后的副作用(如记录"最新一篇") */
  onLoaded?: (items: T[]) => void
}

export function usePagedList<T>(options: PagedListOptions<T>): PagedList<T> {
  const pageSize = isRef(options.pageSize) ? options.pageSize : ref(options.pageSize ?? 10)
  // items 用断言而非 ref<T[]>([]): 泛型数组经 UnwrapRef 后与 Ref<T[]> 不再等价
  const items = ref([]) as Ref<T[]>
  const total = ref(0)
  const page = ref(1)
  const loading = ref(false)

  async function load() {
    loading.value = true
    try {
      const data = await options.fetch(page.value, pageSize.value)
      items.value = data.items
      total.value = data.total
      options.onLoaded?.(data.items)
    } finally {
      // 失败也要复位: 否则页面会一直停在加载态(错误提示由请求拦截器负责)
      loading.value = false
    }
  }

  async function reset() {
    // 已经在第 1 页时页码不会变化, watch 不会触发, 所以这里要显式加载一次
    if (page.value === 1) {
      await load()
      return
    }
    page.value = 1
  }

  watch(page, () => {
    void load()
  })

  if (options.autoLoad !== false) {
    onMounted(() => {
      void load()
    })
  }

  return { items, total, page, pageSize, loading, load, reset }
}
