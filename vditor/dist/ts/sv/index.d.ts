/// <reference types="./types" />
declare class Editor {
    element: HTMLTextAreaElement;
    composingLock: boolean;
    processTimeoutId: number;
    pendingUndoStack: boolean;
    constructor(vditor: IVditor);
    private bindEvent;
}
export { Editor };
