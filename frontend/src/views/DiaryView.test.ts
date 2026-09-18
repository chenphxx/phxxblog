import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ElMessage } from 'element-plus'

/**
 * DiaryView 的回归测试: 保存时必须取「编辑器里的内容」, 而不是只信 v-model。
 *
 * 用户报的现象: 新增日记要点两次保存才成功。
 * 根因: Vditor 在中文输入法组字期间会跳过 input 回调(vditor src/ts/ir/index.ts 的
 * composingLock), 于是会出现"编辑器里已经有字, 但 form.content_md 还是空"的一瞬间。
 * 此时点保存会命中空值判断直接 return, 而那句提示又因为样式缺失而看不见,
 * 用户只看到"点了没反应"。所以 save() 必须通过编辑器实例取值。
 *
 * 这里用一个模拟 VditorEditor 契约的桩: getValue() 返回编辑器里的真实内容,
 * 借此验证 save() 确实走向了编辑器而不是只读表单模型。
 */

/** 桩里编辑器的"真实内容", 由各用例设置(与表单模型故意不一致) */
const stubState = vi.hoisted(() => ({ editorValue: '' as string | null }))

const api = vi.hoisted(() => ({
  diaryList: vi.fn(),
  diaryCreate: vi.fn(),
  diaryUpdate: vi.fn(),
  diaryRemove: vi.fn(),
  contributions: vi.fn(),
}))

vi.mock('@/api', () => ({
  diaryApi: {
    list: api.diaryList,
    create: api.diaryCreate,
    update: api.diaryUpdate,
    remove: api.diaryRemove,
  },
  statsApi: { contributions: api.contributions },
}))

vi.mock('element-plus', () => ({
  ElMessage: { success: vi.fn(), warning: vi.fn(), error: vi.fn() },
  ElMessageBox: { confirm: vi.fn() },
}))

vi.mock('@/components/VditorEditor.vue', () => ({
  default: {
    name: 'VditorEditor',
    props: { modelValue: { type: String, default: '' } },
    emits: ['update:modelValue'],
    setup(_props: unknown, { expose }: { expose: (v: unknown) => void }) {
      expose({ getValue: () => stubState.editorValue })
      return () => null
    },
  },
}))

vi.mock('@/components/MarkdownView.vue', () => ({ default: { template: '<div/>' } }))
vi.mock('@/components/ContributionsChart.vue', () => ({ default: { template: '<div/>' } }))

import DiaryView from '@/views/DiaryView.vue'

/** 透传插槽的桩: 默认的 `true` 桩不会渲染子内容, 那样编辑器实例就不存在了 */
const passthrough = { template: '<div><slot /></div>' }

const stubs = {
  'el-button': true,
  'el-dialog': { template: '<div><slot /><slot name="footer" /></div>' },
  'el-form': passthrough,
  'el-form-item': passthrough,
  'el-date-picker': true,
  'el-empty': true,
  ImportExportDialogs: true,
}

type DiaryVm = {
  openCreate: () => void
  form: { content_md: string; entry_date: string }
  save: () => Promise<void>
}

async function setup() {
  const wrapper = mount(DiaryView, {
    global: { stubs, directives: { loading: () => {} } },
  })
  await flushPromises()
  return { wrapper, vm: wrapper.vm as unknown as DiaryVm }
}

describe('DiaryView 新增日记', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    stubState.editorValue = ''
    api.diaryList.mockResolvedValue({ items: [], total: 0, page: 1, page_size: 100 })
    api.contributions.mockResolvedValue([])
    api.diaryCreate.mockResolvedValue({ id: 1 })
    api.diaryUpdate.mockResolvedValue({ id: 1 })
  })

  it('v-model 还是空的时候, 保存要取编辑器里的内容并成功提交', async () => {
    const { vm } = await setup()
    vm.openCreate()
    // 关键前提: 表单模型为空(模拟组字期间 Vditor 未回调), 但编辑器里已有内容
    expect(vm.form.content_md).toBe('')
    stubState.editorValue = '输入法刚敲出来的内容'

    await vm.save()

    expect(api.diaryCreate).toHaveBeenCalledTimes(1)
    expect(api.diaryCreate).toHaveBeenCalledWith(expect.objectContaining({ content_md: '输入法刚敲出来的内容' }))
    expect(ElMessage.warning).not.toHaveBeenCalled()
    expect(ElMessage.success).toHaveBeenCalledWith('日记已保存')
  })

  it('编辑器与模型都为空时才提示, 并且不发请求', async () => {
    const { vm } = await setup()
    vm.openCreate()
    stubState.editorValue = null

    await vm.save()

    expect(api.diaryCreate).not.toHaveBeenCalled()
    expect(ElMessage.warning).toHaveBeenCalledWith('请输入日记内容')
  })

  it('编辑器取不到值时回退到表单模型(不在编辑器初始化前误判为空)', async () => {
    const { vm } = await setup()
    vm.openCreate()
    vm.form.content_md = '直接写进模型的内容'
    stubState.editorValue = null

    await vm.save()

    expect(api.diaryCreate).toHaveBeenCalledWith(expect.objectContaining({ content_md: '直接写进模型的内容' }))
  })

  it('新增日记的默认日期用本地日期, 不是 UTC 日期', async () => {
    const { vm } = await setup()
    vm.openCreate()

    const now = new Date()
    const pad = (n: number) => String(n).padStart(2, '0')
    const expected = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`
    expect(vm.form.entry_date).toBe(expected)
  })
})
