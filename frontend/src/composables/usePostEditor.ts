/**
 * 文章编辑器共享逻辑(WriteView 与 admin/PostEditView)。
 *
 * 两个视图原本各有一份几乎逐行相同的 `<script setup>`(表单状态、分类/标签联动创建、
 * 封面上传、保存、删除), 差异只有:
 *  - 点"取消"的去向(博客侧 router.back(), 后台侧回列表)
 *  - 删除确认框的文案
 * 这两点通过 options 注入, 其余逻辑只保留一份实现。
 *
 * 返回值是一个 reactive 对象(内部不使用 ref), 因此视图与 PostFormFields 都可以直接读写
 * `editor.form.title` 这类嵌套字段, 无需 .value。
 */
import { onMounted, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { categoryApi, mediaApi, postApi, tagApi } from '@/api'
import type { Category, PostDetail, Tag } from '@/types'

/** 编辑器表单模型 */
export interface PostForm {
  title: string
  slug: string
  summary: string
  content_md: string
  cover_image: string
  category_ids: number[]
  tag_ids: number[]
  status: number
  public_visible: boolean
}

/** 文章状态码 -> 文案(与后台列表的 STATUS_TEXT 前 4 项一致) */
export const POST_STATUS_TEXT: Record<number, string> = {
  0: '草稿',
  1: '审核中',
  2: '已发布',
  3: '私密',
}

export interface UsePostEditorOptions {
  /** 非编辑态点"取消"时执行的跳转; 编辑态一律返回文章页 */
  cancelFallback: () => void
  /** 标题为空时的提示, 默认"请填写文章标题" */
  missingTitleMessage?: string
  /** 删除确认框正文 */
  removeConfirmText?: string
}

export interface PostEditorState {
  isEdit: boolean
  postId: number
  categories: Category[]
  tags: Tag[]
  saving: boolean
  uploadingCover: boolean
  form: PostForm
  /** 首次挂载: 并行拉取分类/标签与文章详情 */
  init: () => Promise<void>
  loadOptions: () => Promise<void>
  loadPost: () => Promise<void>
  onCategoriesChange: (values: unknown) => Promise<void>
  onTagsChange: (values: unknown) => Promise<void>
  uploadCover: (options: { file: File }) => Promise<void>
  /** 不传 targetStatus 时按 public_visible 推导(公开 -> 已发布, 否则 -> 私密) */
  save: (targetStatus?: number) => Promise<void>
  cancel: () => void
  removePost: () => Promise<void>
}

function emptyForm(): PostForm {
  return {
    title: '',
    slug: '',
    summary: '',
    content_md: '',
    cover_image: '',
    category_ids: [],
    tag_ids: [],
    status: 0,
    public_visible: true,
  }
}

export function usePostEditor(options: UsePostEditorOptions): PostEditorState {
  const route = useRoute()
  const router = useRouter()

  const state = reactive({
    isEdit: Boolean(route.params.id),
    postId: Number(route.params.id) || 0,
    categories: [] as Category[],
    tags: [] as Tag[],
    saving: false,
    uploadingCover: false,
    form: emptyForm(),

    async loadOptions() {
      // 两个请求互不依赖, 并行发出
      const [cats, tagList] = await Promise.all([categoryApi.list(), tagApi.list()])
      state.categories = cats
      state.tags = tagList
    },

    async loadPost() {
      if (!state.isEdit) return
      const post: PostDetail = await postApi.detail(state.postId)
      state.form = {
        title: post.title,
        slug: post.slug,
        summary: post.summary || '',
        content_md: post.content_md,
        cover_image: post.cover_image || '',
        category_ids: post.categories.map((c) => c.id),
        tag_ids: post.tags.map((t) => t.id),
        status: post.status,
        public_visible: post.status !== 3,
      }
    },

    async init() {
      await Promise.all([state.loadOptions(), state.loadPost()])
    },

    /** 编辑器内直接新建分类: 与标签一样走 el-select 的 allow-create, 新项作为 string 传回 */
    async onCategoriesChange(values: unknown) {
      if (!Array.isArray(values)) return
      const ids: number[] = []
      let createdCount = 0
      for (const value of values) {
        if (typeof value === 'string' && value.trim()) {
          const created = await categoryApi.create({ name: value.trim(), slug: value.trim() })
          state.categories.push(created)
          ids.push(created.id)
          createdCount += 1
        } else if (typeof value === 'number') {
          ids.push(value)
        }
      }
      state.form.category_ids = ids
      if (createdCount > 0) ElMessage.success('分类已创建')
    },

    /** 编辑器内直接新建标签: el-select 的 allow-create 会把新项作为 string 传回 */
    async onTagsChange(values: unknown) {
      if (!Array.isArray(values)) return
      const ids: number[] = []
      for (const value of values) {
        if (typeof value === 'string' && value.trim()) {
          const created = await tagApi.create({ name: value.trim(), slug: value.trim() })
          state.tags.push(created)
          ids.push(created.id)
        } else if (typeof value === 'number') {
          ids.push(value)
        }
      }
      state.form.tag_ids = ids
    },

    async uploadCover(upload: { file: File }) {
      state.uploadingCover = true
      try {
        const media = await mediaApi.upload(upload.file)
        state.form.cover_image = media.url
        ElMessage.success('封面已上传')
      } finally {
        state.uploadingCover = false
      }
    },

    async save(targetStatus?: number) {
      if (!state.form.title.trim()) {
        ElMessage.warning(options.missingTitleMessage ?? '请填写文章标题')
        return
      }
      const status = targetStatus ?? (state.form.public_visible ? 2 : 3)
      state.saving = true
      try {
        const payload = { ...state.form, status }
        if (state.isEdit) {
          await postApi.update(state.postId, payload)
        } else {
          const created = await postApi.create(payload)
          state.postId = created.id
          state.isEdit = true
        }
        ElMessage.success(`已保存为${POST_STATUS_TEXT[status] ?? ''}`)
        router.push('/admin/posts')
      } finally {
        state.saving = false
      }
    },

    cancel() {
      if (state.isEdit) {
        router.push(`/post/${state.postId}`)
      } else {
        options.cancelFallback()
      }
    },

    async removePost() {
      try {
        await ElMessageBox.confirm(
          options.removeConfirmText ?? '确定删除这篇文章吗? 将移入回收站, 可在文章管理中恢复。',
          '删除确认',
          { type: 'warning', confirmButtonText: '删除' },
        )
      } catch {
        return // 用户取消, 不做任何事
      }
      await postApi.trash(state.postId)
      ElMessage.success('已删除')
      router.push('/admin/posts')
    },
  })

  onMounted(state.init)

  return state
}
