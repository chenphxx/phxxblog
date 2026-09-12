# 绿色系博客主题方案（3 套）

纯静态 HTML 参考稿，每套都是完整首页，自带 **深色 / 浅色切换**（右上角按钮，选择记忆在 `localStorage`）。

打开 `design/index.html` 查看总览：三张卡片内嵌实时预览，可单独切换每张预览的深浅色。

| 文件                   | 主题       | 气质          | 适合方向            |
| -------------------- | -------- | ----------- | --------------- |
| `theme-emerald.html` | A · 清新翡翠 | 清爽、亲切、产品感   | 教程、入门向技术博客、个人主页 |
| `theme-neon.html`    | B · 霓虹青柠 | 高能量、硬朗、态度鲜明 | 技术专栏、观点长文、独立开发者 |
| `theme-sage.html`    | C · 森林墨绿 | 安静、刊物感、耐读   | 随笔、设计观察、长文阅读站   |

---

## A · 清新翡翠 Emerald Fresh

- 强调色：浅色 `#0F9D58`，深色 `#34D980`；辅助色 `#0D9488`
- 背景：`#F5FAF7` / `#06110D`
- 字体：Plus Jakarta Sans + Noto Sans SC
- 手法：柔和玻璃拟态、大圆角、渐变标题、背景网格与光斑、卡片悬停上浮
- 结构：Hero + 数据条 → 精选大图文 → 三列文章网格 → 订阅 → 页脚

## B · 霓虹青柠 Neon Lime

- 强调色：浅色 `#7FC400`，深色 `#C7F53D`；辅助色 `#23E0B0`
- 背景：`#F4F6EC` / `#0B0C0A`
- 字体：Archivo Black（大标题）+ Inter（正文）+ JetBrains Mono（标签）
- 手法：Bento 网格、硬阴影（offset shadow）、荧光高亮块、跑马灯、等宽小标签、噪点质感
- 结构：跑马灯 → 超大字 Hero + 参数面板 → Bento 精选 → 编号列表 → 订阅 → 页脚

## C · 森林墨绿 Sage Editorial

- 强调色：苔绿 `#4A6B52`（深色下提亮为 `#8FBF9A`）；点缀陶土色 `#B5654A`
- 背景：`#F4F5ED` / `#101711`
- 字体：Fraunces + Noto Serif SC（衬线为主）
- 手法：杂志分栏、细分割线与粗标题线、手绘感 SVG 山景插画、引语区、大留白
- 结构：Hero（图文并置）→ 编辑部精选（主文 + 侧栏）→ 图文卡片 → 引语 → 订阅 → 页脚

---

## 实现约定（三套一致）

1. **主题切换**：`<html data-theme="light|dark">`，所有颜色声明为 CSS 变量，两套变量各写一份。
2. **防闪烁**：`<head>` 内联脚本最早读取 `localStorage` + `prefers-color-scheme` 并写入 `data-theme`。
3. **表单控件跟随**：`:root` 与两套变量里都声明 `color-scheme`。
4. **预览联动**：主题页监听 `postMessage({ type:'set-theme', theme })`，总览页据此控制 iframe 预览。
5. **动效降级**：`prefers-reduced-motion: reduce` 时关闭浮现动画与平滑滚动。
6. **无障碍**：切换按钮有 `aria-label`，正文与背景对比度保持 4.5:1 以上。

## 迁移到框架时

- 变量集中在 `<style>` 顶部的两个块里，抽成 `tokens.css` 或 Tailwind 的 `theme.extend.colors` 即可。
- 各区块（导航 / Hero / 精选 / 卡片 / 订阅 / 页脚）边界清晰，可按此顺序拆成组件。
- 插画均为内联 SVG，直接替换成自己的封面图或组件即可。

## 本地预览

```powershell
start design\index.html              # 通用落地页示例（3 套主题）
start design\previews\index.html     # 针对本项目 Vue 组件的 11 套主题预览
```

> `design/*.html`（3 套落地页示例）是早期的通用设计稿；
> 真正接进项目的是 `design/previews/` 里的 11 套主题，对应 `frontend/src/styles/themes/`。
> 主题的生成与校验脚本在 `design/themes/`：

```powershell
node design/themes/generate-themes.mjs   # 由 tokens.mjs 生成 11 个 theme-*.css
node design/themes/audit.mjs             # 校验令牌齐全性与 WCAG 对比度
node design/previews/build-previews.mjs  # 重新生成 22 个预览页
```
