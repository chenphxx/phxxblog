/**
 * 媒体在线预览的方式判定。
 *
 * 后端把图片/视频/音频分别存成 image/video/audio, 其余(pdf、office、压缩包、文本…)统一是 `file`,
 * 所以文档类必须再按扩展名细分。判定结果决定预览浮层渲染什么, 单独抽出来便于单测。
 */
import type { MediaItem } from '@/types'

/** 在线预览方式 */
export type MediaPreviewKind = 'image' | 'video' | 'audio' | 'pdf' | 'text' | 'unsupported'

/** 文本类文档在线预览的大小上限; 超过只给下载入口, 避免把整份大文件读进内存 */
export const MAX_TEXT_PREVIEW = 256 * 1024

/** 可当纯文本读取的扩展名(与 backend/app/services/upload.py 的白名单保持一致) */
const TEXT_EXTS = ['.txt', '.md', '.csv', '.json']

/**
 * 判定一个媒体的预览方式。
 *
 * pdf 交给浏览器内置阅读器(iframe 直接指向文件); txt/md/csv/json 读取内容后用 <pre> 展示
 * (内容通过文本插值输出, 不会被当成 HTML 执行); 其余(office/压缩包等)浏览器无法渲染, 返回
 * unsupported, 浮层只提供下载。
 *
 * @param item 媒体(只需 type / original_name / size)
 * @return 预览方式; 文本类超过 MAX_TEXT_PREVIEW 时同样返回 unsupported
 */
export function previewKind(item: Pick<MediaItem, 'type' | 'original_name' | 'size'>): MediaPreviewKind {
  if (item.type === 'image') return 'image'
  if (item.type === 'video') return 'video'
  if (item.type === 'audio') return 'audio'
  const dot = item.original_name.lastIndexOf('.')
  const ext = dot >= 0 ? item.original_name.slice(dot).toLowerCase() : ''
  if (ext === '.pdf') return 'pdf'
  if (TEXT_EXTS.includes(ext)) return item.size <= MAX_TEXT_PREVIEW ? 'text' : 'unsupported'
  return 'unsupported'
}
