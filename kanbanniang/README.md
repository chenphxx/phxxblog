# 看板娘资源

前台顶栏可以开关看板娘并切换形象, 资源全部自托管在这个目录, 运行时不请求任何外部地址 

## 来源

### kanbanniang

- 仓库: <https://github.com/Vanessa219/kanbanniang>(MIT) 
- 运行时 `live2d.js`: 取自该仓库 `assets/kanbanniang/live2d.js`(即 npm 包 `kanbanniang@0.2.12`), 是 Live2D Cubism 2.0 的 WebGL 运行时, 对外暴露全局函数 `loadlive2d(canvasId, modelJsonPath)` 
- 模型: 取自该仓库 `model/` 目录, 清单见下表 

| 形象 | 目录 | 来源包 |
| --- | --- | --- |
| Pio | `model/Potion-Maker/Pio/` | 模型与动作 `kanbanniang`, 默认服装纹理 `kanbanniang-pio` |
| Tia | `model/Potion-Maker/Tia/` | 模型与动作 `kanbanniang`, 默认服装纹理 `kanbanniang-tia` |
| Murakumo | `model/KantaiCollection/murakumo/` | `kanbanniang` |
| Shizuku | `model/ShizukuTalk/shizuku-48/` | 模型与动作 `kanbanniang`, 纹理在 `kanbanniang-tia` |
| Shizuku Pajama | `model/ShizukuTalk/shizuku-pajama/` | 模型在 `kanbanniang`, 纹理在 `kanbanniang-tia`, 动作与 physics 引用同系列的 `shizuku-48` |
| Blanc | `model/HyperdimensionNeptunia/blanc_normal/` | `kanbanniang`, 纹理与 physics 引用同系列的 `blanc_classic`, pose 与动作引用 `general/` |
| 22娘 | `model/bilibili-live/22/` | `kanbanniang`, 默认服装纹理取自该目录 `texture_00` ~ `texture_03` |
| 33娘 | `model/bilibili-live/33/` | 同上 |

上游共 26 个模型(分布在 5 个系列), 这里收了其中 8 个 剩下的 18 个全部属于 `HyperdimensionNeptunia` 系列, 是同一批角色的服装与配色变体, 单套 2 MB 上下, 
且会跨目录引用兄弟目录的纹理与 `general/` 下的动作, 默认不收录 需要时按下面「新增一个形象」的步骤把引用一起拷进来 

上面的 8 个之外还有 Miku, 上游没有, 取自另一个来源(见下), 因此本项目共 9 个形象 

### Miku

- 包: npm `live2d-widget-model-miku@1.0.5`, 仓库 <https://github.com/xiazeyu/live2d-widget-models> 
- 上面的 kanbanniang 仓库没有这个形象, 这个模型取自这个包, 包声明 GPL-2.0 
- 目录: `model/miku/`, 模型 json 里原本相对模型目录的路径已改写成本项目运行时的相对路径形式(`model/miku/...`), 并补了取景用的 `layout`(见下) 
- 上游该包只有 `miku.model.json`(动作组为 `null` 与 `idle`, 无摸头动作), 这里原样保留 

模型版权属于原作者 上游 README 注明「所有模型的版权均属于原作者, 仅供研究学习, 不得用于商业用途」- 这里只做自托管, 未修改任何模型数据 

## 相对上游做的改动

上游把模型基址写死在运行时里, 模型 json 里的纹理也写成 unpkg 绝对地址, 直接搬过来会请求外部 CDN, 与本项目「字体, 编辑器等静态资源一律自托管」的做法冲突 因此只做了这几处本地化处理: 

1. `live2d.js` 里唯一一处 `this.modelHomeDir="https://unpkg.com/kanbanniang@0.2.12/"` 改成 `this.modelHomeDir="/kanbanniang/"`, 其余代码未动 
   运行时把模型 json 里的路径统一拼在这个基址后面, 于是 `model/...` 会解析到 `/kanbanniang/model/...` 
2. 模型 json 里的 `https://unpkg.com/kanbanniang*/` 前缀去掉, 变成相对基址的路径(如 `model/KantaiCollection/murakumo/textures.1024/00.png`) 
3. `Potion-Maker/Pio`、`Potion-Maker/Tia` 与 `bilibili-live/22`、`bilibili-live/33` 上游 `index.json` 的 `textures` 是空数组(上游靠 `textures.json` 在运行时换装, 这个运行时读不到), 
   这里显式补上纹理路径: Pio / Tia 用 `textures/default-costume.png`, 22娘 / 33娘 用上游 `textures.json` 的第一套服装(`texture_00` ~ `texture_03` 各一张) 
4. Miku 的 `miku.model.json` 里是相对模型目录的路径(`moc/miku.moc` 等), 改写成相对本目录的写法(`model/miku/moc/miku.moc` 等), 并补了取景用的 `layout` 

只保留形象实际用到的文件: 上游的 `textures.json`(未使用的换装表), 各套服装里没用到的纹理, 以及 Solo 博客用的 `index.js` / `index.css` / `tips.json` 都没有搬进来 

## 画布与取景

浮层默认是 280x250 的画布, 多数模型取的是头肩近景, 这个尺寸刚好 尺寸在 `src/kanbanniang/registry.ts` 里按形象配置(可选的 `canvas` 字段), 取景由模型 json 的 `layout` 决定 

Miku 是全身像, 280x250 只能看到膝盖以上, 因此给它单独配了 280x420 的画布, 并把 `layout` 调成 `{ center_x: 0, center_y: 0.03, width: 2.2 }`, 让头到脚填满这块画布 
新加形象时如果默认画布装不下(或人物明显偏小), 同样按这个思路调 `canvas` 与 `layout` 

## 新增一个形象

1. 从上游仓库把整个模型目录拷到 `model/<系列>/<名字>/`, 只保留 `index.json`, `model.moc`, `motions/`, `expressions/`, `physics.json`, `pose.json`, `textures*/` 
2. 把这批 json 里的 `https://unpkg.com/kanbanniang*/` 前缀去掉 
3. 若 `index.json` 的 `textures` 为空或指向外部地址, 改成该模型实际使用的纹理相对路径 
4. 在 `src/kanbanniang/registry.ts` 的 `KANBANNIAN_MODELS` 里追加一条(`id` / `name` / `series` / `path`) 

搬运前先确认模型是否自包含: 上游 `HyperdimensionNeptunia` 系列多数模型会跨目录引用兄弟目录的纹理与 `general/pose.json`, 只拷单个目录会缺文件; 
`bilibili-live`, `ShizukuTalk` 等目录的纹理在 `kanbanniang-pio` / `kanbanniang-tia` 包里, 且 `index.json` 的 `textures` 需要按第 3 步补全 
把某套系列里能互相引用的模型一起搬时, 保持它们在 `model/` 下的相对位置不变, 引用才不需要改写 

## 相关代码

```
src/kanbanniang/registry.ts              形象清单(这里加形象)
src/kanbanniang/loader.ts                运行时按需加载 + loadlive2d 调用封装
src/stores/kanbanniang.ts                开关, 形象与浮层位置的持久化(localStorage), 以及后台总开关的下发
src/components/Kanbanniang.vue           看板娘本体(固定浮层 + canvas, 按住形象本体拖动)
src/components/KanbanniangSwitcher.vue   顶栏的形象下拉与开关
```
