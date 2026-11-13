export declare const countMatches: (text: string, query: string, caseSensitive: boolean) => number;
export declare const findText: (element: HTMLElement, query: string, caseSensitive: boolean, index?: number) => IFindResult;
export declare const replaceText: (element: HTMLElement, query: string, replacement: string, caseSensitive: boolean, index?: number) => number;
export declare const displayRange: (range: Range) => Range;
