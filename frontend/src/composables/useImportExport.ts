/**
 * 导入 / 导出共享逻辑(admin/PostManageView 与 DiaryView)。
 *
 * 两个页面的导入导出流程完全同构, 只有四处不同, 都通过 options 注入:
 *  - 调的接口(文章 / 日记)
 *  - 提示文案里的实体名与数量单位(篇 / 条)
 *  - 导出成功提示(文章带数量, 日记是"全部")
 *  - 导入完成后的刷新(文章要重置页码, 日记直接重载)
 *
 * 返回值是 reactive 对象(内部不使用 ref), 视图与 ImportExportDialogs 可以直接读写
 * `io.importDialog` 这类字段, 无需 .value。
 */
import { reactive } from 'vue'
import { ElMessage } from 'element-plus'
import type { ImportCheckResult, ImportResult } from '@/types'

export type ExportFormat = 'markdown' | 'html'
/** skip=仅导入不重复, all=重复的也一并导入 */
export type DuplicateStrategy = 'skip' | 'all'

export interface UseImportExportOptions {
  /** 导出的 zip 文件名前缀, 最终为 `<prefix>-YYYY-MM-DD.zip` */
  filePrefix: string
  /** 实体名, 用于标题与提示: 文章 / 日记 */
  entity: string
  /** 数量单位: 篇 / 条 */
  unit: string
  exportFile: (format: ExportFormat) => Promise<Blob>
  checkImports: (files: File[]) => Promise<ImportCheckResult>
  submitImports: (files: File[], onDuplicate: DuplicateStrategy) => Promise<ImportResult>
  /** 导出成功提示 */
  exportMessage: () => string
  /** 打开导出弹窗前的守卫(如未勾选内容), 返回 false 则不打开 */
  canExport?: () => boolean
  /** 导入完成后的刷新钩子 */
  onImported?: () => void | Promise<void>
}

export interface ImportExportState {
  entity: string
  unit: string
  importDialog: boolean
  dupDialog: boolean
  exportDialog: boolean
  exportFmt: ExportFormat
  importing: boolean
  exporting: boolean
  importFiles: File[]
  /** 与已有内容重复的条目(标题或正文摘要) */
  duplicates: string[]
  duplicateCount: number
  duplicateTotal: number
  openExportDialog: () => void
  doExport: () => Promise<void>
  onImportPick: (event: Event) => void
  doImport: () => Promise<void>
  runImport: (onDuplicate: DuplicateStrategy) => Promise<void>
}

/** 触发浏览器下载一个 Blob, 用完立即释放 objectURL */
function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = filename
  document.body.appendChild(anchor)
  anchor.click()
  anchor.remove()
  URL.revokeObjectURL(url)
}

export function useImportExport(options: UseImportExportOptions): ImportExportState {
  const state = reactive({
    entity: options.entity,
    unit: options.unit,
    importDialog: false,
    dupDialog: false,
    exportDialog: false,
    exportFmt: 'markdown' as ExportFormat,
    importing: false,
    exporting: false,
    importFiles: [] as File[],
    duplicates: [] as string[],
    duplicateCount: 0,
    duplicateTotal: 0,

    openExportDialog() {
      if (options.canExport && !options.canExport()) {
        ElMessage.warning(`请先勾选要导出的${options.entity}`)
        return
      }
      state.exportFmt = 'markdown'
      state.exportDialog = true
    },

    async doExport() {
      state.exporting = true
      try {
        const blob = await options.exportFile(state.exportFmt)
        downloadBlob(blob, `${options.filePrefix}-${new Date().toISOString().slice(0, 10)}.zip`)
        ElMessage.success(options.exportMessage())
        state.exportDialog = false
      } catch {
        // 错误已由拦截器提示
      } finally {
        state.exporting = false
      }
    },

    onImportPick(event: Event) {
      const input = event.target as HTMLInputElement
      state.importFiles = input.files ? Array.from(input.files) : []
    },

    async doImport() {
      if (!state.importFiles.length) {
        ElMessage.warning('请先选择文件')
        return
      }
      state.importing = true
      try {
        // 先查重(不写入), 有重复时交给用户决定如何导入
        const check = await options.checkImports(state.importFiles)
        if (check.duplicates_count > 0) {
          state.duplicates = check.duplicates
          state.duplicateCount = check.duplicates_count
          state.duplicateTotal = check.total
          state.importDialog = false
          state.dupDialog = true
          return
        }
        await state.runImport('skip')
      } finally {
        state.importing = false
      }
    },

    async runImport(onDuplicate: DuplicateStrategy) {
      state.importing = true
      try {
        const result = await options.submitImports(state.importFiles, onDuplicate)
        ElMessage.success(
          `导入完成: 成功 ${result.imported} ${options.unit}, 跳过 ${result.skipped} ${options.unit}`,
        )
        if (result.errors?.length) {
          ElMessage.warning(`部分文件导入失败: ${result.errors.slice(0, 3).join('; ')}`)
        }
        state.dupDialog = false
        state.importDialog = false
        state.importFiles = []
        await options.onImported?.()
      } finally {
        state.importing = false
      }
    },
  })

  return state
}
