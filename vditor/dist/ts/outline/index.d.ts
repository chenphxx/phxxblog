/// <reference types="./types" />
export declare class Outline {
    element: HTMLElement;
    resizeElement: HTMLElement;
    constructor(outlineLabel: string);
    bindResize(vditor: IVditor): void;
    render(vditor: IVditor): string;
    toggle(vditor: IVditor, show?: boolean, focus?: boolean): void;
}
