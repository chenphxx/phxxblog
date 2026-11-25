/// <reference types="./types" />
export declare class Tip {
    private tips?;
    element: HTMLElement;
    private timeoutId;
    private positionTimeoutId;
    private visible;
    constructor(tips?: ICustomTips);
    show(text: string, time?: number): void;
    hide(): void;
}
