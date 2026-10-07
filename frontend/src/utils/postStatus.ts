/**
 * @brief 文章状态码的展示文案与标签配色
 *
 * 前台列表行, 写作页保存提示, 后台文章管理与仪表盘会展示同一组状态,
 * 收敛到这里后改文案只需改一处
 *
 * 状态码与后端约定一致: 0 草稿, 1 审核中, 2 已发布, 3 私密, 4 回收站
 */

/** el-tag 的 type 只接受固定几个值, 因此用字面量联合而非 string */
export type PostStatusTagType = 'primary' | 'success' | 'warning' | 'info' | 'danger'

/** 状态码 -> 文案 */
export const POST_STATUS_TEXT: Record<number, string> = {
  0: '草稿',
  1: '审核中',
  2: '已发布',
  3: '私密',
  4: '回收站',
}

/** 状态码 -> el-tag 配色 */
export const POST_STATUS_TYPE: Record<number, PostStatusTagType> = {
  0: 'info',
  1: 'warning',
  2: 'success',
  3: 'danger',
  4: 'info',
}

/**
 * 状态码升序排列的文案数组, 下标即状态码
 *
 * 供只能按序号渲染的控件使用(例如后台列表的筛选按钮组)
 */
export const POST_STATUS_ORDERED: readonly string[] = Object.keys(POST_STATUS_TEXT)
  .map(Number)
  .sort((a, b) => a - b)
  .map((status) => POST_STATUS_TEXT[status])
