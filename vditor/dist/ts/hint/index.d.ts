/// <reference types="./types" />
export declare class Hint {
    timeId: number;
    element: HTMLDivElement;
    recentLanguage: string;
    private splitChar;
    private lastIndex;
    private requestId;
    private dismiss;
    constructor(hintExtends: IHintExtend[]);
    hide(): void;
    destroy(): void;
    render(vditor: IVditor): void;
    genHTML(data: IHintData[], key: string, vditor: IVditor): void;
    fillEmoji: (element: HTMLElement, vditor: IVditor) => void;
    select(event: KeyboardEvent, vditor: IVditor): boolean;
    private getKey;
}
