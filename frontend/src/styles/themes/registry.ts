/**
 * 主题清单 —— 由 src/styles/themes/_source/generate-themes.mjs 生成, 请勿手改。
 * 改主题请改 _source/tokens.mjs 后运行 npm run themes:generate。
 */

export type ThemeId =
  | 'cuanmu'
  | 'neon'
  | 'moss'
  | 'mist'
  | 'sage'
  | 'aurora'
  | 'lilac'
  | 'sailblue'
  | 'graphite'

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
    id: 'lilac',
    name: '雾紫',
    en: 'Lilac Mist',
    desc: '雾紫配冷白，低饱和的紫罗兰点缀，安静、通透，接近纸质印刷的克制感。',
    swatch: ['#6a5acd', '#6a5acd', '#9388d2'],
  },
  {
    id: 'sailblue',
    name: '黛蓝',
    en: 'Slate Navy',
    desc: '冷白配黛蓝，几乎没有彩度，最像纸质书的安静配色。',
    swatch: ['#35597f', '#35597f', '#91adca'],
  },
  {
    id: 'graphite',
    name: '石墨',
    en: 'Graphite Brass',
    desc: '石墨灰配黄铜点缀，中性克制，适合以文字和图片为主的博客。',
    swatch: ['#414951', '#6d6a60', '#a6adb5'],
  },
]

export const THEME_IDS = THEME_OPTIONS.map((t) => t.id)
