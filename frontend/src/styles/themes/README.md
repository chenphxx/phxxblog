# 主题系统(9 套, 均含深色 / 浅色)

针对 `frontend/`(Vue 3 + Element Plus)的整套换肤方案 **不改任何 `.vue` 组件的结构**, 靠 CSS 令牌 + 一层增强样式覆盖现有类名实现 前台与后台共用同一套主题 

- **默认主题: 预设**(`cuanmu`) - 中性灰阶 + 静蓝主色, 令牌取自 VitePress + Teek 预设 
- 另含 8 套可选主题(冷调与中性色为主), 可在顶栏随时切换 

## 字体

字母 / 数字 / 符号统一使用 **Cascadia Code**(自托管 latin 子集, 见 `src/styles/fonts.css`): 

```css
--font-sans: 'Cascadia Code', 'Cascadia Mono', ui-monospace, 'PingFang SC', 'Microsoft YaHei', …;
--font-mono: 'Cascadia Code', 'Cascadia Mono', 'JetBrains Mono', ui-monospace, Consolas, …;
```

Cascadia Code 不含中文字形, 因此中文会自动回退到后面的系统字体(PingFang SC / 微软雅黑), 中文排版质量不受影响 - 得到的效果是"西文数字符号等宽, 中文标准无衬线" 

> 注意: Vditor 自带的 `.vditor-reset` 写死了字体栈且不引用 `var(--font-sans)`, 正文的字体由 `theme.css` 里同特异性的 `.markdown-body, .vditor-reset` 规则覆盖, 那条规则不要删 

## 先看效果

```powershell
npm run themes:preview     # 生成到 src/styles/themes/_preview/
```

打开 `_preview/index.html`: 左侧 9 套主题列表, 右侧实时预览, 右上角切换深色/浅色(也支持 ↑↓ 键换主题) 

预览页的样式是从 `theme-*.css` **原样抽取**生成的, 所以预览效果 = 实际效果 `_preview/` 是产物, 已加入 `.gitignore`, 可随时重建 

## 默认主题: 预设 (cuanmu)

令牌逐项对照来源, 便于日后核对: 

| 本项目令牌 | 值(浅色 / 深色) | 来源 |
| --- | --- | --- |
| `--bg` | `#f6f6f7` / `#1b1b1f` | VitePress `--vp-c-bg-alt`; 深色用 Teek `--tk-home-bg-color` |
| `--card-bg` | `#ffffff` / `#202127` | VitePress `--vp-c-bg` / `-bg-soft`, `-bg-elv` |
| `--text` | `#3c3c43` / `#dfdfd6` | `--vp-c-text-1` |
| `--muted` | `#67676c` / `#9facba` | `--vp-c-text-2`; 深色用 Teek `--tk-text-color-secondary` |
| `--border` / `--border-strong` | `#e2e2e3` / `#2e2e32`, `#c2c2c4` / `#3c3f44` | `--vp-c-divider`, `--vp-c-border` |
| `--link` | `#3451b2` / `#a8b1ff` | `--vp-c-indigo-1`(品牌文字) |
| `--primary` / `--primary-strong` | `#3a5ccc` / `#3e63dd`, `#3451b2` / `#5c73e7` | `--vp-c-indigo-2` / `-3` |
| `--ok` / `--warn` / `--danger` | `#18794e` / `#3dd68c` 等 | `--vp-c-green-1` / `-yellow-1` / `-red-1` |
| `--radius` | `8px` | Teek 卡片圆角 `--tk-home-card-border-radius` 的量级 |

设计语言(增强层族 `minimal`)刻意保持克制: 细边框, 极淡阴影, **不使用位移与硬阴影**, 只做颜色与边框的过渡 - 与文档站一致 

一处必要的偏离: 浅色主按钮底色用了 `--vp-c-indigo-2`(`#3a5ccc`)而不是 `-3`(`#5672cd`) 后者白字对比度只有 4.48:1, 略低于 WCAG AA 的 4.5; 换成 `-2` 后为 5.86:1, 仍在同一套 VitePress 色板内 

## 9 套主题

按"增强层风格"分四族, 同族共享同一套动效语言, 只有配色与圆角/阴影参数不同: 

