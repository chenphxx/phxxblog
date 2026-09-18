import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import {
  DEFAULT_MODEL_ID,
  KANBANNIAN_MODELS,
  MODEL_IDS,
  type KanbanniangModel,
  type KanbanniangModelId,
} from '@/kanbanniang/registry'

const ENABLED_KEY = 'blog_kanbanniang'
const MODEL_KEY = 'blog_kanbanniang_model'
const POSITION_KEY = 'blog_kanbanniang_pos'

/** 看板娘浮层左上角在视口内的坐标(px), 未拖动过时为 null */
export interface KanbanniangPosition {
  x: number
  y: number
}

function readStoredModel(): KanbanniangModelId {
  const saved = localStorage.getItem(MODEL_KEY)
  return MODEL_IDS.includes(saved as KanbanniangModelId) ? (saved as KanbanniangModelId) : DEFAULT_MODEL_ID
}

function readStoredPosition(): KanbanniangPosition | null {
  const saved = localStorage.getItem(POSITION_KEY)
  if (!saved) return null
  const [x, y] = saved.split(',').map(Number)
  return Number.isFinite(x) && Number.isFinite(y) ? { x, y } : null
}

/**
 * 看板娘设置:
 *   - allowed  后台的全站开关(系统设置 - 前台展示), 关掉后前台完全不出现看板娘
 *   - enabled  访客自己是否展示, 默认展示(关掉后由浏览器记住, 下次访问不再出现)
 *   - modelId  当前形象(见 kanbanniang/registry.ts)
 *   - position 拖动后的浮层坐标(相对视口左上角), null 表示未拖动过, 仍停在默认的左下角
 * 与主题一样属于访客自己的外观偏好, 只存在 localStorage, 不下发到后端。
 */
export const useKanbanniangStore = defineStore('kanbanniang', () => {
  // 默认不展示: 等公开配置回来再决定, 免得后台关掉时还去下载运行时与模型
  const allowed = ref(false)
  const enabled = ref(localStorage.getItem(ENABLED_KEY) !== 'off')
  const modelId = ref<KanbanniangModelId>(readStoredModel())
  const position = ref<KanbanniangPosition | null>(readStoredPosition())

  /** @brief 应用后台的全站开关(前台加载到公开配置后调用) */
  function setAllowed(value: boolean) {
    allowed.value = value
  }

  function toggle() {
    enabled.value = !enabled.value
    localStorage.setItem(ENABLED_KEY, enabled.value ? 'on' : 'off')
  }

  function setModel(id: KanbanniangModelId) {
    if (id === modelId.value) return
    modelId.value = id
    localStorage.setItem(MODEL_KEY, id)
  }

  /** @brief 记录浮层位置, 传 null 表示回到默认的左下角 */
  function setPosition(next: KanbanniangPosition | null) {
    position.value = next
    if (next) localStorage.setItem(POSITION_KEY, `${next.x},${next.y}`)
    else localStorage.removeItem(POSITION_KEY)
  }

  // 显式标注类型: registry 里的数组是 as const 的, 不标注会丢掉可选字段 canvas
  const current = computed<KanbanniangModel>(
    () => KANBANNIAN_MODELS.find((model) => model.id === modelId.value) ?? KANBANNIAN_MODELS[0],
  )

  return { allowed, enabled, modelId, position, current, setAllowed, toggle, setModel, setPosition }
})
