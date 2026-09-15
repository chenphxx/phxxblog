import { flushPromises, mount } from '@vue/test-utils'
import { defineComponent, h } from 'vue'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ElMessage, ElMessageBox } from 'element-plus'

/**
 * usePostEditor 的单元测试。
 *
 * 这个 composable 承接了 WriteView 与 admin/PostEditView 里原本各一份(约 120 行)的
 * 表单逻辑, 两个视图的差异只有"取消的去向"和删除文案, 靠 options 注入。
 * 因此这里重点覆盖容易写错的分支:
 *   - 状态推导(不传 targetStatus 时按 public_visible 决定 已发布/私密)
 *   - el-select 的 allow-create 回传字符串时要建新分类/标签, 数字则原样保留
 *   - 用户取消删除确认时不能真的调删除接口(否则会误删)
 */

const { routeState, pushMock, backMock } = vi.hoisted(() => ({
  routeState: { params: {} as Record<string, string> },
  pushMock: vi.fn(),
  backMock: vi.fn(),
}))

vi.mock('vue-router', () => ({
  useRoute: () => routeState,
  useRouter: () => ({ push: pushMock, back: backMock }),
}))

vi.mock('element-plus', () => ({
  ElMessage: { success: vi.fn(), warning: vi.fn(), error: vi.fn() },
  ElMessageBox: { confirm: vi.fn(() => Promise.resolve('confirm')) },
}))

const api = vi.hoisted(() => ({
  categoryList: vi.fn(),
  categoryCreate: vi.fn(),
  tagList: vi.fn(),
  tagCreate: vi.fn(),
  postDetail: vi.fn(),
  postCreate: vi.fn(),
  postUpdate: vi.fn(),
  postTrash: vi.fn(),
  mediaUpload: vi.fn(),
}))

vi.mock('@/api', () => ({
  categoryApi: { list: api.categoryList, create: api.categoryCreate },
  tagApi: { list: api.tagList, create: api.tagCreate },
  postApi: {
    detail: api.postDetail,
    create: api.postCreate,
    update: api.postUpdate,
    trash: api.postTrash,
  },
  mediaApi: { upload: api.mediaUpload },
}))

import { usePostEditor, type PostEditorState } from './usePostEditor'

/** 详情接口的完整返回, 与后端 PostDetail 对齐 */
const post = {
  id: 7,
  title: '旧标题',
  slug: 'old-post',
  summary: '旧摘要',
  content_md: '# 正文',
  cover_image: '/assets/uploads/a.png',
  status: 3, // 私密
  views: 0,
  likes_count: 0,
  word_count: 10,
  reading_minutes: 1,
  created_at: '2026-09-14T00:00:00',
  updated_at: '2026-09-14T00:00:00',
  categories: [{ id: 2, name: '后端', slug: 'backend' }],
  tags: [
    { id: 5, name: 'vue', slug: 'vue' },
    { id: 6, name: 'ts', slug: 'ts' },
  ],
}

/**
 * ElMessageBox.confirm 的 resolve 值。
 *
 * element-plus 把 MessageBoxData 声明成 `MessageBoxInputData & Action`(对象与字符串字面量求交,
 * 实际构造不出来), 所以只能断言掉。业务代码只关心"确认/取消", 从不读取这个值。
 */
const CONFIRM_RESULT = undefined as never

/** 在组件上下文里调用 composable(onMounted 需要有活着的实例) */
async function setupEditor(options: { cancelFallback?: () => void } = {}) {
  let editor!: PostEditorState
  const Host = defineComponent({
    setup() {
      editor = usePostEditor({ cancelFallback: options.cancelFallback ?? vi.fn() })
      return () => h('div')
    },
  })
  const wrapper = mount(Host)
  await flushPromises()
  return { editor, wrapper }
}