| 族 | 视觉语言 | 动效 | 主题 |
| --- | --- | --- | --- |
| **minimal** 文档极简 | 中性灰阶, 细边框, 极淡阴影 | 仅颜色/边框过渡, 360ms | **预设 `cuanmu`(默认)**, 雾紫 `lilac`, 黛蓝 `sailblue` |
| **soft** 柔和抬升 | 渐变主色, 大圆角(10–16px), 多层柔和阴影 | 卡片上浮 + 左侧色条生长, 220ms | 晨雾青 `mist` |
| **hard** 硬朗位移 | 纯色主色, 方正小圆角(6–12px), 偏移硬阴影, 等宽标题 | 悬停位移 + 终端扫描线, 170ms | 霓虹青柠 `neon`, 极光青绿 `aurora` |
| **editorial** 编辑细线 | 衬线标题, 极淡阴影, 细线分割 | 标题细线浮现 + 轻微抬升, 280ms | 苔原手记 `moss`, 鼠尾草灰绿 `sage`, 石墨 `graphite` |

每套都: 

- 有完整的深色与浅色两套令牌(`html[data-theme='<id>']` 与 `html[data-theme='<id>'].dark`) 
- 同步改写 **Element Plus** 的 `--el-*` 令牌(色阶由主色自动推导)→ 按钮, 输入框, 分页, 弹窗, 消息跟随主题, 不用改组件 
- 补上了原 `theme.css` 缺失的贡献热力图令牌 `--cell-0`~`--cell-4`(之前会退回 GitHub 默认绿, 深色下尤其违和) 
- 在 `prefers-reduced-motion: reduce` 下自动关掉动效 
- 通过 WCAG AA 对比度校验(见下) 

## 默认主题与裸 `:root`

`<html>` 上的 `data-theme` 由 `stores/theme.ts` 维护 **未选过主题的新访客**拿不到任何 `html[data-theme=...]` 匹配, 靠的是 `theme-default.css` 里的裸 `:root` 浅色令牌 

因此有一条硬约定: **只有 `theme-default.css` 能写颜色级裸 `:root`**, 其余主题一律只写 `html[data-theme='<id>']` - 否则后加载的那套会覆盖默认主题 `npm run themes:audit` 会检查这一点, 也会核对 `theme-default.css` 与 `registry.ts` 的 `DEFAULT_THEME` 是否一致 

想换默认主题: 把 `_source/tokens.mjs` 里想用的那套挪到 `THEMES` 数组第一位, 重新生成即可 

## 运行时切换(已接入)

顶栏的主题按钮(`components/ThemeSwitcher.vue`)下拉里就是这 9 套, 只显示"色点 + 主题名", 选中即生效并记入 `localStorage`; 旁边的圆形按钮单独切换深色/浅色 两者互相独立, 前台与后台共用 

```
stores/theme.ts
  themeId      当前主题 id，持久化在 blog_theme_style
  isDark       深色模式，持久化在 blog_theme
  setTheme(id) 换主题
  toggle()     换深浅
```

切换时会临时给 `<html>` 加 `theme-transition` 类, 让颜色平滑过渡 首屏不闪的保证在 `main.ts` 顶部: 挂载前就读 `localStorage` 并写入 `data-theme` 与 `.dark` 

## 后台如何跟随主题

后台原本依赖 Element Plus 默认蓝, 与前台是两套体系 `src/styles/admin.css` 负责打通: 

```css
:root {
  --el-color-primary: var(--primary);
  --el-color-primary-light-3: color-mix(in srgb, var(--primary) 70%, var(--card-bg));
  /* …以及边框/文字/填充色全套 */
}
```

它必须在所有主题之后加载(见 `theme-green.css` 的 `@import` 顺序), 且在 `:root` 上以同特异性后写入, 才能覆盖 Element Plus 与各主题自带的 `--el-color-primary` 

## 改配色

9 套主题**全部由一份数据生成**, 不要手改生成的 CSS: 

