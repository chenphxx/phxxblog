/**
 * @brief 文章正文字号的档位表与本地存储
 *
 * 档位的像素表固定在前端, 后端只能改默认档与允许范围(见 app/modules/fontsize/spec.py):
 * 这样调配置不会让老访客已有的偏好落到未定义的像素值上
 *
 * 存储键只在这一处出现: 与 tokenStorage 同一约定, 散落在多处时改一处名字会让其他处静默失效
 */

/** 存储键, 值为档位序号(1 起), 不存像素 */
export const READING_FONT_SIZE_KEY = 'blog_reading_font_size'

/**
 * 档位像素表, 下标 0 即第 1 档
 *
 * 第 3 档与文章正文当前的默认字号一致(见 styles/theme.css 的 .markdown-body), 也就是
 * "不调字号时看到的效果"
 */
export const READING_FONT_STEPS = [13.5, 15, 16.5, 18, 19.5] as const

/** 档位总数, 也是档位取值的上限 */
export const READING_FONT_MAX_STEP = READING_FONT_STEPS.length

/** 后端配置拿不到时的兜底默认档位 */
export const READING_FONT_FALLBACK_STEP = 3

/** 代码块字号与正文字号的差值: 当前默认是 16.5 与 14.5 */
export const READING_CODE_SIZE_DELTA = 2

/**
 * @brief 把档位夹取到合法范围内
 *
 * @param step 目标档位
 * @param minStep 允许的最小档位
 * @param maxStep 允许的最大档位
 * @returns 落在 [1, 5] 且在允许范围内的整数档位
 */
export function clampStep(step: number, minStep: number, maxStep: number): number {
  const low = Math.max(1, Math.min(minStep, maxStep))
  const high = Math.min(READING_FONT_MAX_STEP, Math.max(minStep, maxStep))
  const value = Number.isFinite(step) ? Math.round(step) : READING_FONT_FALLBACK_STEP
  return Math.min(high, Math.max(low, value))
}

/**
 * @brief 档位换算成正文像素
 *
 * @param step 档位(1 起)
 * @returns 该档位的正文像素值
 */
export function stepToFontSize(step: number): number {
  return READING_FONT_STEPS[clampStep(step, 1, READING_FONT_MAX_STEP) - 1]
}

/**
 * @brief 档位换算成代码块像素
 *
 * @param step 档位(1 起)
 * @returns 该档位的代码块像素值
 */
export function stepToCodeSize(step: number): number {
  return stepToFontSize(step) - READING_CODE_SIZE_DELTA
}

/**
 * @brief 读取访客保存的字号档位
 *
 * @returns 档位; 没有存过或存的值非法时返回 null, 由调用方回落到默认档
 */
export function readStoredStep(): number | null {
  try {
    const raw = window.localStorage.getItem(READING_FONT_SIZE_KEY)
    if (!raw) return null
    const value = Number(raw)
    return Number.isFinite(value) ? value : null
  } catch {
    // 隐私模式等禁用本地存储的场景: 当作没存过, 不影响阅读
    return null
  }
}

/**
 * @brief 保存访客选择的字号档位
 *
 * @param step 档位(1 起)
 */
export function writeStoredStep(step: number): void {
  try {
    window.localStorage.setItem(READING_FONT_SIZE_KEY, String(step))
  } catch {
    // 写不进去不影响本次阅读, 只是下次打开回到默认档
  }
}
