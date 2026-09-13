# 前端 (Vue 3 + TypeScript + Vite + Element Plus)

## Node 版本要求

**必须 Node >= 22.19**，CI 与本地统一用仓库根目录 `.nvmrc` 里的版本（当前 24）。
`npm ci` 在更低的版本上会打出 `EBADENGINE` 警告，装了 nvm / fnm 的话直接：

```powershell
nvm use            # 读取根目录 .nvmrc
```

原因值得记一笔，因为它踩过：测试环境用的 `jsdom@30` 依赖 `undici@8`，而 undici 8 需要
`node:worker_threads.markAsUncloneable`（Node 22.19 才有）。用 Node 20 跑测试时，jsdom 在**加载阶段**
就崩，报错是这个，而且**每个测试文件都报同一条**：

```
TypeError: webidl.util.markAsUncloneable is not a function
  at new CacheStorage (node_modules/undici/lib/web/cache/cachestorage.js:20:17)
  at ... jsdom/lib/api.js:12
```

看着像测试代码有问题，其实是 Node 版本不对。见到这条报错先 `node -v`，不要改测试。
下限写在 `package.json` 的 `engines.node`，改版本时 `.nvmrc`、`engines` 与两个 workflow 要一起改
（workflow 用 `node-version-file: '.nvmrc'`，不会再各自写死）。

## 开发

```powershell
npm install
npm run dev            # http://localhost:5173, /api 等请求代理到 FastAPI (localhost:8000)
npm run build          # vue-tsc 类型检查 + vite build
npm run test           # vitest 单次运行
npm run test:watch     # 监听模式(开发时用)
npm run test:coverage  # 覆盖率报告 -> coverage/index.html
npm run check:icons    # 校验 MetaIcon 的 SVG path 是否合法
npm run check:size     # 打印首屏/整包体积(先 npm run build)
```

## 测试

用 **Vitest**（与 Vite 共用配置与解析规则，无需另配 Jest）。

- 配置在独立的 `vitest.config.ts`，**不是** `vite.config.ts`：后者带 Element Plus 按需引入插件，
  而该插件在测试时会试图解析组件并改写 `src/components.d.ts` —— 跑个测试就把源码改了，不合适。
  测试配置只保留必需的两项：Vue 单文件组件编译 + `@` 别名。
- 默认环境是 `jsdom`（组件与 DOM 测试需要）。纯函数测试可在文件顶部加
  `// @vitest-environment node` 换到更快的 node 环境。
- 测试文件与被测代码同目录，命名 `*.test.ts`。

### 已有用例

| 文件 | 覆盖内容 |
| --- | --- |
| `src/utils/datetime.test.ts` | 时间格式化（全站列表/详情共用，改动影响面大） |
| `src/composables/usePostEditor.test.ts` | 文章编辑流程：状态推导、分类/标签就地新建、删除取消不误删、封面上传复位 |
| `src/composables/useImportExport.test.ts` | 导入查重分支、导入后刷新、导出下载与失败回滚 |
| `src/api/http.test.ts` | 401 静默刷新：重放原请求、并发只刷新一次、防循环、刷新失败才登出 |
| `src/views/SearchView.test.ts` | **回归测试**：该组件被 keep-alive 缓存，切换 `route.query` 时必须重新检索 |

`SearchView` 那组用例是针对一个真实 bug 写的（URL 变了但列表不刷新）。它用真实 router
反复 push 不同 query 来复现 keep-alive 场景 —— 已验证：把组件里响应 route 变化的那段逻辑去掉，
用例会失败（`expected length 3 but got 5`），所以它不是"假绿"。

### 测试非组件逻辑（composable / 拦截器）

- composable 用 `reactive` 返回状态，可以直接 `editor.form.title = 'x'` 后断言，不需要渲染模板。
  但凡是内部调用了 `onMounted` 的（如 `usePostEditor`），**必须放进组件里调用**，
  否则 Vue 会警告"no active component instance"；为此用例里用一个只有 `setup()` 的空壳组件 `mount` 一下即可。
- 测 Axios 拦截器不要 mock axios 本身，而是给实例换一个假 adapter：
  `rawAxios.defaults.adapter = (config) => Promise.reject({ config, response: { status: 401, ... } })`。
  这样拦截器链路、重试、错误分支都是真实代码在跑。`http.ts` 导出 `refreshClient` 就是为了给刷新请求也装上假 adapter。
- ⚠️ `http.ts` 里有**模块级**的刷新 Promise（单飞）。若某个用例让刷新一直挂起，它会污染后续用例
  （表现为莫名其妙的 5s 超时）。用 `vi.waitFor()` 等状态，并在 `finally` 里释放挂起的 Promise。

### 写组件测试的三个注意点

1. Element Plus 组件在测试里无关紧要，用 `global.stubs` 桩掉；`v-loading` 是全局指令，
   还要给 `global.directives` 一个空实现，否则会有大量 `Failed to resolve directive` 警告。
2. 对外请求用 `vi.mock('@/api', ...)` 整体替换，不要引入真实 axios 实例（否则会真发请求）。
3. 断言渲染结果时优先用子组件的桩标记（如 `.post-stub`）而不是文字匹配，避免被样式或装饰文本干扰。

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
  composables/              跨视图复用逻辑(usePostEditor / useImportExport), 返回 reactive 对象
  api/http.ts               拦截器: 附加令牌 / 解包 / 401 静默刷新(单飞, 见文件内注释)
  utils/tokenStorage.ts     令牌与用户信息的唯一读写入口(不要在别处写 localStorage 的 key 字面量)
  styles/
    theme.css               结构样式与基础令牌
    theme-green.css         主题入口: 引入 theme.css + theme-default.css + 各主题
    admin.css               后台主题层: Element Plus 主色接到主题令牌
    fonts.css               自托管 Cascadia Code 的 @font-face
    themes/                 主题令牌(生成物, 勿手改) + registry.ts
      _source/              主题源: tokens.mjs / 模板 / 增强层 / 生成与校验脚本
      _preview/             预览页产物(不入库, 可用 npm run themes:preview 重建)
  stores/theme.ts           深浅色 + 配色主题(持久化到 localStorage)
```

主题共 12 套、每套都有深色与浅色，生成与改配色的说明见
[`src/styles/themes/README.md`](src/styles/themes/README.md)。
主题的源数据在 `src/styles/themes/_source/tokens.mjs`：

```powershell
npm run themes:generate   # 由 tokens.mjs 生成 13 个 CSS + registry.ts
npm run themes:audit      # 校验令牌齐全性、默认主题一致性、WCAG 对比度
npm run themes:preview    # 生成 24 个预览页到 _preview/
```
