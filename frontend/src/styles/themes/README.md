# 主题系统(9 套, 均含深色 / 浅色)

针对 `frontend/`(Vue 3 + Element Plus)的整套换肤方案, 核心约定是:

> **主题只负责品牌色与画布底色, 其余一切都由统一的结构令牌决定**

所以换主题不会再改变圆角, 阴影, 字体气质或组件形态 - 只会换掉主色和页面底色 

## 视觉基调(Soft Minimal)

- 浅灰画布 + 白色大面板, 内容靠留白与细分隔线组织, 少用卡片嵌套 
- 圆角: 面板 `--radius-panel: 28px`, 卡片 `--radius-card: 20px`, 控件 `--radius-control: 12px`, 标签 `--radius-chip: 10px` 
- 阴影克制(`--shadow-panel` / `--shadow-float`), 深色下由 `html.dark` 单独加重 
- 字体分两档: UI 文字用系统无衬线(`--font-sans`), 代码块 / 终端 / 日期 / 计数用 `--font-mono`(Cascadia Code 自托管 latin 子集) 
- 入场动画全站只有一个 `fade-up`, 在 `styles/theme.css` 

这些结构令牌与主题无关, 全部由 `_source/derive.mjs` 的 `STRUCTURE_TOKENS` 定义, 生成到 `themes/base.css`, **全站只出现一份** 

## 每套主题声明什么

`_source/tokens.mjs` 里每套主题只给两套颜色(浅色 / 深色), 每套只有品牌色与画布色:

```js
{
  id: 'mist',
  name: '晨雾青',
  light: { primary: '#0e7a70', bg: '#ecefee' },
  dark: { primary: '#2fd4bd', bg: '#0a1413' },
}
```

可选字段: `gradFrom` / `gradTo`(装饰渐变两端, 默认由品牌色推导), `termAccent`(终端强调色, 默认由品牌色推导并保证可读) 

其余令牌全部由 `_source/derive.mjs` 推导: 卡片底色, 正文 / 次要 / 边框 / 代码底 / 语义色 / 终端 / 热力图 

| 令牌 | 浅色 | 深色 | 来源 |
| --- | --- | --- | --- |
| `--card-bg` | 恒为白色 | 画布色提亮 7% | 推导 |
| `--text` / `--muted` / `--border` | `#171717` / `#6b6b6b` / `#e6e6e6` | `#ededed` / `#a3a3a3` / `#2c2c2c` | 中性基准, **不随主题变化** |
| `--ok` / `--warn` / `--danger` | 固定 | 固定 | 语义色, 只区分深浅 |
| `--link` | 品牌色(必要时朝黑调整) | 品牌色(必要时朝白调整) | 保证 ≥ 4.5:1 |
| `--on-primary` | 白或近黑, 取对比度更高的一侧 | 同左 | 保证 ≥ 4.5:1 |
| `--cell-0..4` | 中性灰 -> 品牌色递进 | 深灰 -> 品牌色递进 | 推导, 梯度单调 |

## 先看效果

```powershell
npm run themes:preview     # 生成到 src/styles/themes/_preview/
```

打开 `_preview/index.html`: 左侧 9 套主题列表, 右侧实时预览, 右上角切换深色/浅色 

预览页注入的是真实的 `base.css` + `theme.css` + `layout.css` + 当前主题令牌, 所以**预览效果 = 实际效果** 
`_preview/` 是产物, 已加入 `.gitignore`, 可随时重建 

## 9 套主题

| 主题 | id | 浅色品牌色 | 画布 | 深色品牌色 |
| --- | --- | --- | --- | --- |
| 预设(默认) | `cuanmu` | `#262626` | `#ededed` | `#e8e8e8` |
| 霓虹青柠 | `neon` | `#5f9c00` | `#f0f1ea` | `#a3e635` |
| 苔原手记 | `moss` | `#3f6b4a` | `#eeefe9` | `#9dbfa4` |
| 晨雾青 | `mist` | `#0e7a70` | `#ecefee` | `#2fd4bd` |
| 鼠尾草灰绿 | `sage` | `#52705f` | `#eeeeec` | `#a9bfae` |
| 极光青绿 | `aurora` | `#0a7d97` | `#ecf0f1` | `#22d3ee` |
| 雾紫 | `lilac` | `#6a5acd` | `#eeeef3` | `#9388d2` |
| 黛蓝 | `sailblue` | `#35597f` | `#ecedf0` | `#91adca` |
| 石墨 | `graphite` | `#414951` | `#eeeeec` | `#a6adb5` |

## 默认主题与裸 `:root`

`<html>` 上的 `data-theme` 由 `stores/theme.ts` 维护 **未选过主题的新访客**拿不到任何 `html[data-theme=...]` 匹配, 靠的是 `theme-default.css` 里的裸 `:root` 浅色令牌 

