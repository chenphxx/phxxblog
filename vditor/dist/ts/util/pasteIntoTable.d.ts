export declare const parseMarkdownTableRows: (text: string) => string[][] | null;
export declare const pasteIntoTable: (vditor: IVditor, html: string, markdown?: string) => boolean;
export declare const buildTableSelectionClipboard: (vditor: IVditor, range: Range) => {
    html: string;
    plain: string;
};
