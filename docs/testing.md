# 测试与检查说明(testing.md)

> 本文档说明项目的测试分层, 用例分布, 检查脚本, 一键验证与 CI 流水线, 以及新增代码时测试该写在哪里 
> 相关文档: [技术架构与实现说明](./architecture.md), [接口设计](./api.md), [数据库表结构](./mysql.md), [更新日志](../CHANGELOG.md) 

## 1. 分层与原则

| 层 | 工具 | 位置 | 是否依赖真实服务 |
| --- | --- | --- | --- |
| 后端单元与接口测试 | pytest + 内存 SQLite | `backend/tests/` | 不连 MySQL, 不起 HTTP 服务 |
| 前端单元与组件测试 | Vitest + jsdom | `frontend/src/**/*.test.ts` | 不发真实请求(接口层整体 mock) |
| 静态一致性检查 | Node / Python 脚本 | `frontend/scripts/`, `backend/scripts/` | 只有 `backend/scripts/check_*.py` 需要开发库(只读) |
| 代码检查与格式化 | ruff, ESLint, Prettier | `backend/ruff.toml`, `frontend/eslint.config.js`, `frontend/.prettierrc.json` | 不需要 |
| 类型检查与构建 | vue-tsc, vite build | `frontend/` | 不需要 |
| 持续集成 | GitHub Actions | `.github/workflows/` | 在干净容器里重跑上面这些 |

选用例的标准不是覆盖率数字, 而是"改错会被拦住" 优先给这三类逻辑补用例: 

- 分支多, 改错了在界面上看不出来的(状态推导, 分页, 排序, 时间格式化) 
- 涉及越权与安全边界的(匿名读私密文章, 上传白名单, 静态资源鉴权) 
- 已经真实出过 bug 的(回归测试, 见 3.3) 

## 2. 后端测试(pytest)

### 2.1 运行

```powershell
cd backend
pip install -r requirements-dev.txt
python -m pytest tests -q
```

- 测试依赖与生产依赖分开: `backend/requirements-dev.txt` 只比 `requirements.txt` 多 `ruff 0.16.8`, `pytest 9.1.1` 与 `httpx 0.28.1` 
- 配置在 `backend/pytest.ini`: `testpaths = tests`, `python_files = test_*.py`, 默认带 `-q`, 并忽略 `DeprecationWarning` 
- 用例直接调用路由函数与 service(必要时用一个最小的 Request 替身), 不启动 HTTP 服务, 因此不占端口也不需要网络 

### 2.2 装置 `tests/conftest.py`

| 装置 | 作用 |
| --- | --- |
| `db_session` | 每个用例一套全新的内存 SQLite 与独立 Session |
| `seeded` | 在 `db_session` 上建好权限 / 角色 / 管理员 / 作者的最小数据集, 返回 `(admin, author, 明文密码)` |

内存库的四个要点(文件头注释里也写着, 改动前先读那里): 

- 用 `sqlite://` 加 `StaticPool`, 不碰开发用的 MySQL - 测试必须能随便跑 
- 模型的 `BigInteger` 主键在 SQLite 上不会自增, 用 `@compiles(BigInteger, "sqlite")` 编译成 `INTEGER` 
- 连接时执行 `PRAGMA foreign_keys=ON`, 让级联删除的行为与 MySQL 一致 
- `PHXXBLOG_SECRET_KEY` 必须在导入 `app.core.config` 之前用 `setdefault` 设好, 否则会被 `.env` 覆盖 

### 2.3 用例清单

`backend/tests/test_core_rules.py`, 14 条, 都是"核心业务规则与安全断言"的回归测试: 

