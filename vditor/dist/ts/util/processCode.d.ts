export declare const isPlainTextPaste: (html: string, editorData: string) => boolean;
export declare const processPasteCode: (html: string, text: string, type?: string) => string | false;
export declare const highlightEditableCode: (previewPanel: HTMLElement, vditor: IVditor) => void;
export declare const processCodeRender: (previewPanel: HTMLElement, vditor: IVditor) => void;
