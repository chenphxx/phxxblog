import type { ConfigRow, ModuleSettingValue } from '@/types'

/**
 * @brief 把模块配置里的行列表读成对象数组
 *
 * 行列表的值由后端解析后下发, 但类型上是联合类型; 这里做一次收敛, 取不到(模块被禁用,
 * 配置缺失或值被写坏)时返回空数组, 调用方不必再判空
 *
 * @param value 模块配置里的原始值
 * @returns 行列表, 每行是"列名 -> 值"
 */
export function rowsOf(value: ModuleSettingValue | undefined): ConfigRow[] {
  if (!Array.isArray(value)) return []
  return value
}

/**
 * @brief 把模块配置里的行列表读成"链接行"
 *
 * 行列表的列名由模块自己声明, 这里按链接的约定(name/url)取列并补齐, 缺列时补空串;
 * 取不到时返回空数组, 调用方不必再判空
 *
 * @param value 模块配置里的原始值
 * @returns 形如 { name, url } 的链接列表
 */
export function linkRowsOf(value: ModuleSettingValue | undefined): { name: string; url: string }[] {
  return rowsOf(value).map((row) => ({ name: row.name ?? '', url: row.url ?? '' }))
}

/**
 * @brief 把模块配置里的文本读成字符串
 *
 * @param value 模块配置里的原始值
 * @param fallback 值不是字符串时使用的兜底文案(值本身是空串时保留空串)
 * @returns 文本
 */
export function textOf(value: ModuleSettingValue | undefined, fallback = ''): string {
  return typeof value === 'string' ? value : fallback
}