因此有一条硬约定: **只有 `theme-default.css` 能写颜色级裸 `:root`**, 其余主题一律只写 `html[data-theme='<id>']` - 否则后加载的那套会覆盖默认主题 `npm run themes:audit` 会检查这一点, 也会核对 `theme-default.css` 与 `registry.ts` 的 `DEFAULT_THEME` 是否一致 

想换默认主题: 把 `_source/tokens.mjs` 里想用的那套挪到 `THEMES` 数组第一位, 重新生成即可 

## 运行时切换(已接入)

侧栏底部的主题按钮(`components/ThemeSwitcher.vue`)下拉里就是这 9 套, 只显示"色点 + 主题名", 选中即生效并记入 `localStorage`; 旁边的圆形按钮单独切换深色/浅色 两者互相独立, 前台与后台共用 

```
stores/theme.ts
  themeId      当前主题 id, 持久化在 blog_theme_style
  isDark       深色模式, 持久化在 blog_theme
  setTheme(id) 换主题
  toggle()     换深浅
```

切换时会临时给 `<html>` 加 `theme-transition` 类, 让颜色平滑过渡 首屏不闪的保证在 `main.ts` 顶部: 挂载前就读 `localStorage` 并写入 `data-theme` 与 `.dark` 

## 后台如何跟随主题

后台同样只吃主题令牌, 由 `src/styles/admin.css` 打通: 

```css
:root {
  --el-color-primary: var(--primary);
  --el-color-success: var(--ok);
  /* ...以及警告 / 危险 / 信息与各自的 light-N 色阶 */
}
```

它必须在所有主题之后加载(见 `theme-green.css` 的 `@import` 顺序), 且在 `:root` / `html:root` 上以同特异性后写入, 才能覆盖 Element Plus 自带的色阶 

## 改配色 / 改结构

```powershell
npm run themes:generate   # 生成 base.css + theme-default.css + 9 套 theme-<id>.css + registry.ts
npm run themes:audit      # 校验
npm run themes:preview    # 生成 18 个预览页 + 总览
```

只改颜色改 `_source/tokens.mjs`; 改圆角, 间距, 阴影, 动效, 字体改 `_source/derive.mjs` 的 `STRUCTURE_TOKENS` 

`themes:audit` 会检查: 

1. 每套主题的输入是否完整, 推导出的令牌是否齐全且格式正确 
2. 生成的 `theme-*.css` 是否与数据一致(防止忘了重新生成), 主题文件里有没有混进结构令牌 
3. `base.css` 是否写全了结构令牌, 且不含任何主题颜色 
4. `theme-default.css` 是否等于默认主题的浅色令牌, 是否只有它写了颜色级裸 `:root` 
5. 链接色 / 主按钮文字 / 正文 / 次要文字 / 悬停主色 / 装饰渐变两端是否达标(文字 4.5:1, 图形 3:1, 渐变两端需肉眼可辨) 
6. 任意两套主题的浅色品牌色是否过于接近(仅警告), 每套的深色品牌色是否比浅色更亮(仅警告) 

## 只想固定用一套?

把 `styles/theme-green.css` 里多余的 `@import` 注释掉, 再移除 `SiteLayout.vue` / `AdminLayout.vue` 里的 `<ThemeSwitcher />` 即可 
9 套颜色令牌都很短(每套约 2 KB), 全部引入的代价很小 

## 目录

```
src/styles/
  theme.css                  结构与组件样式(面板/列表行/正文/编辑器/Element Plus 细节)
  layout.css                 应用外壳(桌面侧栏 + 移动端抽屉 + 画布与主内容区)
  theme-green.css            主题入口: theme.css + layout.css + base.css + theme-default.css + 9 套主题 + admin.css
  admin.css                  后台主题层(Element Plus 令牌 -> 主题令牌, 后台外壳与表格)
  fonts.css                  自托管 Cascadia Code(只给 --font-mono 用)
  themes/
    base.css                 结构令牌与字体(生成物, 全站唯一一份)
    theme-default.css        默认主题的裸 :root 颜色令牌(生成物)
    theme-<id>.css           ×9, 只含颜色令牌(生成物)
    registry.ts              主题清单(生成物), 供下拉菜单与类型使用
    _source/                 主题源与脚本
      tokens.mjs             主题输入: 品牌色 + 画布色
      derive.mjs             令牌推导 + 结构令牌 + 对比度工具
      generate-themes.mjs    生成 base.css / theme-*.css / registry.ts
      audit.mjs              自检
      build-previews.mjs     预览页生成
      _gallery-template.html 总览页模板
    _preview/                预览产物(不入库, 可重建)
```