describe('usePostEditor', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    routeState.params = {}
    api.categoryList.mockResolvedValue([])
    api.tagList.mockResolvedValue([])
    api.postDetail.mockResolvedValue(post)
    api.postCreate.mockResolvedValue({ ...post, id: 9 })
    api.postUpdate.mockResolvedValue(post)
    api.postTrash.mockResolvedValue(null)
    api.mediaUpload.mockResolvedValue({ url: '/assets/uploads/new.png' })
    vi.mocked(ElMessageBox.confirm).mockResolvedValue(CONFIRM_RESULT)
  })

  it('新建态: 标题为空时不提交, 只提示', async () => {
    const { editor } = await setupEditor()

    await editor.save(0)

    expect(ElMessage.warning).toHaveBeenCalledWith('请填写文章标题')
    expect(api.postCreate).not.toHaveBeenCalled()
    expect(editor.saving).toBe(false)
  })

  it('新建态: 不传状态时按 public_visible 推导(公开 -> 2, 私密 -> 3)', async () => {
    // 分两次挂载: 首次保存后就会转成编辑态, 后续保存走的是 update
    const pub = await setupEditor()
    pub.editor.form.title = '新文章'
    pub.editor.form.public_visible = true
    await pub.editor.save()
    expect(api.postCreate).toHaveBeenCalledWith(expect.objectContaining({ status: 2 }))

    const priv = await setupEditor()
    priv.editor.form.title = '新文章'
    priv.editor.form.public_visible = false
    await priv.editor.save()
    expect(api.postCreate).toHaveBeenLastCalledWith(expect.objectContaining({ status: 3 }))
  })

  it('新建态: 保存草稿后记住新 id 并转为编辑态', async () => {
    const { editor } = await setupEditor()
    editor.form.title = '新文章'

    await editor.save(0)

    expect(editor.isEdit).toBe(true)
    expect(editor.postId).toBe(9)
    expect(ElMessage.success).toHaveBeenCalledWith('已保存为草稿')
    expect(pushMock).toHaveBeenCalledWith('/admin/posts')
  })

  it('编辑态: 详情映射进表单(私密 -> public_visible=false)', async () => {
    routeState.params = { id: '7' }
    const { editor } = await setupEditor()

    expect(editor.isEdit).toBe(true)
    expect(api.postDetail).toHaveBeenCalledWith(7)
    expect(editor.form).toMatchObject({
      title: '旧标题',
      slug: 'old-post',
      summary: '旧摘要',
      content_md: '# 正文',
      category_ids: [2],
      tag_ids: [5, 6],
      public_visible: false,
    })
  })

  it('编辑态: 保存走 update 而不是 create', async () => {
    routeState.params = { id: '7' }
    const { editor } = await setupEditor()

    await editor.save(1)

    expect(api.postUpdate).toHaveBeenCalledWith(7, expect.objectContaining({ status: 1 }))
    expect(api.postCreate).not.toHaveBeenCalled()
  })

  it('分类: 数组里的字符串项建新分类, 数字项原样保留', async () => {
    api.categoryCreate.mockResolvedValue({ id: 11, name: '运维', slug: '运维' })
    const { editor } = await setupEditor()

    await editor.onCategoriesChange([2, '  运维  '])

    expect(api.categoryCreate).toHaveBeenCalledWith({ name: '运维', slug: '运维' })
    expect(editor.form.category_ids).toEqual([2, 11])
    expect(editor.categories.map((c) => c.id)).toEqual([11])
  })

  it('分类: 空字符串不建新分类, 非数组(清空选择)直接忽略', async () => {
    const { editor } = await setupEditor()

    await editor.onCategoriesChange(['   '])
    await editor.onCategoriesChange(null)

    expect(api.categoryCreate).not.toHaveBeenCalled()
    expect(editor.form.category_ids).toEqual([])
  })

  it('标签: 字符串项建新标签, 数字项原样保留', async () => {
    api.tagCreate.mockResolvedValue({ id: 21, name: '新标签', slug: '新标签' })
    const { editor } = await setupEditor()

    await editor.onTagsChange([5, ' 新标签 '])

    expect(api.tagCreate).toHaveBeenCalledTimes(1)
    expect(editor.form.tag_ids).toEqual([5, 21])
  })

  it('删除: 用户在确认框里取消时不调用删除接口', async () => {
    routeState.params = { id: '7' }
    // ElMessageBox.confirm 在用户点取消时是 reject
    vi.mocked(ElMessageBox.confirm).mockRejectedValue('cancel')
    const { editor } = await setupEditor()

    await editor.removePost()

    expect(api.postTrash).not.toHaveBeenCalled()
    expect(pushMock).not.toHaveBeenCalled()
  })

  it('删除: 确认后移入回收站并回到列表', async () => {
    routeState.params = { id: '7' }
    const { editor } = await setupEditor()

    await editor.removePost()

    expect(api.postTrash).toHaveBeenCalledWith(7)
    expect(pushMock).toHaveBeenCalledWith('/admin/posts')
  })

  it('取消: 新建态走注入的 cancelFallback, 编辑态回文章页', async () => {
    const cancelFallback = vi.fn()
    const created = await setupEditor({ cancelFallback })
    created.editor.cancel()
    expect(cancelFallback).toHaveBeenCalledTimes(1)
    expect(pushMock).not.toHaveBeenCalled()

    routeState.params = { id: '7' }
    const editing = await setupEditor({ cancelFallback })
    editing.editor.cancel()
    expect(pushMock).toHaveBeenCalledWith('/post/7')
  })

  it('封面上传: 成功后写入 URL, 并复位 loading 标记', async () => {
    const { editor } = await setupEditor()
    const file = new File(['x'], 'cover.png', { type: 'image/png' })

    const pending = editor.uploadCover({ file })
    expect(editor.uploadingCover).toBe(true)
    await pending

    expect(api.mediaUpload).toHaveBeenCalledWith(file)
    expect(editor.form.cover_image).toBe('/assets/uploads/new.png')
    expect(editor.uploadingCover).toBe(false)
  })

  it('封面上传: 接口失败时也要复位 loading 标记', async () => {
    api.mediaUpload.mockRejectedValue(new Error('上传失败'))
    const { editor } = await setupEditor()

    await expect(editor.uploadCover({ file: new File(['x'], 'a.png') })).rejects.toThrow('上传失败')

    expect(editor.uploadingCover).toBe(false)
  })
})
