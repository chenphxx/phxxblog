/**
 * 模块状态
 *
 * 后端 /api/v1/modules 给出"当前启用了哪些模块", 前端据此决定:
 *   - 侧栏与后台菜单里显示哪些入口(见 layouts/SiteLayout.vue, views/admin/AdminLayout.vue)
 *   - 直接访问禁用模块的页面时由路由守卫送回首页(见 router/index.ts)
 *   - 首页的终端卡片 / 历史上的今天 / 发布记录等模块化区块是否请求接口
 *
 * load() 是幂等的: 同一个会话内只请求一次, 后台改完模块配置后调用 load(true) 强制刷新
 */

import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { modulesApi } from '@/api'
import type { ModuleSettingValue, PublicModuleState } from '@/types'

export const useModulesStore = defineStore('modules', () => {
  const ids = ref<string[]>([])
  const config = ref<PublicModuleState['config']>({})
  const loaded = ref(false)
  /** 正在进行的加载(并发调用共用同一个请求) */
  let pending: Promise<void> | null = null

  /** 模块 id -> 是否可用 */
  const enabledMap = computed(() => new Set(ids.value))

  /**
   * 判断模块是否已启用
   *
   * 状态还没加载完时按"可用"处理: 否则首屏(还没等到接口返回)会把所有入口都藏起来,
   * 页面看起来像空的; 真正禁用后的兜底由路由守卫负责
   *
   * @param id 模块 id
   * @returns 可用返回 true
   */
  function isEnabled(id: string): boolean {
    if (!loaded.value) return true
    return enabledMap.value.has(id)
  }

  /**
   * 取模块的公开配置
   *
   * @param id 模块 id
   * @returns 该模块的公开配置(没有则返回空对象)
   */
  function moduleConfig(id: string): Record<string, ModuleSettingValue> {
    return config.value[id] ?? {}
  }

  /**
   * 拉取模块状态(幂等)
   *
   * @param force 为 true 时忽略缓存重新拉取
   */
  async function load(force = false): Promise<void> {
    if (loaded.value && !force) return
    if (pending) return pending
    pending = (async () => {
      try {
        const data = await modulesApi.public()
        ids.value = data.ids
        config.value = data.config
        loaded.value = true
      } catch {
        // 拉不到就保持"全部可用"的保守状态: 接口本身不可用时, 页面入口不该跟着消失
      } finally {
        pending = null
      }
    })()
    return pending
  }

  return { ids, config, loaded, isEnabled, moduleConfig, load }
})