| 用例 | 断言的行为 |
| --- | --- |
| `test_private_post_not_readable_by_anonymous` | 匿名读私密文章返回 404(不是 403, 不暴露"存在但不可见") |
| `test_author_cannot_publish_directly` | 无 `post:publish` 的作者提交 `status=2` 被降级为审核中 |
| `test_refresh_token_is_single_use` | 刷新令牌轮换后旧令牌失效(重放检测) |
| `test_upload_rejects_scriptable_extensions` | 上传拒绝 `.html` / `.svg` / `.js` 等可执行文档(同源托管等于存储型 XSS) |
| `test_upload_rejects_fake_image_by_magic_bytes` | HTML 改名成 `.png` 也要按文件头拦下 |
| `test_public_post_detail_has_no_author_ip` | 公开详情响应不含作者 `ip` / `location` |
| `test_record_visit_keeps_post_updated_at` | 记录阅读量不得改动 `Post.updated_at` |
| `test_assets_access_control_rule` | `/assets` 下只有前台会渲染的媒体匿名可访问, 其余仅管理员 |
| `test_post_neighbors_and_hot_ranking` | 上一篇 / 下一篇按发布时间相邻, 热门榜按阅读量倒序 |
| `test_login_rate_limiter_blocks_after_threshold` | 登录连续失败达到阈值后返回 429 |
| `test_post_can_have_multiple_categories` | 一篇文章属于多个分类时, 写入 / 筛选 / 分类计数都按关联表来 |
| `test_post_import_reports_and_skips_duplicates` | 文章导入按标题查重: 查重结果与实际落库条数必须一致, 重复项按策略跳过 |
| `test_diary_import_dedups_by_content_ignoring_whitespace` | 日记导入按正文查重, 空白差异不算不同内容(与库中及本批内容都比对) |
| `test_diary_import_can_import_duplicates_on_demand` | 选择"导入全部"时, 重复内容必须真的写入库中 |

### 2.4 新增用例

- 文件放在 `backend/tests/`, 命名 `test_*.py`; 需要数据库时在参数里带上 `db_session`, 需要账号时再加 `seeded` 
- 断言错误码时用 `pytest.raises(HTTPException)` 检查 `status_code`, 不要只判断"有没有抛异常" 
- 与现有主题相关的新分支, 优先在 `test_core_rules.py` 里按主题追加一条, 不另起文件 

## 3. 前端测试(Vitest)

### 3.1 运行

```powershell
cd frontend
npm run test            # 单次
npm run test:watch      # 监听
npm run test:coverage   # 覆盖率报告 -> coverage/index.html
```

`coverage/` 不入库(见 `frontend/.gitignore`) 覆盖率口径写在 `vitest.config.ts`: 统计 `src/**/*.{ts,vue}`, 排除 `*.d.ts`, `src/types/**` 与 `src/main.ts` 

### 3.2 配置

- 配置在**独立**的 `frontend/vitest.config.ts`, 不是 `vite.config.ts`: 后者带 Element Plus 按需引入插件, 该插件在测试时会改写 `src/components.d.ts` - 跑个测试就把源码改了 测试配置只保留 Vue 单文件组件编译与 `@` 别名 
- 默认环境 `jsdom`(组件与 DOM 相关用例需要), 纯函数用例可在文件顶部加 `// @vitest-environment node` 换到更快的 node 环境 
- 收集范围 `src/**/*.{test,spec}.{ts,js}` 与 `tests/**/*.{test,spec}.{ts,js}`; 测试文件与被测代码**同目录**, 命名 `*.test.ts` 
- `css: false`, 不解析样式 

### 3.3 用例清单

10 个文件 73 条: 

| 文件 | 覆盖内容 |
| --- | --- |
| `src/utils/datetime.test.ts` | 时间格式化(全站列表与详情共用, 改动影响面大) |
| `src/utils/mediaGrid.test.ts` | 媒体网格的尺寸与分页计算 |
| `src/utils/mediaPreview.test.ts` | 预览类型判定(图片 / 视频 / 音频 / PDF / 文本) |
| `src/utils/trendRange.test.ts` | 访问趋势的时间范围, 环比与汇总 |
| `src/composables/usePostEditor.test.ts` | 文章编辑流程: 状态推导, 分类 / 标签就地新建, 删除取消不误删, 封面上传复位 |
| `src/composables/useImportExport.test.ts` | 导入查重分支, 导入后刷新, 导出下载与失败回滚 |
| `src/composables/usePagedList.test.ts` | 列表分页: 翻页与"回到第 1 页"各只请求一次, 请求失败也要复位 loading |
| `src/api/http.test.ts` | 401 静默刷新: 重放原请求, 并发只刷新一次, 防循环, 刷新失败才登出 |
| `src/views/DiaryView.test.ts` | **回归**: Vditor 组字期间 `v-model` 落后时, 保存必须取编辑器内容 |
| `src/views/SearchView.test.ts` | **回归**: 被 keep-alive 缓存的组件在 `route.query` 变化时必须重新检索 |

