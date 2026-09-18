/**
 * 文本统计(算法与后端 backend/app/services/text.py 保持一致),
 * 供写作页状态栏实时显示字数与预计阅读时间。
 */

/** 中日韩字符(按"字"计) */
const CJK_RE = /[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\u3040-\u30ff\uac00-\ud7af]/g
/** 英文/数字(按"词"计) */
const WORD_RE = /[A-Za-z0-9_']+/g
/** 预计阅读速度(字/分钟) */
const READING_SPEED = 300

/** 统计字数: 中日韩字符按字计, 英文/数字按单词计 */
export function countWords(text: string): number {
  if (!text) return 0
  return (text.match(CJK_RE)?.length ?? 0) + (text.match(WORD_RE)?.length ?? 0)
}

/** 按固定速度估算阅读时间(分钟), 不足 1 分钟按 1 分钟计 */
export function readingMinutes(words: number): number {
  if (words <= 0) return 0
  return Math.max(1, Math.ceil(words / READING_SPEED))
}