```
src/styles/themes/_source/
  tokens.mjs                                        ← 唯一事实来源（每套的浅色/深色令牌）
  template.css                                      ← 令牌文件骨架
  enhance.base.css                                  ← 增强层公共部分
  enhance-{soft,hard,editorial,minimal}.css         ← 四族的差异部分
  generate-themes.mjs  audit.mjs  build-previews.mjs
  _gallery-template.html                            ← 预览总览页模板
```

```powershell
npm run themes:generate   # 生成 10 个 CSS(9 套 + theme-default) + registry.ts
npm run themes:audit      # 校验
npm run themes:preview    # 生成 18 个预览页 + 总览
```

`themes:audit` 会检查: 

1. 每套主题深浅两模式的令牌是否齐全, 颜色格式是否正确 
2. 生成的 `theme-*.css` 是否与 `tokens.mjs` 一致(防止忘了重新生成) 
3. `theme-default.css` 是否等于默认主题的浅色令牌, 是否只有它写了颜色级裸 `:root` 
4. 链接色 / 主按钮文字 / 正文 / 次要文字的对比度是否 ≥ 4.5:1(WCAG AA) 
5. 用渐变装饰的族, 渐变两端是否有肉眼可辨的差异 
6. 任意两套主题的主色是否过于接近(仅警告) 

### 三个容易踩的令牌约定

"同一个颜色既当填充又当文字"是最常出问题的地方 - 亮色配白字, 或亮色当链接色, 都会掉到 3:1 左右 所以每套主题都单独导出: 

| 令牌 | 用途 | 例子 |
| --- | --- | --- |
| `--on-primary` | 主色**填充**之上的文字色 | 霓虹青柠浅色主按钮用深墨字 `#0A1405`(5.60:1), 而不是白字(3.36:1) |
| `--link` | 主色当**文字/链接**用时的颜色, 可深于主色 | 雾紫链接用 `#5c4ac8`(6.42:1), 按钮填充仍是 `#6a5acd` |
| `--grad-from` / `--grad-to` | 装饰色带两端, 纯装饰, 只需两端可辨 | 苔原手记浅色 `#7FA888 → #3F6B4A` |

## 只想固定用一套?

把 `styles/theme-green.css` 里多余的 `@import` 注释掉, 并移除 `SiteLayout.vue` / `AdminLayout.vue` 里的 `<ThemeSwitcher />` 即可 全部引入的代价很小: 9 套令牌 gzip 后约 13 KB 

## 目录

```
src/styles/
  theme.css                    原有结构样式（卡片、正文、终端、时间轴、代码块）
  theme-green.css              主题入口：theme.css + theme-default.css + 9 套主题 + admin.css
  admin.css                    后台主题层（Element Plus 主色 → 主题令牌）
  fonts.css                    自托管 Cascadia Code
  themes/
    theme-default.css          默认主题的裸 :root 令牌（生成物）
    theme-<id>.css             ×9，生成物，勿手改
    registry.ts                主题清单（生成物），供下拉菜单与类型使用
    _source/                   主题源与脚本（见上）
    _preview/                  预览产物（不入库，可重建）
```

## 与项目原有实现的改动点

除了新增主题文件, 为了让运行时切换成立, 改了若干既有文件: 

1. `main.ts`: 挂载前同时恢复深浅色与主题(`data-theme`), 未选过时回退 `cuanmu`; 并引入自托管字体 
2. `stores/theme.ts`: 新增 `themeId` 与 `setTheme()`, 与 `isDark` 共同决定 DOM 状态 
3. `layouts/SiteLayout.vue` 与 `views/admin/AdminLayout.vue`: 把原来的 `<ThemeToggle />` 换成 `<ThemeSwitcher />` 
4. `views/HomeView.vue`: 终端会话按钮的悬停底色原本写死 `#16222b`(偏蓝), 改为由 `--term-*` 令牌推导 
5. `views/admin/DashboardView.vue`: 数据卡片与图例的写死颜色改为主题令牌 
6. `components/MetaIcon.vue`: 新增元信息图标组件(日历/眼睛/标签等), 跟随主题文字色 

`components/ThemeToggle.vue` 仍被登录页 `views/admin/LoginView.vue` 使用(那里只放一个圆形按钮更合适), 因此保留 
