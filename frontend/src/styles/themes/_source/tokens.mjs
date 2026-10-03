/**
 * 主题输入表 - 唯一事实来源
 *
 * 这里只声明"每套主题想表达什么":
 *   primary  品牌色(按钮/链接/选中态/热力图)
 *   bg       页面画布底色
 *   gradFrom / gradTo  可选, 覆盖推导出来的装饰渐变两端
 *   termAccent         可选, 覆盖终端里的强调色
 *
 * 其余令牌(文字/边框/卡片/代码底/语义色/终端底色)由 derive.mjs 在统一的中性基准上
 * 推导, 所以 9 套主题的视觉语言完全一致, 换主题只换品牌色与画布
 *
 * 生成与校验:
 *   node _source/generate-themes.mjs   (或 npm run themes:generate)
 *   node _source/audit.mjs             (或 npm run themes:audit)
 *
 * 对比度约定(推导层已保证, audit 会复核):
 *   --link       主色当文字用时 >= 4.5:1
 *   --on-primary 主色填充上的文字 >= 4.5:1
 *   --grad-from  渐变起点属于装饰图形, 只要求与主色肉眼可辨
 */

export { COLOR_KEYS } from './derive.mjs'

export const THEMES = [
  {
    id: 'cuanmu',
    name: '预设',
    en: 'Preset',
    desc: '中性灰阶 + 近黑品牌色, 白面板配浅灰画布, 最接近参考稿的默认外观',
    light: { primary: '#262626', bg: '#ededed' },
    dark: { primary: '#e8e8e8', bg: '#151515' },
  },
  {
    id: 'neon',
    name: '霓虹青柠',
    en: 'Neon Lime',
    desc: '荧光青柠品牌色, 灰白画布上只留一抹开发者气质',
    light: { primary: '#5f9c00', bg: '#f0f1ea' },
    dark: { primary: '#a3e635', bg: '#0e100c' },
  },
  {
    id: 'moss',
    name: '苔原手记',
    en: 'Moss Editorial',
    desc: '苔绿品牌色配微暖画布, 安静耐读',
    light: { primary: '#3f6b4a', bg: '#eeefe9' },
    dark: { primary: '#9dbfa4', bg: '#121512' },
  },
  {
    id: 'mist',
    name: '晨雾青',
    en: 'Morning Mist',
    desc: '冷调青绿品牌色, 低饱和, 干净克制',
    light: { primary: '#0e7a70', bg: '#ecefee' },
    dark: { primary: '#2fd4bd', bg: '#0a1413' },
  },
  {
    id: 'sage',
    name: '鼠尾草灰绿',
    en: 'Sage Neutral',
    desc: '灰绿品牌色, 几乎没有彩度, 配任何图片都稳',
    light: { primary: '#52705f', bg: '#eeeeec' },
    dark: { primary: '#a9bfae', bg: '#151715' },
  },
  {
    id: 'aurora',
    name: '极光青绿',
    en: 'Aurora Teal',
    desc: '青绿品牌色, 带一点海面反光的通透感',
    light: { primary: '#0a7d97', bg: '#ecf0f1' },
    dark: { primary: '#22d3ee', bg: '#0a1216' },
  },
  {
    id: 'lilac',
    name: '雾紫',
    en: 'Lilac Mist',
    desc: '低饱和紫罗兰品牌色配冷白画布, 安静通透',
    light: { primary: '#6a5acd', bg: '#eeeef3' },
    dark: { primary: '#9388d2', bg: '#141319' },
  },
  {
    id: 'sailblue',
    name: '黛蓝',
    en: 'Slate Navy',
    desc: '黛蓝品牌色, 几乎没有彩度, 最像纸质书的安静配色',
    light: { primary: '#35597f', bg: '#ecedf0' },
    dark: { primary: '#91adca', bg: '#141719' },
  },
  {
    id: 'graphite',
    name: '石墨',
    en: 'Graphite Brass',
    desc: '石墨灰品牌色, 中性克制, 适合以文字和图片为主的博客',
    light: { primary: '#414951', bg: '#eeeeec' },
    dark: { primary: '#a6adb5', bg: '#161718' },
  },
]
