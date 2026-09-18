import { describe, expect, it } from 'vitest'
import { faviconOf, linkName, onFaviconError } from '@/utils/linkIcon'

/**
 * 首页的社交链接与常用网站依赖这三个函数, 它们的兜底分支(地址不合法)在页面上
 * 只表现为"这个链接没有图标"或"显示成了地址本身", 很容易被当成正常现象, 因此逐个钉住。
 */
describe('faviconOf', () => {
  it('按域名取图标', () => {
    expect(faviconOf('https://github.com/chenphxx')).toContain('domain=github.com')
  })

  it('地址不合法时返回空串(调用方据此不渲染 img)', () => {
    expect(faviconOf('不是地址')).toBe('')
  })
})

describe('linkName', () => {
  it('配置了名称时优先用名称', () => {
    expect(linkName({ name: 'GitHub', url: 'https://github.com/chenphxx' })).toBe('GitHub')
  })

  it('没有名称时退回域名', () => {
    expect(linkName({ url: 'https://developer.mozilla.org/zh-CN/' })).toBe('developer.mozilla.org')
  })

  it('地址不合法时原样返回, 至少不会显示成空白', () => {
    expect(linkName({ url: 'blog' })).toBe('blog')
  })
})

describe('onFaviconError', () => {
  it('加载失败时退回站点根目录的 favicon.ico', () => {
    const img = { src: 'x', style: { visibility: '' } }
    onFaviconError({ target: img } as unknown as Event, 'https://github.com/chenphxx')
    expect(img.src).toBe('https://github.com/favicon.ico')
  })

  it('地址不合法时把图标藏起来(否则浏览器显示裂图)', () => {
    const img = { src: 'x', style: { visibility: '' } }
    onFaviconError({ target: img } as unknown as Event, '不是地址')
    expect(img.style.visibility).toBe('hidden')
  })
})
