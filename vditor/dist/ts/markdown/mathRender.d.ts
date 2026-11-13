declare global {
    interface Window {
        MathJax: {
            loader?: {
                paths: {
                    mathjax: string;
                };
            };
            startup: {
                typeset?: boolean;
                promise?: Promise<void>;
                document?: {
                    clear(): void;
                    updateDocument(): void;
                };
            };
            tex?: {
                macros: object;
            };
            getMetricsFor?(element: Element): {
                display?: boolean;
            };
            tex2svgPromise?(math: string, options: {
                display?: boolean;
            }): Promise<Element>;
        };
    }
}
export declare const mathRender: (element?: (HTMLElement | Document), options?: {
    cdn?: string;
    math?: IMath;
}) => void;
