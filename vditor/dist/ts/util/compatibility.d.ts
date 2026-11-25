export declare const isSafari: () => boolean;
export declare const isFirefox: () => boolean;
export declare const accessLocalStorage: () => boolean;
export declare const getEventName: () => "click" | "touchstart";
export declare const isCtrl: (event: Pick<KeyboardEvent, "ctrlKey" | "metaKey">) => boolean;
export declare const updateHotkeyTip: (hotkey: string) => string;
export declare const isChrome: () => boolean;
