# 前端 (Vue 3 + TypeScript + Vite + Element Plus)

## Node 版本要求

**必须 Node >= 22.19**, CI 与本地统一用仓库根目录 `.nvmrc` 里的版本(当前 24) 
`npm ci` 在更低的版本上会打出 `EBADENGINE` 警告, 装了 nvm / fnm 的话直接: 

```powershell
nvm use            # 读取根目录 .nvmrc
```

下限写在 `package.json` 的 `engines.node`, 改版本时 `.nvmrc`, `engines` 与两个 workflow 要一起改 
(workflow 用 `node-version-file: '.nvmrc'`, 不会再各自写死) 

## 开发

```powershell
npm install
npm run dev            # http://localhost:5173, /api 等请求代理到 FastAPI (localhost:8000)
npm run build          # vue-tsc 类型检查 + vite build
npm run check:icons    # 校验 MetaIcon 的 SVG path 是否合法
npm run check:element-styles  # 校验程序式 Element Plus 组件是否补了样式
npm run check:size     # 打印首屏/整包体积(先 npm run build)
npm run check:lint     # ESLint 静态检查
npm run lint:fix       # ESLint 自动修复
npm run format         # Prettier 格式化 src 与 scripts
npm run check:format   # 只检查格式, 不写文件(CI 用)
```

### 代码检查与格式化

- ESLint 配置在 `eslint.config.js`(扁平配置), Prettier 配置在 `.prettierrc.json`: 
  单引号, 无分号, 行宽 120, 与项目原有写法保持一致 
- 只开能自动拦截缺陷的规则, 格式类规则交给 Prettier(`eslint-config-prettier` 关掉冲突项); 
  类型检查仍由 `vue-tsc` 负责, 因此没有启用 typescript-eslint 的类型感知规则(那需要 project 配置, 明显更慢) 
- 不进检查也不格式化的只有生成物与主题源 CSS(见 `.prettierignore`): `dist/`, `src/components.d.ts`, `src/styles/themes/*.css` 与 `registry.ts`(生成器产出), 以及 `_source/*.css` 
  (主题源样式直接决定生成结果, 要改格式就必须连 9 套主题的观感一起重新核对) 
- 主题的生成脚本 `_source/*.mjs` 与画廊模板照常检查与格式化, 它们按 Node 环境处理(用到 `console`/`process`) 

## 开发环境注意事项

### 按需引入下, 程序式组件的样式要手动加(踩过)

Element Plus 改成按需引入后, `vite.config.ts` 的 `ElementPlusResolver` 只能看到**模板里的标签** 
`ElMessageBox.confirm()` / `ElMessage.success()` 是 JS 调用, 解析器看不到, **样式不会自动进来**: 

- 确认框变成页面左上角一堆裸按钮(截图里就是这样), 没有遮罩也没有圆角; 
- 提示条(`ElMessage`)完全不可见 - 界面上看起来"点了没反应" 

这类问题 `vue-tsc` 发现不了, 所以在 `main.ts` 里显式引入, 并用脚本兜底: 

```ts
import 'element-plus/es/components/message-box/style/css'
import 'element-plus/es/components/message/style/css'
```

```powershell
npm run check:element-styles   # 扫源码里用到的程序式 API, 核对 main.ts 是否引入对应样式
```

再加 `ElNotification` / `ElLoading` 之类的程序式 API 时, 先跑这个脚本它会直接告诉你缺哪一行 

### 编辑器里的内容以 `getValue()` 为准(踩过)

用 `VditorEditor` 的表单, **保存前必须读编辑器实例的当前值**, 不要只信 `v-model`: 
Vditor 在中文输入法组字期间会跳过 `input` 回调(`vditor/src/ts/ir/index.ts` 的 `composingLock`), 
于是存在"编辑器里已经有字, 但 model 还是空"的一瞬间 这时候点保存会命中空值判断直接 return, 
表现就是"新增日记要点两次保存" 

