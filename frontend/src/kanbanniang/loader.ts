/**
 * @brief 看板娘运行时(public/kanbanniang/live2d.js)的按需加载与调用封装。
 *
 * 运行时是上游 kanbanniang 仓库里那份 Cubism 2.0 WebGL 运行时, 只在访客打开看板娘时才下载,
 * 下载结果缓存在模块作用域, 反复开关不会重复请求。
 * 运行时按 id 取 canvas 并初始化 WebGL, 因此调用 render() 前必须保证该 canvas 已在 DOM 中并设好宽高。
 */
import { BASE_URL } from './registry'

/** public/kanbanniang/live2d.js 注入的全局函数 */
declare global {
  interface Window {
    /** 在指定 canvas 上展示模型; 已经初始化过时再次调用即切换模型 */
    loadlive2d?: (canvasId: string, modelPath: string) => void
  }
}

/** 运行时脚本地址, 与 public/kanbanniang 目录一致 */
const RUNTIME_SRC = BASE_URL + 'live2d.js'

let runtimePromise: Promise<void> | null = null

/**
 * @brief 确保运行时脚本已加载。
 * @return 加载完成的 Promise, 失败时 reject 并清空缓存(下次可以重试)
 */
export function loadRuntime(): Promise<void> {
  if (!runtimePromise) {
    runtimePromise = new Promise<void>((resolve, reject) => {
      const script = document.createElement('script')
      script.src = RUNTIME_SRC
      script.async = true
      script.onload = () => resolve()
      script.onerror = () => {
        runtimePromise = null
        reject(new Error('看板娘运行时加载失败: ' + RUNTIME_SRC))
      }
      document.head.appendChild(script)
    })
  }
  return runtimePromise
}

/**
 * @brief 判断浏览器是否具备运行时需要的 WebGL 能力。
 *
 * 用一个临时 canvas 探测, 探测完主动释放上下文: 否则它会一直占着浏览器的 WebGL 上下文配额。
 * @return 支持返回 true
 */
export function supportsWebgl(): boolean {
  try {
    const probe = document.createElement('canvas')
    const gl = (probe.getContext('webgl') || probe.getContext('experimental-webgl')) as WebGLRenderingContext | null
    if (!gl) return false
    gl.getExtension('WEBGL_lose_context')?.loseContext()
    return true
  } catch {
    return false
  }
}

/**
 * @brief 展示或切换看板娘形象。
 * @param canvasId canvas 元素的 id
 * @param modelPath 模型 json 相对 BASE_URL 的路径(见 registry.ts)
 * @return 运行时或 canvas 尚未就绪时返回 false, 已交给运行时渲染返回 true
 */
export function render(canvasId: string, modelPath: string): boolean {
  const load = window.loadlive2d
  if (typeof load !== 'function' || !document.getElementById(canvasId)) return false
  load(canvasId, BASE_URL + modelPath)
  return true
}
