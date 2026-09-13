import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ElMessage } from 'element-plus'
import type { ImportCheckResult, ImportResult } from '@/types'

/**
 * useImportExport 的单元测试。
 *
 * 这个 composable 承接了 PostManageView 与 DiaryView 里原本各一份(约 90 行)的
 * 导入/导出流程, 因此这里覆盖的是"流程分支"而不是渲染:
 *   - 没选文件时不应该调接口
 *   - 查到重复时应打开查重弹窗而不是直接导入
 *   - 导入成功后要清空文件并触发刷新钩子(否则列表还是旧的)
 *   - 未勾选内容时不能打开导出弹窗
 */

vi.mock('element-plus', () => ({
  ElMessage: { success: vi.fn(), warning: vi.fn(), error: vi.fn() },
}))

import { useImportExport, type UseImportExportOptions } from './useImportExport'

const makeCheck = (overrides: Partial<ImportCheckResult> = {}): ImportCheckResult => ({
  total: 2,
  duplicates_count: 0,
  duplicates: [],
  ...overrides,
})

const makeResult = (overrides: Partial<ImportResult> = {}): ImportResult => ({
  imported: 2,
  skipped: 0,
  errors: [],
  duplicates_count: 0,
  ...overrides,
})

/** 每个用例一套全新的 spy, 避免相互污染 */
function makeOptions(overrides: Partial<UseImportExportOptions> = {}) {
  const options = {
    filePrefix: 'phxxblog-posts',
    entity: '文章',
    unit: '篇',
    exportFile: vi.fn(() => Promise.resolve(new Blob(['zip']))),
    checkImports: vi.fn(() => Promise.resolve(makeCheck())),
    submitImports: vi.fn(() => Promise.resolve(makeResult())),
    exportMessage: vi.fn(() => '已导出 2 篇文章'),
    onImported: vi.fn(),
    ...overrides,
  }
  return options
}

function pickFiles(io: ReturnType<typeof useImportExport>, files: File[]) {
  const input = document.createElement('input')
  input.type = 'file'
  Object.defineProperty(input, 'files', { value: files })
  io.onImportPick({ target: input } as unknown as Event)
}

describe('useImportExport', () => {
  beforeEach(() => {
    vi.mocked(ElMessage.success).mockClear()
    vi.mocked(ElMessage.warning).mockClear()
    // jsdom 没有实现这两个 API, 导出流程要用
    URL.createObjectURL = vi.fn(() => 'blob:test')
    URL.revokeObjectURL = vi.fn()
    vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {})
  })

  it('没选文件时只提示, 不调用查重接口', async () => {
    const options = makeOptions()
    const io = useImportExport(options)

    await io.doImport()

    expect(options.checkImports).not.toHaveBeenCalled()
    expect(ElMessage.warning).toHaveBeenCalledWith('请先选择文件')
    expect(io.dupDialog).toBe(false)
  })

  it('查到重复时打开查重弹窗并关闭导入弹窗, 不写入数据', async () => {
    const options = makeOptions({
      checkImports: vi.fn(() =>
        Promise.resolve(makeCheck({ duplicates_count: 1, duplicates: ['旧文章'], total: 3 })),
      ),
    })
    const io = useImportExport(options)
    io.importDialog = true
    pickFiles(io, [new File(['a'], 'a.md')])

    await io.doImport()

    expect(options.submitImports).not.toHaveBeenCalled()
    expect(io.duplicateTotal).toBe(3)
    expect(io.duplicateCount).toBe(1)
    expect(io.duplicates).toEqual(['旧文章'])
    expect(io.importDialog).toBe(false)
    expect(io.dupDialog).toBe(true)
  })

  it('没有重复时直接导入, 成功后清空文件并刷新列表', async () => {
    const options = makeOptions()
    const io = useImportExport(options)
    io.importDialog = true
    pickFiles(io, [new File(['a'], 'a.md')])

    await io.doImport()

    expect(options.submitImports).toHaveBeenCalledWith(
      [expect.any(File)],
      'skip',
    )
    expect(io.importDialog).toBe(false)
    expect(io.importFiles).toEqual([])
    expect(options.onImported).toHaveBeenCalledTimes(1)
    // 提示里带实体单位(篇/条), 这是两个视图唯一的文案差异
    expect(ElMessage.success).toHaveBeenCalledWith('导入完成: 成功 2 篇, 跳过 0 篇')
  })

  it('查重弹窗里选"导入全部"时把 all 透传给接口', async () => {
    const options = makeOptions()
    const io = useImportExport(options)
    pickFiles(io, [new File(['a'], 'a.md')])
    io.dupDialog = true

    await io.runImport('all')

    expect(options.submitImports).toHaveBeenCalledWith([expect.any(File)], 'all')
    expect(io.dupDialog).toBe(false)
  })

  it('某个文件导入失败时会额外给出警告', async () => {
    const options = makeOptions({
      submitImports: vi.fn(() =>
        Promise.resolve(makeResult({ imported: 1, skipped: 1, errors: ['b.md 解析失败'] })),
      ),
    })
    const io = useImportExport(options)
    pickFiles(io, [new File(['a'], 'a.md')])

    await io.runImport('skip')

    expect(ElMessage.warning).toHaveBeenCalledWith('部分文件导入失败: b.md 解析失败')
  })

  it('canExport 返回 false 时不打开导出弹窗, 提示里带实体名', () => {
    const canExport = vi.fn(() => false)
    const io = useImportExport(makeOptions({ canExport }))

    io.openExportDialog()

    expect(canExport).toHaveBeenCalled()
    expect(io.exportDialog).toBe(false)
    expect(ElMessage.warning).toHaveBeenCalledWith('请先勾选要导出的文章')
  })

  it('导出时用当前格式请求文件, 触发下载并关闭弹窗', async () => {
    const options = makeOptions()
    const io = useImportExport(options)
    io.openExportDialog()
    io.exportFmt = 'html'

    await io.doExport()

    expect(options.exportFile).toHaveBeenCalledWith('html')
    expect(URL.createObjectURL).toHaveBeenCalled()
    expect(URL.revokeObjectURL).toHaveBeenCalled() // 下载后必须释放, 否则 blob 常驻内存
    expect(ElMessage.success).toHaveBeenCalledWith('已导出 2 篇文章')
    expect(io.exportDialog).toBe(false)
    expect(io.exporting).toBe(false)
  })

  it('每次打开导出弹窗都把格式重置回 markdown', () => {
    const io = useImportExport(makeOptions())
    io.exportFmt = 'html'

    io.openExportDialog()

    expect(io.exportFmt).toBe('markdown')
    expect(io.exportDialog).toBe(true)
  })

  it('导出接口抛错时只打日志, 不提示成功也不关闭弹窗', async () => {
    const options = makeOptions({
      exportFile: vi.fn(() => Promise.reject(new Error('导出失败(500)'))),
    })
    const io = useImportExport(options)
    io.openExportDialog()

    await io.doExport()

    expect(ElMessage.success).not.toHaveBeenCalled()
    expect(io.exportDialog).toBe(true) // 保持打开, 用户可以重试
    expect(io.exporting).toBe(false)
  })
})
