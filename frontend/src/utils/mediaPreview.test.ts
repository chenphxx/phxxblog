import { describe, expect, it } from 'vitest'
import { MAX_TEXT_PREVIEW, previewKind } from '@/utils/mediaPreview'

/** 按后端 save_upload() 的字段构造一条媒体, 只给出判定用到的部分 */
function media(type: string, name: string, size = 1024) {
  return { type, original_name: name, size }
}

/**
 * 判定结果决定预览浮层渲染什么(图片/播放器/PDF 阅读器/文本/仅下载),
 * 文档类全靠扩展名区分, 所以逐个钉住。
 */
describe('previewKind', () => {
  it('图片/视频/音频直接用后端给的 type', () => {
    expect(previewKind(media('image', 'a.png'))).toBe('image')
    expect(previewKind(media('video', 'a.mp4'))).toBe('video')
    expect(previewKind(media('audio', 'a.mp3'))).toBe('audio')
  })

  it('pdf 交给浏览器内置阅读器', () => {
    expect(previewKind(media('file', 'report.PDF'))).toBe('pdf')
  })

  it('txt/md/csv/json 当纯文本读取', () => {
    expect(previewKind(media('file', 'note.txt'))).toBe('text')
    expect(previewKind(media('file', 'readme.md'))).toBe('text')
    expect(previewKind(media('file', 'data.csv'))).toBe('text')
    expect(previewKind(media('file', 'config.Json'))).toBe('text')
  })

  it('office / 压缩包 / 无扩展名等无法在线渲染, 只给下载', () => {
    expect(previewKind(media('file', 'doc.docx'))).toBe('unsupported')
    expect(previewKind(media('file', 'sheet.xlsx'))).toBe('unsupported')
    expect(previewKind(media('file', 'archive.zip'))).toBe('unsupported')
    expect(previewKind(media('file', 'README'))).toBe('unsupported')
    // 点号在目录名里而不是扩展名里(后端文件名已规范化, 这里只保证不误判)
    expect(previewKind(media('file', 'v1.2/bundle'))).toBe('unsupported')
  })

  it('超过上限的文本不再读取内容, 只给下载', () => {
    expect(previewKind(media('file', 'big.txt', MAX_TEXT_PREVIEW + 1))).toBe('unsupported')
    expect(previewKind(media('file', 'big.txt', MAX_TEXT_PREVIEW))).toBe('text')
  })
})