`DiaryView` 与 `SearchView` 两组是针对真实 bug 写的 后者用真实 router 反复 push 不同 query 复现 keep-alive 场景, 验证方式是: 把组件里响应 route 变化的那段逻辑删掉, 用例会失败(`expected length 3 but got 5`), 所以不是"假绿" 

### 3.4 写法要点

composable 的断言方式, Axios 假 adapter 的用法, Element Plus 组件的桩与全局指令, 以及 `http.ts` 里模块级单飞 Promise 会污染后续用例这类坑, 都记在 `frontend/README.md` 的「测试」一节, 新增用例前先读那里 

## 4. 检查脚本

用例之外, 还有一批脚本兜住"类型检查与单测都发现不了"的问题 

### 4.1 前端

| 命令 | 检查什么 | 什么时候会失败 |
| --- | --- | --- |
| `npm run themes:audit` | 主题自检: 令牌是否齐全, 生成的 `theme-*.css` 是否与 `tokens.mjs` 一致, 深浅两种模式的关键配色是否满足 WCAG AA(4.5:1) 等 | 改了 `src/styles/themes/_source/tokens.mjs` 却忘记 `npm run themes:generate` |
| `npm run check:icons` | 按 SVG 规范给 `MetaIcon` 的 path 分词, 再逐段核对命令参数个数 | 手写 path 时出现 `7.5.5` 这类"数字粘连", 笔画画不出来但页面不报错 |
| `npm run check:element-styles` | 扫描源码里用到的程序式 API(`ElMessage` / `ElMessageBox` 等), 核对 `main.ts` 是否 import 了对应样式 | 按需引入下漏了样式行, 确认框会变成没有遮罩的裸按钮 |
| `npm run check:size` | 打印首屏与整包体积(未压缩 / gzip 后) | 不判失败, 用来发现体积回退; 需先 `npm run build` |
| `npm run check:lint` | ESLint 静态检查(配置在 `eslint.config.js`) | 出现未使用的导入或变量, 无效赋值, 模板属性顺序不合规 |
| `npm run check:format` | Prettier 格式检查(配置在 `.prettierrc.json`) | 代码未按统一格式书写; `npm run format` 可自动修 |

### 4.2 后端

`backend/scripts/` 下这几个脚本只读开发库或磁盘, 不写数据, 但需要能连上开发用的 MySQL: 

| 脚本 | 检查什么 |
| --- | --- |
| `check_query_counts.py` | 关键接口的 SQL 条数(验证关联加载策略) |
| `check_list_query_counts.py` | 分类 / 标签接口的 SQL 条数(验证 n+1 优化) |
| `check_media_paths.py` | `media` 表的 `url` / `path` 与磁盘文件是否对得上 |
| `check_upload_path.py` | `resolve_upload_file` 的路径校验(含旧实现会漏掉的绕过用例) |
| `check_settings_keys.py` | 设置项的后端默认值, 公开键列表, 前端类型与后台表单四处的键是否一致(不需要数据库) |

### 4.3 后端静态检查与格式化(ruff)

配置在 `backend/ruff.toml`, 选了哪些规则集, 忽略了什么, 都写在文件注释里: 

| 命令 | 作用 |
| --- | --- |
| `ruff check .` | 静态检查: 未使用的导入 / 变量, 无效赋值, 裸 `except`, 导入排序, bugbear 常见陷阱 |
| `ruff check --fix .` | 自动修可自动修的部分(其余需要手工处理) |
| `ruff format .` | 按统一风格格式化, 行宽 100 |

三处刻意的排除, 改配置前先看这里: 

- `app/services/ip2region/` 是第三方绑定, 整体不检查也不格式化, 便于与上游比对 
- `app/models/*.py` 忽略 `F821`: SQLAlchemy 的关系用字符串前向引用跨模块类型名, 这些名字在本文件里没有导入 
- `scripts/gen_api_doc.py` 忽略 `W291`: 它里面的多行字符串就是要写进 `docs/api.md` 的正文, 行尾空格是文档约定 

## 5. 一键验证与 CI

### 5.1 `verify_all.py`

```powershell
cd backend
.venv/Scripts/python.exe scripts/verify_all.py
```

把散落在各处的检查串起来跑一遍并打印汇总表, 退出码非 0 即有用例或检查失败 目前 13 项: 

