/**
 * 主题清单 —— 由 design/themes/generate-themes.mjs 生成, 请勿手改。
 * 改主题请改 design/themes/tokens.mjs 后重新生成。
 */

export type ThemeId =
  | 'cuanmu'
  | 'emerald'
  | 'neon'
  | 'moss'
  | 'mist'
  | 'matcha'
  | 'pine'
  | 'bud'
  | 'mint'
  | 'sage'
  | 'aurora'
  | 'ink'

export interface ThemeOption {
  id: ThemeId
  name: string
  en: string
  desc: string
  /** 预览用的两三个代表色, 供下拉菜单左侧色点显示 */
  swatch: string[]
}

export const DEFAULT_THEME: ThemeId = 'cuanmu'

export const THEME_OPTIONS: ThemeOption[] = [
  {
    id: 'cuanmu',
    name: '预设',
    en: 'Preset',
    desc: '中性灰阶 + 静蓝主色，克制的文档站风格（令牌来自 VitePress + Teek 预设）。',
    swatch: ['#3a5ccc', '#3a5ccc', '#3e63dd'],
  },
  {
    id: 'emerald',
    name: '森屿绿洲',
    en: 'Fresh Emerald',
    desc: '翡翠绿主色 + 青绿渐变，大圆角与柔和阴影，最现代产品化的一套。',
    swatch: ['#0b7f45', '#0d9488', '#34d980'],
  },
  {
    id: 'neon',
    name: '霓虹青柠',
    en: 'Neon Lime',
    desc: '荧光青柠 + 近黑底色，方正硬阴影与等宽标题，开发者气质最强。',
    swatch: ['#5f9c00', '#4e8f00', '#a3e635'],
  },
  {
    id: 'moss',
    name: '苔原手记',
    en: 'Moss Editorial',
    desc: '苔绿 + 陶土点缀与衬线标题，纸质底色，最安静耐读的一套。',
    swatch: ['#3f6b4a', '#3f6b4a', '#9dbfa4'],
  },
  {
    id: 'mist',
    name: '晨雾青',
    en: 'Morning Mist',
    desc: '冷调青绿 + 灰绿底色，低饱和、干净克制，像清晨的薄雾。',
    swatch: ['#0e7a70', '#0e8a8a', '#2fd4bd'],
  },
  {
    id: 'matcha',
    name: '抹茶奶绿',
    en: 'Matcha Latte',
    desc: '暖调抹茶绿配奶油底色，低饱和、温柔治愈，久看不累。',
    swatch: ['#566f2a', '#566f2a', '#b3cc7a'],
  },
  {
    id: 'pine',
    name: '松涛墨绿',
    en: 'Pine Night',
    desc: '深色优先的影院感，墨绿底 + 松针绿高光，对比强、气场足。',
    swatch: ['#0d5f45', '#0f7a5a', '#43c98b'],
  },
  {
    id: 'bud',
    name: '春芽黄绿',
    en: 'Lime Bud',
    desc: '明亮嫩芽黄绿，年轻、有冲劲，适合想要一点活泼感的博客。',
    swatch: ['#527d00', '#5d8c00', '#a3e635'],
  },
  {
    id: 'mint',
    name: '薄荷冰',
    en: 'Mint Frost',
    desc: '薄荷绿到冰蓝的渐变，清爽通透，夏天感最强的一套。',
    swatch: ['#0d8464', '#0891b2', '#2dd4bf'],
  },
  {
    id: 'sage',
    name: '鼠尾草灰绿',
    en: 'Sage Neutral',
    desc: '灰绿中性色，几乎没有彩度，配任何图片都稳，最不容易看腻。',
    swatch: ['#4c6b58', '#4c6b58', '#a9bfae'],
  },
  {
    id: 'aurora',
    name: '极光青绿',
    en: 'Aurora Teal',
    desc: '青绿到紫的极光渐变，梦幻有个性，适合想要一点记忆点的博客。',
    swatch: ['#0b7a8c', '#7c5cff', '#22d3ee'],
  },
  {
    id: 'ink',
    name: '青墨',
    en: 'Ink Green',
    desc: '近黑的墨底配一点青，几乎看不到绿但很耐看，偏「暗夜工作台」气质。',
    swatch: ['#1f4f40', '#1f4f40', '#6ee7c4'],
  },
]

export const THEME_IDS = THEME_OPTIONS.map((t) => t.id)
