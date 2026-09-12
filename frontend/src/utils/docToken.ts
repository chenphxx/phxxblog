/**
 * API 文档鉴权 cookie 工具。
 *
 * 后端 /docs、/redoc、/openapi.json 仅 admin 角色可访问, 令牌既可从
 * Authorization 头读取, 也可从该 cookie 读取。把 access token 同步到 cookie,
 * 就能在新窗口直接打开文档页面(无需手动携带请求头)。
 */
export const DOC_TOKEN_COOKIE = 'phxxblog_doc_token'

/** 写入 access token(SameSite=Lax); 传空字符串表示清除 */
export function setDocTokenCookie(token: string) {
  if (typeof document === 'undefined') return
  // Secure 仅在 https 下附加, 否则本地 http 开发环境会被浏览器丢弃
  const secure = location.protocol === 'https:' ? '; Secure' : ''
  const maxAge = token ? `; Max-Age=${60 * 60 * 24 * 7}` : '; Max-Age=0'
  const value = token ? encodeURIComponent(token) : ''
  document.cookie = `${DOC_TOKEN_COOKIE}=${value}; Path=/; SameSite=Lax${secure}${maxAge}`
}

/** 清除 API 文档鉴权 cookie(登出或令牌失效时调用) */
export function clearDocTokenCookie() {
  setDocTokenCookie('')
}