```ts
const editorRef = ref<InstanceType<typeof VditorEditor> | null>(null)
const content = editorRef.value?.getValue() ?? form.value.content_md
```

`DiaryView.vue` / `PostFormFields.vue` 都按这个模式处理 

### 改了文件不用重启服务

Vite 的 HMR 工作正常, 改 `.vue` / `.css` 都会自动生效 **如果发现"必须重启才生效", 先别急着重启 - 大概率是进程被杀了**, 可以用下面两条确认: 

```powershell
Get-NetTCPConnection -State Listen | Where-Object LocalPort -eq 5173   # 有没有在监听
npm run dev                                                            # 没有就是被杀了, 重新起
```

### 曾经有一个"改配置就崩"的坑(已修)

在 Windows 上改动 `vite.config.ts` 会导致 dev server **直接退出**: 

```
Error: EBUSY: resource busy or locked, watch
  '...\.vite.config.ts.<pid>.<guid>.tmpdir\vite.config.ts.tmp'
    at FSWatcher._handleError
    at NodeFsHandler._addToNodeFs
```

原因: config 变更时 Vite 会写一个临时配置文件再去 `watch` 它, 而该文件在 Windows 上常被占用 → `fs.watch` 抛 `EBUSY` → `FSWatcher` 的 `error` 事件没人处理 → 进程未捕获异常退出 

已在 `vite.config.ts` 的 `server.watch.ignored` 里把这些临时文件排除掉, 实测改配置不再崩溃 **这段忽略规则不要删**, 否则每次改配置都要重启 

### `npm run build` 不会影响 dev server

`dist/` 与 `.vite/` 已在 `watch.ignored` 中排除 否则 build 写盘时 dev server 会收到大量 change 事件并触发整页刷新, 看起来像"服务出问题了" 

## 目录约定

```
src/
  components/MetaIcon.vue   元信息小图标(日历/眼睛/标签...), 内联 SVG + currentColor
  components/Kanbanniang*.vue 看板娘浮层(可按住形象本体拖动)与顶栏的形象下拉/开关
  components/home/          首页的模块组件: 每个模块自己取数, 自己转圈, 开关由 HomeView 判断
  composables/              跨视图复用逻辑(usePostEditor / useImportExport / usePagedList)
  api/http.ts               拦截器: 附加令牌 / 解包 / 401 静默刷新(单飞, 见文件内注释)
  utils/tokenStorage.ts     令牌与用户信息的唯一读写入口(不要在别处写 localStorage 的 key 字面量)
  styles/
    theme.css               结构样式与基础令牌
    app.css                 样式入口: 引入 theme.css + layout.css + 默认令牌 + 各主题 + admin.css
    admin.css               后台主题层: Element Plus 主色接到主题令牌
    fonts.css               自托管 Cascadia Code 的 @font-face
    themes/                 主题令牌(生成物, 勿手改) + registry.ts
      _source/              主题源: tokens.mjs / 模板 / 增强层 / 生成与校验脚本
      _preview/             预览页产物(不入库, 可用 npm run themes:preview 重建)
  stores/theme.ts           深浅色 + 配色主题(持久化到 localStorage)
  stores/kanbanniang.ts     看板娘开关, 形象与浮层位置(持久化到 localStorage), 以及后台总开关的下发
  kanbanniang/              形象清单(registry.ts)与运行时加载(loader.ts)
```

看板娘的形象与运行时自托管在 `public/kanbanniang/`, 来源与本地化改动见 
[`public/kanbanniang/README.md`](public/kanbanniang/README.md) 

主题共 9 套, 每套都有深色与浅色, 生成与改配色的说明见 
[`src/styles/themes/README.md`](src/styles/themes/README.md) 
主题的源数据在 `src/styles/themes/_source/tokens.mjs`: 

```powershell
npm run themes:generate   # 由 tokens.mjs 生成 10 个 CSS + registry.ts
npm run themes:audit      # 校验令牌齐全性, 默认主题一致性, WCAG 对比度
npm run themes:preview    # 生成 18 个预览页到 _preview/
```
