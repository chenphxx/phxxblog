/**
 * @brief 看板娘形象清单。
 *
 * 形象资源全部自托管在 frontend/public/kanbanniang/ 下(来源与本地化改动见该目录的 README),
 * 运行时不请求任何外部地址。新增形象时按那份 README 把模型目录放进去, 再在下面的数组里追加一条即可。
 */

/** 资源基址, 与 vite 的 public 目录一致 */
export const BASE_URL = '/kanbanniang/'

/** 一个可选形象 */
export interface KanbanniangModel {
  /** 形象标识, 持久化在 localStorage */
  id: string
  /** 下拉里显示的名字(沿用模型/角色的原始名称, 不另行翻译或改写) */
  name: string
  /** 出自哪套模型系列, 显示在下拉项名字后面 */
  series: string
  /** 模型 json 相对 BASE_URL 的路径 */
  path: string
  /** 画布尺寸, 省略时用默认的 280x250; 全身像这类瘦高的模型需要更高的画布 */
  canvas?: { width: number; height: number }
}

export const KANBANNIAN_MODELS = [
  { id: 'pio', name: 'Pio', series: 'Potion-Maker', path: 'model/Potion-Maker/Pio/index.json' },
  { id: 'tia', name: 'Tia', series: 'Potion-Maker', path: 'model/Potion-Maker/Tia/index.json' },
  { id: 'murakumo', name: 'Murakumo', series: '舰队 Collection', path: 'model/KantaiCollection/murakumo/index.json' },
  { id: 'shizuku', name: 'Shizuku', series: 'ShizukuTalk', path: 'model/ShizukuTalk/shizuku-48/index.json' },
  {
    id: 'shizuku-pajama',
    name: 'Shizuku Pajama',
    series: 'ShizukuTalk',
    path: 'model/ShizukuTalk/shizuku-pajama/index.json',
  },
  {
    id: 'blanc',
    name: 'Blanc',
    series: 'HyperdimensionNeptunia',
    path: 'model/HyperdimensionNeptunia/blanc_normal/index.json',
  },
  { id: 'bilibili-22', name: '22娘', series: 'bilibili-live', path: 'model/bilibili-live/22/index.json' },
  { id: 'bilibili-33', name: '33娘', series: 'bilibili-live', path: 'model/bilibili-live/33/index.json' },
  // 唯一不来自 Vanessa219/kanbanniang 的形象, 取自 live2d-widget-models 的 live2d-widget-model-miku 包
  // 它是全身像: 在默认的 280x250 画布里只能看到膝盖以上, 因此单独给一块更高的画布
  {
    id: 'miku',
    name: 'Miku',
    series: 'Hatsune Miku',
    path: 'model/miku/miku.model.json',
    canvas: { width: 280, height: 420 },
  },
] as const satisfies readonly KanbanniangModel[]

export type KanbanniangModelId = (typeof KANBANNIAN_MODELS)[number]['id']

export const MODEL_IDS: readonly KanbanniangModelId[] = KANBANNIAN_MODELS.map((model) => model.id)

/** 未选过形象时的默认形象 */
export const DEFAULT_MODEL_ID: KanbanniangModelId = KANBANNIAN_MODELS[0].id
