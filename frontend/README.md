# 前端 (Vue 3 + TypeScript + Vite + Element Plus)

## 开发

```powershell
npm install
npm run dev      # http://localhost:5173, /api 等请求代理到 FastAPI (localhost:8000)
npm run build    # vue-tsc 类型检查 + vite build
npm run check:icons   # 校验 MetaIcon 的 SVG path 是否合法
```

## 开发环境注意事项

### 改了文件不用重启服务

Vite 的 HMR 工作正常，改 `.vue` / `.css` 都会自动生效。**如果发现"必须重启才生效"，先别急着重启——大概率是进程被杀了**，可以用下面两条确认：

```powershell
Get-NetTCPConnection -State Listen | Where-Object LocalPort -eq 5173   # 有没有在监听
npm run dev                                                            # 没有就是被杀了, 重新起
```

### 曾经有一个"改配置就崩"的坑（已修）

在 Windows 上改动 `vite.config.ts` 会导致 dev server **直接退出**：

```
Error: EBUSY: resource busy or locked, watch
  '...\.vite.config.ts.<pid>.<guid>.tmpdir\vite.config.ts.tmp'
    at FSWatcher._handleError
    at NodeFsHandler._addToNodeFs
```

原因：config 变更时 Vite 会写一个临时配置文件再去 `watch` 它，而该文件在 Windows 上常被占用 → `fs.watch` 抛 `EBUSY` → `FSWatcher` 的 `error` 事件没人处理 → 进程未捕获异常退出。

已在 `vite.config.ts` 的 `server.watch.ignored` 里把这些临时文件排除掉，实测改配置不再崩溃。**这段忽略规则不要删**，否则每次改配置都要重启。

### `npm run build` 不会影响 dev server

`dist/` 与 `.vite/` 已在 `watch.ignored` 中排除。否则 build 写盘时 dev server 会收到大量 change 事件并触发整页刷新，看起来像"服务出问题了"。

## 目录约定

```
src/
  components/MetaIcon.vue   元信息小图标(日历/眼睛/标签…), 内联 SVG + currentColor
  styles/
    theme.css               结构样式与基础令牌
    theme-green.css         主题入口: 引入 theme.css + theme-default.css + 各主题
    themes/                 主题令牌(生成物, 勿手改) + registry.ts
  stores/theme.ts           深浅色 + 配色主题(持久化到 localStorage)
```

主题共 12 套、每套都有深色与浅色，生成与改配色的说明见
[`src/styles/themes/README.md`](src/styles/themes/README.md)。
主题的源数据在 `design/themes/tokens.mjs`，改完运行：

```powershell
node design/themes/generate-themes.mjs   # 生成 CSS 与 registry
node design/themes/audit.mjs             # 校验令牌齐全性与 WCAG 对比度
```
