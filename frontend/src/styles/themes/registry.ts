/**
 * 主题清单 - 由 src/styles/themes/_source/generate-themes.mjs 生成, 请勿手改
 * 改主题请改 _source/tokens.mjs 后运行 npm run themes:generate
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
  /** 预览用的两个代表色, 供下拉菜单左侧色点显示(品牌色 + 画布色) */
  swatch: string[]
}

export const DEFAULT_THEME: ThemeId = 'cuanmu'

export const THEME_OPTIONS: ThemeOption[] = [
  {
    id: 'cuanmu',
    name: '预设',
    en: 'Preset',
    desc: '中性灰阶 + 近黑品牌色, 白面板配浅灰画布, 最接近参考稿的默认外观',
    swatch: ['#262626', '#ededed'],
  },
  {
    id: 'neon',
    name: '霓虹青柠',
    en: 'Neon Lime',
    desc: '荧光青柠品牌色, 灰白画布上只留一抹开发者气质',
    swatch: ['#5f9c00', '#f0f1ea'],
  },
  {
    id: 'moss',
    name: '苔原手记',
    en: 'Moss Editorial',
    desc: '苔绿品牌色配微暖画布, 安静耐读',
    swatch: ['#3f6b4a', '#eeefe9'],
  },
  {
    id: 'mist',
    name: '晨雾青',
    en: 'Morning Mist',
    desc: '冷调青绿品牌色, 低饱和, 干净克制',
    swatch: ['#0e7a70', '#ecefee'],
  },
  {
    id: 'sage',
    name: '鼠尾草灰绿',
    en: 'Sage Neutral',
    desc: '灰绿品牌色, 几乎没有彩度, 配任何图片都稳',
    swatch: ['#52705f', '#eeeeec'],
  },
  {
    id: 'aurora',
    name: '极光青绿',
    en: 'Aurora Teal',
    desc: '青绿品牌色, 带一点海面反光的通透感',
    swatch: ['#0a7d97', '#ecf0f1'],
  },
  {
    id: 'lilac',
    name: '雾紫',
    en: 'Lilac Mist',
    desc: '低饱和紫罗兰品牌色配冷白画布, 安静通透',
    swatch: ['#6a5acd', '#eeeef3'],
  },
  {
    id: 'sailblue',
    name: '黛蓝',
    en: 'Slate Navy',
    desc: '黛蓝品牌色, 几乎没有彩度, 最像纸质书的安静配色',
    swatch: ['#35597f', '#ecedf0'],
  },
  {
    id: 'graphite',
    name: '石墨',
    en: 'Graphite Brass',
    desc: '石墨灰品牌色, 中性克制, 适合以文字和图片为主的博客',
    swatch: ['#414951', '#eeeeec'],
  },
]

export const THEME_IDS = THEME_OPTIONS.map((t) => t.id)