| 分组 | 检查 |
| --- | --- |
| 后端 | `import app.main` 可导入 |
| 后端 | `python -m pytest tests -q` |
| 后端 | 启动即校验表结构(`missing_columns()` 为空) |
| 后端 | `scripts/check_settings_keys.py`(设置项的默认值, 公开键, 前端类型与表单一致) |
| 后端 | `ruff check .` 与 `ruff format --check .` |
| 前端 | `npx vue-tsc -b --force` |
| 前端 | `npm run test` |
| 前端 | `npm run themes:audit` |
| 前端 | `npm run check:icons` |
| 前端 | `npm run check:element-styles` |
| 前端 | `npx eslint .` 与 `npm run check:format` |

它假设后端虚拟环境在 `backend/.venv`(`Scripts/python.exe`), 前端依赖已经 `npm install` 不跑 `npm run build` 与 `npm run check:size`, 这两条只在本节 5.2 与手工验证时跑 

### 5.2 `.github/workflows/ci.yml`

两个 job, 与本地检查一一对应: 

| job | 内容 |
| --- | --- |
| `backend` | Python 3.11 加 `requirements-dev.txt`, 依次跑 `ruff check .`, `ruff format --check .`, 再带 `PHXXBLOG_SECRET_KEY` 环境变量跑 `python -m pytest tests -q`(内存 SQLite, 不需要 MySQL 服务) |
| `frontend` | Node 版本取自仓库根 `.nvmrc`, `npm ci` 后依次跑 `themes:audit`, `check:icons`, `check:element-styles`, `check:lint`, `check:format`, `vue-tsc -b --force` 加 `npm run test`, 最后 `npm run build` 加 `check:size` |

- 触发条件: push 到 `main`, pull request, 以及手动 `workflow_dispatch` 
- 路径过滤同时覆盖 `backend/**` 与 `frontend/**` - 只写 `backend/**` 时单独改前端不会触发任何检查(这是修过的漏洞) 
- Node 版本必须与 `frontend/package.json` 的 `engines` 一致: jsdom 30 依赖 undici 8, 而 undici 8 需要 Node 22.19 才有的 `node:worker_threads.markAsUncloneable`, 在旧版本上所有测试文件都起不来 

### 5.3 `.github/workflows/build-frontend.yml`

push 到 `main` 后构建前端, 并把 `frontend/dist` 以孤立提交强推到 `built` 分支(该分支只含最新一次构建产物) 它不跑测试, 但会让"构建失败"在最外层暴露出来 

## 6. 未覆盖范围与手工验证

下面这些没有自动化用例, 改动后需要手工过一遍: 

| 范围 | 为什么没有用例 | 手工验证方式 |
| --- | --- | --- |
| 真实 MySQL 上的建表与迁移脚本 | CI 里只有 SQLite | 在开发库执行 `backend/scripts/migration_*.sql` 后重启后端, 启动时的表结构校验会报出缺失列 |
| 浏览器里的渲染与交互(Vditor, Element Plus 弹窗与下拉, 主题切换) | 前端测试跑在 jsdom 上, 没有布局与排版 | `npm run dev` 后按改动范围人工过一遍 |
| 需要 WebGL 的功能(看板娘) | 无头环境不一定有可用的 GPU | 打开前台, 确认形象加载, 拖动, 切换形象与开关都生效 |
| 静态资源鉴权在真实部署下的表现 | 用例只覆盖判定函数 | 用管理员与匿名两种身份各访问一次 `/assets` 下的渲染类与非渲染类文件, 对比状态码 |
| 打包体积 | 只在 CI 与本地手动跑 | `npm run build` 后 `npm run check:size` |

## 7. 与测试相关的约定

- 修 bug 时先补一条能复现的用例再改代码; 确实写不成用例的(渲染, 交互)在最终说明里给出复现与验证步骤 
- 新增分支多或涉及安全边界的逻辑时补用例; 纯样式与文案调整不补 
- 测试不连真实数据库, 不发真实外部请求; 需要外部依赖时用替换实现, 不要为了省事放宽这条 
- 新增检查脚本时同时接进 `verify_all.py` 与 `.github/workflows/ci.yml`, 保证本地与 CI 跑的是同一套 
- 格式问题交给工具: 后端 `ruff format .`, 前端 `npm run format` 不要手工对齐空格或换行去迎合检查 
- 踩过的坑记在就近的位置(`backend/tests/conftest.py` 的文件头, `frontend/vitest.config.ts` 与相关脚本的注释, `frontend/README.md` 的「测试」一节), 不要只留在提交信息里 
