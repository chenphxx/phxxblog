import type { User } from '@/types'

/**
 * @brief 判断当前用户是否拥有权限码
 *
 * 旧版本缓存的用户对象可能没有 permission_codes 字段; 编辑页会先重新读取
 * `/auth/me`, 因此这里仍做空值保护, 避免页面初始化时抛出异常
 *
 * @param user 当前用户
 * @param code 权限码
 * @returns 拥有权限时为 true
 */
export function hasPermission(user: User | null | undefined, code: string): boolean {
  return user?.permission_codes?.includes(code) ?? false
}
