/*!
 * Vditor v4.0.2-alpha.9 - A markdown editor written in TypeScript.
 *
 * MIT License
 *
 * Copyright (c) 2018-present B3log 开源, b3log.org
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */
/******/ var __webpack_modules__ = ({

/***/ 45
(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   l: () => (/* binding */ mediaRender)
/* harmony export */ });
/* harmony import */ var _util_function__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(210);

var replaceMedia = function (element, tag, url) {
    var media = element.ownerDocument.createElement(tag);
    if (tag === "iframe") {
        media.className = "iframe__video";
    }
    else {
        media.setAttribute("controls", "controls");
    }
    // 链接属性经 DOM 解码后可能包含引号，直接设置属性以保留 URL 的数据语义。
    media.setAttribute("src", url);
    element.replaceWith(media);
};
var iframeRender = function (element, url) {
    var youtubeMatch = url.match(/\/\/(?:www\.)?(?:youtu\.be\/|youtube\.com\/(?:embed\/|v\/|watch\?v=|watch\?.+&v=))([\w|-]{11})(?:(?:[\?&]t=)(\S+))?/);
    var youkuMatch = url.match(/\/\/v\.youku\.com\/v_show\/id_(\w+)=*\.html/);
    var qqMatch = url.match(/\/\/v\.qq\.com\/x\/cover\/.*\/([^\/]+)\.html\??.*/);
    var coubMatch = url.match(/(?:www\.|\/\/)coub\.com\/view\/(\w+)/);
    var facebookMatch = url.match(/(?:www\.|\/\/)facebook\.com\/([^\/]+)\/videos\/([0-9]+)/);
    var dailymotionMatch = url.match(/.+dailymotion.com\/(video|hub)\/(\w+)\?/);
    var bilibiliMatch = url.match(/(?:www\.|\/\/)bilibili\.com\/video\/(\w+)/);
    var tedMatch = url.match(/(?:www\.|\/\/)ted\.com\/talks\/(\w+)/);
    if (youtubeMatch && youtubeMatch[1].length === 11) {
        replaceMedia(element, "iframe", "//www.youtube.com/embed/".concat(youtubeMatch[1] +
            (youtubeMatch[2] ? "?start=" + youtubeMatch[2] : "")));
    }
    else if (youkuMatch && youkuMatch[1]) {
        replaceMedia(element, "iframe", "//player.youku.com/embed/".concat(youkuMatch[1]));
    }
    else if (qqMatch && qqMatch[1]) {
        replaceMedia(element, "iframe", "https://v.qq.com/txp/iframe/player.html?vid=".concat(qqMatch[1]));
    }
    else if (coubMatch && coubMatch[1]) {
        replaceMedia(element, "iframe", "//coub.com/embed/".concat(coubMatch[1], "?muted=false&autostart=false&originalSize=true&startWithHD=true"));
    }
    else if (facebookMatch && facebookMatch[0]) {
        replaceMedia(element, "iframe", "https://www.facebook.com/plugins/video.php?href=".concat(encodeURIComponent(facebookMatch[0])));
    }
    else if (dailymotionMatch && dailymotionMatch[2]) {
        replaceMedia(element, "iframe", "https://www.dailymotion.com/embed/video/".concat(dailymotionMatch[2]));
    }
    else if (url.indexOf("bilibili.com") > -1 && (url.indexOf("bvid=") > -1 || (bilibiliMatch && bilibiliMatch[1]))) {
        var params_1 = {
            bvid: (0,_util_function__WEBPACK_IMPORTED_MODULE_0__/* .getSearch */ .TK)("bvid", url) || (bilibiliMatch && bilibiliMatch[1]),
            page: "1",
            high_quality: "1",
            as_wide: "1",
            allowfullscreen: "true",
            autoplay: "0"
        };
        new URL(url.startsWith("http") ? url : "https:" + url).search.split("&").forEach(function (item, index) {
            if (!item) {
                return;
            }
            if (index === 0) {
                item = item.substr(1);
            }
            var keyValue = item.split("=");
            params_1[keyValue[0]] = keyValue[1];
        });
        var src_1 = "https://player.bilibili.com/player.html?";
        var keys_1 = Object.keys(params_1);
        keys_1.forEach(function (key, index) {
            src_1 += "".concat(key, "=").concat(params_1[key]);
            if (index < keys_1.length - 1) {
                src_1 += "&";
            }
        });
        replaceMedia(element, "iframe", src_1);
    }
    else if (tedMatch && tedMatch[1]) {
        replaceMedia(element, "iframe", "//embed.ted.com/talks/".concat(tedMatch[1]));
    }
};
var mediaRender = function (element) {
    if (!element) {
        return;
    }
    element.querySelectorAll("a").forEach(function (aElement) {
        var url = aElement.getAttribute("href");
        if (!url) {
            return;
        }
        if (url.match(/^.+.(mp4|m4v|ogg|ogv|webm)$/)) {
            replaceMedia(aElement, "video", url);
        }
        else if (url.match(/^.+\.(mp3|wav|flac|aac)(?:[?#].*)?$/i)) {
            replaceMedia(aElement, "audio", url);
        }
        else {
            iframeRender(aElement, url);
        }
    });
};


/***/ },

/***/ 57
(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   KJ: () => (/* binding */ hasClosestByClassName),
/* harmony export */   _Y: () => (/* binding */ hasClosestByMatchTag)
/* harmony export */ });
/* unused harmony exports hasTopClosestByClassName, hasTopClosestByAttribute, hasTopClosestByTag, getTopList, hasClosestByAttribute, hasClosestBlock, getLastNode */

var hasTopClosestByClassName = function (element, className) {
    var closest = hasClosestByClassName(element, className);
    var parentClosest = false;
    var findTop = false;
    while (closest && !closest.classList.contains("vditor-reset") && !findTop) {
        parentClosest = hasClosestByClassName(closest.parentElement, className);
        if (parentClosest) {
            closest = parentClosest;
        }
        else {
            findTop = true;
        }
    }
    return closest || false;
};
var hasTopClosestByAttribute = function (element, attr, value) {
    var closest = hasClosestByAttribute(element, attr, value);
    var parentClosest = false;
    var findTop = false;
    while (closest && !closest.classList.contains("vditor-reset") && !findTop) {
        parentClosest = hasClosestByAttribute(closest.parentElement, attr, value);
        if (parentClosest) {
            closest = parentClosest;
        }
        else {
            findTop = true;
        }
    }
    return closest || false;
};
var hasTopClosestByTag = function (element, nodeName) {
    var closest = hasClosestByTag(element, nodeName);
    var parentClosest = false;
    var findTop = false;
    while (closest && !closest.classList.contains("vditor-reset") && !findTop) {
        parentClosest = hasClosestByTag(closest.parentElement, nodeName);
        if (parentClosest) {
            closest = parentClosest;
        }
        else {
            findTop = true;
        }
    }
    return closest || false;
};
var getTopList = function (element) {
    var topUlElement = hasTopClosestByTag(element, "UL");
    var topOlElement = hasTopClosestByTag(element, "OL");
    var topListElement = topUlElement;
    if (topOlElement && (!topUlElement || (topUlElement && topOlElement.contains(topUlElement)))) {
        topListElement = topOlElement;
    }
    return topListElement;
};
var hasClosestByAttribute = function (element, attr, value) {
    if (!element) {
        return false;
    }
    if (element.nodeType === 3) {
        element = element.parentElement;
    }
    var e = element;
    var isClosest = false;
    while (e && !isClosest && !e.classList.contains("vditor-reset")) {
        if (e.getAttribute(attr) === value) {
            isClosest = true;
        }
        else {
            e = e.parentElement;
        }
    }
    return isClosest && e;
};
var hasClosestBlock = function (element) {
    if (!element) {
        return false;
    }
    if (element.nodeType === 3) {
        element = element.parentElement;
    }
    var e = element;
    var isClosest = false;
    var blockElement = hasClosestByAttribute(element, "data-block", "0");
    if (blockElement) {
        return blockElement;
    }
    while (e && !isClosest && !e.classList.contains("vditor-reset")) {
        if (e.tagName === "H1" ||
            e.tagName === "H2" ||
            e.tagName === "H3" ||
            e.tagName === "H4" ||
            e.tagName === "H5" ||
            e.tagName === "H6" ||
            e.tagName === "P" ||
            e.tagName === "BLOCKQUOTE" ||
            e.tagName === "OL" ||
            e.tagName === "UL") {
            isClosest = true;
        }
        else {
            e = e.parentElement;
        }
    }
    return isClosest && e;
};
var hasClosestByMatchTag = function (element, nodeName) {
    if (!element) {
        return false;
    }
    if (element.nodeType === 3) {
        element = element.parentElement;
    }
    var e = element;
    var isClosest = false;
    while (e && !isClosest && !e.classList.contains("vditor-reset")) {
        if (e.nodeName === nodeName) {
            isClosest = true;
        }
        else {
            e = e.parentElement;
        }
    }
    return isClosest && e;
};
var hasClosestByClassName = function (element, className) {
    if (!element) {
        return false;
    }
    if (element.nodeType === 3) {
        element = element.parentElement;
    }
    var e = element;
    var isClosest = false;
    while (e && !isClosest && !e.classList.contains("vditor-reset")) {
        if (e.classList.contains(className)) {
            isClosest = true;
        }
        else {
            e = e.parentElement;
        }
    }
    return isClosest && e;
};
var getLastNode = function (node) {
    while (node && node.lastChild) {
        node = node.lastChild;
    }
    return node;
};


/***/ },

/***/ 63
(__unused_webpack_module, __webpack_exports__, __webpack_require__) {


// EXPORTS
__webpack_require__.d(__webpack_exports__, {
  o: () => (/* binding */ codeRender)
});

// EXTERNAL MODULE: ./src/ts/util/code160to32.ts
var code160to32 = __webpack_require__(994);
;// ./src/ts/markdown/codeCopy.ts
// Bind outside HTML attributes so strict CSP and restored undo snapshots work alike.
var bindCodeCopy = function (menu, textarea, button) {
    var _a;
    var doc = menu.ownerDocument;
    var label = ((_a = window.VditorI18n) === null || _a === void 0 ? void 0 : _a.copy) || "复制";
    button.setAttribute("aria-label", label);
    button.setAttribute("role", "button");
    button.tabIndex = 0;
    button.addEventListener("mouseover", function () { return button.setAttribute("aria-label", label); });
    var copy = function (event) {
        var _a;
        event.preventDefault();
        event.stopPropagation();
        var active = doc.activeElement;
        var input = active instanceof HTMLInputElement || active instanceof HTMLTextAreaElement ? active : undefined;
        var inputSelection = input && input.selectionStart !== null ?
            { start: input.selectionStart, end: input.selectionEnd, direction: input.selectionDirection } : undefined;
        var selection = doc.getSelection();
        var ranges = Array.from({ length: (selection === null || selection === void 0 ? void 0 : selection.rangeCount) || 0 }, function (_, index) { return selection.getRangeAt(index).cloneRange(); });
        button.setAttribute("aria-label", label);
        var copied = false;
        try {
            textarea.select();
            copied = doc.execCommand("copy");
        }
        finally {
            textarea.blur();
            if (active instanceof HTMLElement && active.isConnected)
                active.focus({ preventScroll: true });
            selection === null || selection === void 0 ? void 0 : selection.removeAllRanges();
            ranges.forEach(function (range) { return selection === null || selection === void 0 ? void 0 : selection.addRange(range); });
            if (inputSelection && input.isConnected) {
                input.setSelectionRange(inputSelection.start, inputSelection.end, inputSelection.direction);
            }
        }
        if (copied) {
            button.setAttribute("aria-label", ((_a = window.VditorI18n) === null || _a === void 0 ? void 0 : _a.copied) || "已复制");
            button.dispatchEvent(new CustomEvent("vditor-copy-success", { bubbles: true, detail: { label: label } }));
        }
    };
    button.addEventListener("click", copy);
    button.addEventListener("keydown", function (event) {
        if (event.key === "Enter" || event.key === " ")
            copy(event);
    });
};

// EXTERNAL MODULE: ./src/ts/constants.ts
var constants = __webpack_require__(802);
;// ./src/ts/markdown/codeRender.ts



var initializedMenus = new WeakSet();
var codeRender = function (element, option) {
    Array.from(element.querySelectorAll("pre > code")).filter(function (e, index) {
        if (e.parentElement.classList.contains("vditor-wysiwyg__pre") ||
            e.parentElement.classList.contains("vditor-ir__marker--pre")) {
            return false;
        }
        if (e.classList.contains("language-mermaid") || e.classList.contains("language-flowchart") ||
            e.classList.contains("language-echarts") || e.classList.contains("language-mindmap") ||
            e.classList.contains("language-plantuml") || e.classList.contains("language-markmap") ||
            e.classList.contains("language-abc") || e.classList.contains("language-graphviz") ||
            e.classList.contains("language-math") || e.classList.contains("language-smiles")) {
            return false;
        }
        // 避免预览区在渲染后由于代码块过多产生性能问题 https://github.com/b3log/vditor/issues/67
        if (element.classList.contains("vditor-preview") && index > 5) {
            return false;
        }
        return true;
    }).forEach(function (e) {
        var _a;
        var previous = e.previousElementSibling;
        if (previous === null || previous === void 0 ? void 0 : previous.classList.contains("vditor-copy")) {
            if (initializedMenus.has(previous))
                return;
            previous.remove();
        }
        var codeText = e.innerText;
        if (e.classList.contains("highlight-chroma")) {
            var codeElement = e.cloneNode(true);
            codeElement.querySelectorAll(".highlight-ln").forEach(function (item) {
                item.remove();
            });
            codeText = codeElement.innerText;
        }
        else if (codeText.endsWith("\n")) {
            codeText = codeText.substr(0, codeText.length - 1);
        }
        var iconHTML = '<svg><use xlink:href="#vditor-icon-copy"></use></svg>';
        if (!document.getElementById("vditorIconScript")) {
            iconHTML = '<svg viewBox="0 0 32 32"><path d="M22.545-0h-17.455c-1.6 0-2.909 1.309-2.909 2.909v20.364h2.909v-20.364h17.455v-2.909zM26.909 5.818h-16c-1.6 0-2.909 1.309-2.909 2.909v20.364c0 1.6 1.309 2.909 2.909 2.909h16c1.6 0 2.909-1.309 2.909-2.909v-20.364c0-1.6-1.309-2.909-2.909-2.909zM26.909 29.091h-16v-20.364h16v20.364z"></path></svg>';
        }
        var divElement = document.createElement("div");
        divElement.className = "vditor-copy";
        var button = document.createElement("span");
        button.className = "vditor-tooltipped vditor-tooltipped__w";
        button.innerHTML = iconHTML;
        divElement.appendChild(button);
        var textarea = document.createElement("textarea");
        textarea.value = (0,code160to32/* code160to32 */.p)(codeText);
        divElement.insertAdjacentElement("afterbegin", textarea);
        bindCodeCopy(divElement, textarea, button);
        initializedMenus.add(divElement);
        if (option && option.renderMenu) {
            option.renderMenu(e, divElement);
        }
        e.before(divElement);
        e.style.maxHeight = (window.outerHeight - 40) + "px";
        // https://github.com/Vanessa219/vditor/issues/1356
        if (!(((_a = e.nextElementSibling) === null || _a === void 0 ? void 0 : _a.textContent) === constants/* Constants */.Y.ZWSP &&
            e.nextElementSibling.style.position === "absolute")) {
            e.insertAdjacentHTML("afterend", "<span style=\"position: absolute\">".concat(constants/* Constants */.Y.ZWSP, "</span>"));
        }
    });
};


/***/ },

/***/ 71
(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   q: () => (/* binding */ normalizeCodeHTML)
/* harmony export */ });
/* unused harmony export normalizeCodeDOM */
var normalizeCodeDOM = function (element) {
    element.querySelectorAll("code[data-code-highlight]").forEach(function (code) {
        code.removeAttribute("data-code-highlight");
        code.classList.remove("hljs");
        code.querySelectorAll("span").forEach(function (span) {
            if (!span.classList.contains("vditor-wbr")) {
                span.replaceWith.apply(span, Array.from(span.childNodes));
            }
        });
    });
};
var normalizeCodeHTML = function (html) {
    if (!html.includes("data-code-highlight")) {
        return html;
    }
    var element = document.createElement("div");
    element.innerHTML = html;
    normalizeCodeDOM(element);
    return element.innerHTML;
};


/***/ },

/***/ 84
(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   Z: () => (/* binding */ addScript)
/* harmony export */ });
var loadingScripts = new Map();
var addScript = function (path, id) {
    if (document.getElementById(id)) {
        return Promise.resolve(true);
    }
    if (loadingScripts.has(id)) {
        return loadingScripts.get(id);
    }
    var promise = new Promise(function (resolve, reject) {
        var scriptElement = document.createElement("script");
        scriptElement.src = path;
        scriptElement.async = true;
        scriptElement.onerror = function (event) {
            scriptElement.remove();
            loadingScripts.delete(id);
            reject(event);
        };
        scriptElement.onload = function () {
            loadingScripts.delete(id);
            if (document.getElementById(id)) {
                // 循环调用需清除 DOM 中的 script 标签
                scriptElement.remove();
                resolve(true);
                return false;
            }
            scriptElement.id = id;
            resolve(true);
        };
        document.head.appendChild(scriptElement);
    });
    loadingScripts.set(id, promise);
    return promise;
};


/***/ },

/***/ 140
(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   T: () => (/* binding */ renderImageCaptionHTML)
/* harmony export */ });
/* unused harmony export renderImageCaptions */
var getContentNodes = function (element, ignoreIRMarkers) {
    if (ignoreIRMarkers === void 0) { ignoreIRMarkers = false; }
    return Array.from(element.childNodes).filter(function (node) {
        if (node.nodeType === Node.COMMENT_NODE) {
            return false;
        }
        if (node.nodeType === Node.TEXT_NODE) {
            return node.textContent.replace(/\u200b/g, "").trim() !== "";
        }
        if (!(node instanceof HTMLElement)) {
            return true;
        }
        if (node.tagName === "WBR") {
            return false;
        }
        return !ignoreIRMarkers || !node.classList.contains("vditor-ir__marker");
    });
};
var getWYSIWYGImage = function (paragraph) {
    var nodes = getContentNodes(paragraph);
    if (nodes.length !== 1 || !(nodes[0] instanceof HTMLElement)) {
        return undefined;
    }
    var container = nodes[0];
    if (container instanceof HTMLImageElement) {
        return {
            container: container,
            image: container,
        };
    }
    if (container instanceof HTMLAnchorElement) {
        var linkNodes = getContentNodes(container);
        if (linkNodes.length === 1 && linkNodes[0] instanceof HTMLImageElement) {
            return {
                container: container,
                image: linkNodes[0],
            };
        }
    }
    return undefined;
};
var getIRImage = function (paragraph) {
    var nodes = getContentNodes(paragraph);
    if (nodes.length !== 1 || !(nodes[0] instanceof HTMLElement)) {
        return undefined;
    }
    var imageNode = nodes[0];
    if (imageNode.getAttribute("data-type") === "a") {
        var linkNodes = getContentNodes(imageNode, true);
        if (linkNodes.length !== 1 || !(linkNodes[0] instanceof HTMLElement)) {
            return undefined;
        }
        imageNode = linkNodes[0];
    }
    if (imageNode.getAttribute("data-type") !== "img") {
        return undefined;
    }
    var image = imageNode.querySelector(":scope > img");
    var titleMarker = imageNode.querySelector(":scope > .vditor-ir__marker--title");
    if (!(image instanceof HTMLImageElement) || !titleMarker) {
        return undefined;
    }
    var markerText = titleMarker.textContent.trim();
    var closeMarker = markerText[0] === "(" ? ")" : markerText[0];
    if (markerText.length < 2 || !["\"", "'", "("].includes(markerText[0]) ||
        markerText[markerText.length - 1] !== closeMarker) {
        return undefined;
    }
    return {
        caption: markerText.slice(1, -1).trim(),
        container: imageNode,
        image: image,
    };
};
var unwrapWYSIWYGCaptions = function (element) {
    element.querySelectorAll("span.vditor-image[data-image-caption]").forEach(function (wrapper) {
        while (wrapper.firstChild) {
            wrapper.parentNode.insertBefore(wrapper.firstChild, wrapper);
        }
        wrapper.remove();
    });
};
var resetIRCaptions = function (element) {
    element.querySelectorAll(".vditor-image[data-image-caption]").forEach(function (imageNode) {
        imageNode.classList.remove("vditor-image");
        imageNode.removeAttribute("data-image-caption");
    });
};
var renderPreviewCaptions = function (element) {
    element.querySelectorAll("p").forEach(function (paragraph) {
        var _a;
        var imageData = getWYSIWYGImage(paragraph);
        var caption = (_a = imageData === null || imageData === void 0 ? void 0 : imageData.image.getAttribute("title")) === null || _a === void 0 ? void 0 : _a.trim();
        if (!imageData || !caption) {
            return;
        }
        var figure = document.createElement("figure");
        Array.from(paragraph.attributes).forEach(function (attribute) {
            figure.setAttribute(attribute.name, attribute.value);
        });
        figure.classList.add("vditor-image");
        var figcaption = document.createElement("figcaption");
        figcaption.textContent = caption;
        figure.append(imageData.container, figcaption);
        paragraph.replaceWith(figure);
    });
};
var renderWYSIWYGCaptions = function (element) {
    element.querySelectorAll("p").forEach(function (paragraph) {
        var _a;
        var imageData = getWYSIWYGImage(paragraph);
        var caption = (_a = imageData === null || imageData === void 0 ? void 0 : imageData.image.getAttribute("title")) === null || _a === void 0 ? void 0 : _a.trim();
        if (!imageData || !caption) {
            return;
        }
        var wrapper = document.createElement("span");
        wrapper.className = "vditor-image";
        wrapper.setAttribute("data-image-caption", caption);
        imageData.container.replaceWith(wrapper);
        wrapper.append(imageData.container);
    });
};
var renderIRCaptions = function (element) {
    element.querySelectorAll("p").forEach(function (paragraph) {
        var imageData = getIRImage(paragraph);
        if (!(imageData === null || imageData === void 0 ? void 0 : imageData.caption)) {
            return;
        }
        imageData.container.classList.add("vditor-image");
        imageData.container.setAttribute("data-image-caption", imageData.caption);
    });
};
var renderImageCaptions = function (element, mode, enable) {
    if (mode === "wysiwyg") {
        unwrapWYSIWYGCaptions(element);
    }
    else if (mode === "ir") {
        resetIRCaptions(element);
    }
    if (!enable) {
        return;
    }
    if (mode === "preview") {
        renderPreviewCaptions(element);
    }
    else if (mode === "wysiwyg") {
        renderWYSIWYGCaptions(element);
    }
    else {
        renderIRCaptions(element);
    }
};
var renderImageCaptionHTML = function (html, enable) {
    if (!enable) {
        return html;
    }
    var container = document.createElement("div");
    container.innerHTML = html;
    renderImageCaptions(container, "preview", true);
    return container.innerHTML;
};


/***/ },

/***/ 210
(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   Ee: () => (/* binding */ genUUID),
/* harmony export */   TK: () => (/* binding */ getSearch),
/* harmony export */   kY: () => (/* binding */ looseJsonParse)
/* harmony export */ });
var genUUID = function () { return ([1e7].toString() + -1e3 + -4e3 + -8e3 + -1e11).replace(/[018]/g, function (c) {
    return (parseInt(c, 10) ^ (window.crypto.getRandomValues(new Uint32Array(1))[0] & (15 >> (parseInt(c, 10) / 4)))).toString(16);
}); };
var getSearch = function (key, link) {
    if (link === void 0) { link = window.location.search; }
    var params = link.substring(link.indexOf("?"));
    var hashIndex = params.indexOf("#");
    // REF https://developer.mozilla.org/zh-CN/docs/Web/API/URLSearchParams
    var urlSearchParams = new URLSearchParams(params.substring(0, hashIndex >= 0 ? hashIndex : undefined));
    return urlSearchParams.get(key);
};
var looseJsonParse = function (text) {
    return Function("\"use strict\";return (".concat(text, ")"))();
};


/***/ },

/***/ 225
(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   D: () => (/* binding */ flowchartRender)
/* harmony export */ });
/* harmony import */ var _constants__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(802);
/* harmony import */ var _util_addScript__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(84);
/* harmony import */ var _adapterRender__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(586);



var flowchartRender = function (element, cdn) {
    if (cdn === void 0) { cdn = _constants__WEBPACK_IMPORTED_MODULE_0__/* .Constants */ .Y.CDN; }
    var flowchartElements = _adapterRender__WEBPACK_IMPORTED_MODULE_2__.flowchartRenderAdapter.getElements(element);
    if (flowchartElements.length === 0) {
        return;
    }
    (0,_util_addScript__WEBPACK_IMPORTED_MODULE_1__/* .addScript */ .Z)("".concat(cdn, "/dist/js/flowchart.js/flowchart.min.js"), "vditorFlowchartScript").then(function () {
        flowchartElements.forEach(function (item) {
            if (item.getAttribute("data-processed") === "true") {
                return;
            }
            var flowchartObj = flowchart.parse(_adapterRender__WEBPACK_IMPORTED_MODULE_2__.flowchartRenderAdapter.getCode(item));
            item.innerHTML = "";
            flowchartObj.drawSVG(item);
            item.setAttribute("data-processed", "true");
        });
    });
};


/***/ },

/***/ 291
(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   T: () => (/* binding */ mathRender)
/* harmony export */ });
/* harmony import */ var _constants__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(802);
/* harmony import */ var _util_addScript__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(84);
/* harmony import */ var _util_addStyle__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(546);
/* harmony import */ var _util_code160to32__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(994);
/* harmony import */ var _adapterRender__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(586);





var mathRender = function (element, options) {
    if (element === void 0) { element = document; }
    var mathElements = _adapterRender__WEBPACK_IMPORTED_MODULE_4__.mathRenderAdapter.getElements(element);
    if (mathElements.length === 0) {
        return;
    }
    var defaultOptions = {
        cdn: _constants__WEBPACK_IMPORTED_MODULE_0__/* .Constants */ .Y.CDN,
        math: {
            engine: "KaTeX",
            inlineDigit: false,
            macros: {},
        },
    };
    if (options && options.math) {
        options.math =
            Object.assign({}, defaultOptions.math, options.math);
    }
    options = Object.assign({}, defaultOptions, options);
    if (options.math.engine === "KaTeX") {
        (0,_util_addStyle__WEBPACK_IMPORTED_MODULE_2__/* .addStyle */ .T)("".concat(options.cdn, "/dist/js/katex/katex.min.css?v=0.16.9"), "vditorKatexStyle");
        (0,_util_addScript__WEBPACK_IMPORTED_MODULE_1__/* .addScript */ .Z)("".concat(options.cdn, "/dist/js/katex/katex.min.js?v=0.16.9"), "vditorKatexScript").then(function () {
            (0,_util_addScript__WEBPACK_IMPORTED_MODULE_1__/* .addScript */ .Z)("".concat(options.cdn, "/dist/js/katex/mhchem.min.js?v=0.16.9"), "vditorKatexChemScript").then(function () {
                mathElements.forEach(function (mathElement) {
                    if (mathElement.parentElement.classList.contains("vditor-wysiwyg__pre") ||
                        mathElement.parentElement.classList.contains("vditor-ir__marker--pre")) {
                        return;
                    }
                    if (mathElement.getAttribute("data-math")) {
                        return;
                    }
                    var math = (0,_util_code160to32__WEBPACK_IMPORTED_MODULE_3__/* .code160to32 */ .p)(_adapterRender__WEBPACK_IMPORTED_MODULE_4__.mathRenderAdapter.getCode(mathElement));
                    mathElement.setAttribute("data-math", math);
                    try {
                        mathElement.innerHTML = katex.renderToString(math, {
                            displayMode: mathElement.tagName === "DIV",
                            output: "html",
                            macros: options.math.macros,
                        });
                    }
                    catch (e) {
                        mathElement.innerHTML = e.message;
                        mathElement.className = "language-math vditor-reset--error";
                    }
                    mathElement.addEventListener("copy", function (event) {
                        event.stopPropagation();
                        event.preventDefault();
                        var vditorMathElement = event.currentTarget.closest(".language-math");
                        event.clipboardData.setData("text/html", vditorMathElement.innerHTML);
                        event.clipboardData.setData("text/plain", vditorMathElement.getAttribute("data-math"));
                    });
                });
            });
        });
    }
    else if (options.math.engine === "MathJax") {
        if (!window.MathJax) {
            window.MathJax = {
                loader: {
                    paths: { mathjax: "".concat(options.cdn, "/dist/js/mathjax") },
                },
                startup: {
                    typeset: false,
                },
                tex: {
                    macros: options.math.macros,
                },
            };
            // https://github.com/Vanessa219/vditor/issues/1453
            Object.assign(window.MathJax, options.math.mathJaxOptions);
        }
        var renderMath_1 = function (mathElement) {
            var math = (0,_util_code160to32__WEBPACK_IMPORTED_MODULE_3__/* .code160to32 */ .p)(mathElement.textContent).trim();
            var mathOptions = window.MathJax.getMetricsFor(mathElement);
            mathOptions.display = mathElement.tagName === "DIV";
            return window.MathJax.tex2svgPromise(math, mathOptions).then(function (node) {
                mathElement.innerHTML = "";
                mathElement.setAttribute("data-math", math);
                mathElement.append(node);
                window.MathJax.startup.document.clear();
                window.MathJax.startup.document.updateDocument();
                var errorTextElement = node.querySelector('[data-mml-node="merror"]');
                if (errorTextElement && errorTextElement.textContent.trim() !== "") {
                    mathElement.innerHTML = errorTextElement.textContent.trim();
                    mathElement.className = "vditor-reset--error";
                }
            });
        };
        (0,_util_addScript__WEBPACK_IMPORTED_MODULE_1__/* .addScript */ .Z)("".concat(options.cdn, "/dist/js/mathjax/tex-svg-full.js"), "protyleMathJaxScript")
            .then(function () { return window.MathJax.startup.promise; }).then(function () {
            var rendering = Promise.resolve();
            var _loop_1 = function (i) {
                var mathElement = mathElements[i];
                if (!mathElement.parentElement.classList.contains("vditor-wysiwyg__pre") &&
                    !mathElement.parentElement.classList.contains("vditor-ir__marker--pre") &&
                    !mathElement.getAttribute("data-math") && (0,_util_code160to32__WEBPACK_IMPORTED_MODULE_3__/* .code160to32 */ .p)(mathElement.textContent).trim()) {
                    rendering = rendering.then(function () { return renderMath_1(mathElement); });
                }
            };
            for (var i = 0; i < mathElements.length; i++) {
                _loop_1(i);
            }
            return rendering;
        });
    }
};


/***/ },

/***/ 305
(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   $: () => (/* binding */ abcRender)
/* harmony export */ });
/* harmony import */ var _constants__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(802);
/* harmony import */ var _util_addScript__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(84);
/* harmony import */ var _adapterRender__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(586);



var abcRender = function (element, cdn) {
    if (element === void 0) { element = document; }
    if (cdn === void 0) { cdn = _constants__WEBPACK_IMPORTED_MODULE_0__/* .Constants */ .Y.CDN; }
    var abcElements = _adapterRender__WEBPACK_IMPORTED_MODULE_2__.abcRenderAdapter.getElements(element);
    if (abcElements.length > 0) {
        (0,_util_addScript__WEBPACK_IMPORTED_MODULE_1__/* .addScript */ .Z)("".concat(cdn, "/dist/js/abcjs/abcjs_basic.min.js"), "vditorAbcjsScript").then(function () {
            abcElements.forEach(function (item) {
                if (item.parentElement.classList.contains("vditor-wysiwyg__pre") ||
                    item.parentElement.classList.contains("vditor-ir__marker--pre")) {
                    return;
                }
                if (item.getAttribute("data-processed") === "true") {
                    return;
                }
                ABCJS.renderAbc(item, _adapterRender__WEBPACK_IMPORTED_MODULE_2__.abcRenderAdapter.getCode(item).trim());
                item.style.overflowX = "auto";
                item.setAttribute("data-processed", "true");
            });
        });
    }
};


/***/ },

/***/ 320
(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   M: () => (/* binding */ plantumlRender)
/* harmony export */ });
/* harmony import */ var _constants__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(802);
/* harmony import */ var _util_addScript__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(84);
/* harmony import */ var _adapterRender__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(586);



var plantumlRender = function (element, cdn, plantuml) {
    if (element === void 0) { element = document; }
    if (cdn === void 0) { cdn = _constants__WEBPACK_IMPORTED_MODULE_0__/* .Constants */ .Y.CDN; }
    var plantumlElements = _adapterRender__WEBPACK_IMPORTED_MODULE_2__.plantumlRenderAdapter.getElements(element);
    if (plantumlElements.length === 0) {
        return;
    }
    var renderer = plantuml === null || plantuml === void 0 ? void 0 : plantuml.renderer;
    var server = (plantuml === null || plantuml === void 0 ? void 0 : plantuml.server) || _constants__WEBPACK_IMPORTED_MODULE_0__/* .Constants */ .Y.PLANTUML_OPTIONS.server;
    var renderElements = function () {
        plantumlElements.forEach(function (e) {
            if (e.parentElement.classList.contains("vditor-wysiwyg__pre") ||
                e.parentElement.classList.contains("vditor-ir__marker--pre")) {
                return;
            }
            var text = _adapterRender__WEBPACK_IMPORTED_MODULE_2__.plantumlRenderAdapter.getCode(e).trim();
            if (!text) {
                return;
            }
            if (renderer) {
                Promise.resolve().then(function () { return renderer(text, e); }).catch(function (error) {
                    e.className = "vditor-reset--error";
                    e.textContent = "plantuml render error: ".concat(error);
                });
                return;
            }
            try {
                var image = document.createElement("object");
                image.type = "image/svg+xml";
                image.data = "".concat(server, "~1").concat(plantumlEncoder.encode(text));
                e.replaceChildren(image);
            }
            catch (error) {
                e.className = "vditor-reset--error";
                e.textContent = "plantuml render error: ".concat(error);
            }
        });
    };
    if (renderer) {
        // 自定义渲染无需加载 plantuml-encoder
        renderElements();
        return;
    }
    (0,_util_addScript__WEBPACK_IMPORTED_MODULE_1__/* .addScript */ .Z)("".concat(cdn, "/dist/js/plantuml/plantuml-encoder.min.js"), "vditorPlantumlScript").then(renderElements);
};


/***/ },

/***/ 345
(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   v: () => (/* binding */ chartRender)
/* harmony export */ });
/* harmony import */ var _constants__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(802);
/* harmony import */ var _util_addScript__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(84);
/* harmony import */ var _adapterRender__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(586);
/* harmony import */ var _util_function__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(210);
var __awaiter = (undefined && undefined.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
var __generator = (undefined && undefined.__generator) || function (thisArg, body) {
    var _ = { label: 0, sent: function() { if (t[0] & 1) throw t[1]; return t[1]; }, trys: [], ops: [] }, f, y, t, g;
    return g = { next: verb(0), "throw": verb(1), "return": verb(2) }, typeof Symbol === "function" && (g[Symbol.iterator] = function() { return this; }), g;
    function verb(n) { return function (v) { return step([n, v]); }; }
    function step(op) {
        if (f) throw new TypeError("Generator is already executing.");
        while (g && (g = 0, op[0] && (_ = 0)), _) try {
            if (f = 1, y && (t = op[0] & 2 ? y["return"] : op[0] ? y["throw"] || ((t = y["return"]) && t.call(y), 0) : y.next) && !(t = t.call(y, op[1])).done) return t;
            if (y = 0, t) op = [op[0] & 2, t.value];
            switch (op[0]) {
                case 0: case 1: t = op; break;
                case 4: _.label++; return { value: op[1], done: false };
                case 5: _.label++; y = op[1]; op = [0]; continue;
                case 7: op = _.ops.pop(); _.trys.pop(); continue;
                default:
                    if (!(t = _.trys, t = t.length > 0 && t[t.length - 1]) && (op[0] === 6 || op[0] === 2)) { _ = 0; continue; }
                    if (op[0] === 3 && (!t || (op[1] > t[0] && op[1] < t[3]))) { _.label = op[1]; break; }
                    if (op[0] === 6 && _.label < t[1]) { _.label = t[1]; t = op; break; }
                    if (t && _.label < t[2]) { _.label = t[2]; _.ops.push(op); break; }
                    if (t[2]) _.ops.pop();
                    _.trys.pop(); continue;
            }
            op = body.call(thisArg, _);
        } catch (e) { op = [6, e]; y = 0; } finally { f = t = 0; }
        if (op[0] & 5) throw op[1]; return { value: op[0] ? op[1] : void 0, done: true };
    }
};




var charts = new WeakMap();
var chartRender = function (element, cdn, theme) {
    if (element === void 0) { element = document; }
    if (cdn === void 0) { cdn = _constants__WEBPACK_IMPORTED_MODULE_0__/* .Constants */ .Y.CDN; }
    var echartsElements = _adapterRender__WEBPACK_IMPORTED_MODULE_2__.chartRenderAdapter.getElements(element);
    if (echartsElements.length > 0) {
        (0,_util_addScript__WEBPACK_IMPORTED_MODULE_1__/* .addScript */ .Z)("".concat(cdn, "/dist/js/echarts/echarts.min.js?v=5.5.1"), "vditorEchartsScript").then(function () {
            echartsElements.forEach(function (e) { return __awaiter(void 0, void 0, void 0, function () {
                var text, option, previous, instance_1, state_1, error_1;
                var _a;
                return __generator(this, function (_b) {
                    switch (_b.label) {
                        case 0:
                            if (e.parentElement.classList.contains("vditor-wysiwyg__pre") ||
                                e.parentElement.classList.contains("vditor-ir__marker--pre")) {
                                return [2 /*return*/];
                            }
                            text = _adapterRender__WEBPACK_IMPORTED_MODULE_2__.chartRenderAdapter.getCode(e).trim();
                            if (!text) {
                                return [2 /*return*/];
                            }
                            _b.label = 1;
                        case 1:
                            _b.trys.push([1, 3, , 4]);
                            if (e.getAttribute("data-processed") === "true") {
                                return [2 /*return*/];
                            }
                            return [4 /*yield*/, (0,_util_function__WEBPACK_IMPORTED_MODULE_3__/* .looseJsonParse */ .kY)(text)];
                        case 2:
                            option = _b.sent();
                            previous = charts.get(e);
                            (_a = previous === null || previous === void 0 ? void 0 : previous.observer) === null || _a === void 0 ? void 0 : _a.disconnect();
                            previous === null || previous === void 0 ? void 0 : previous.instance.dispose();
                            instance_1 = echarts.init(e, theme === "dark" ? "dark" : undefined);
                            instance_1.setOption(option);
                            state_1 = { instance: instance_1 };
                            if (typeof ResizeObserver !== "undefined") {
                                state_1.observer = new ResizeObserver(function () {
                                    if (!e.isConnected) {
                                        state_1.observer.disconnect();
                                        instance_1.dispose();
                                        charts.delete(e);
                                        e.removeAttribute("data-processed");
                                        return;
                                    }
                                    if (e.clientWidth > 0 && e.clientHeight > 0) {
                                        instance_1.resize();
                                    }
                                });
                                state_1.observer.observe(e);
                            }
                            charts.set(e, state_1);
                            e.setAttribute("data-processed", "true");
                            return [3 /*break*/, 4];
                        case 3:
                            error_1 = _b.sent();
                            e.className = "vditor-reset--error";
                            e.innerHTML = "echarts render error: <br>".concat(error_1);
                            return [3 /*break*/, 4];
                        case 4: return [2 /*return*/];
                    }
                });
            }); });
        });
    }
};


/***/ },

/***/ 382
(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   jl: () => (/* binding */ setSelectionFocus)
/* harmony export */ });
/* unused harmony exports getEditorRange, getCursorPosition, selectIsEditor, getSelectPosition, setSelectionByPosition, setRangeByWbr, insertHTML */
/* harmony import */ var _constants__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(802);



var getEditorRange = function (vditor) {
    if (vditor.currentMode === "sv") {
        throw new Error("SV mode uses textarea selection");
    }
    var range;
    var element = vditor[vditor.currentMode].element;
    if (getSelection().rangeCount > 0) {
        range = getSelection().getRangeAt(0);
        if (element.isEqualNode(range.startContainer) || element.contains(range.startContainer)) {
            return range;
        }
    }
    var lastRange = vditor.currentMode === "ir" ? vditor.ir.range : vditor.wysiwyg.range;
    if (lastRange) {
        return lastRange;
    }
    element.focus();
    range = element.ownerDocument.createRange();
    range.setStart(element, 0);
    range.collapse(true);
    return range;
};
var getCursorPosition = function (editor) {
    var range = window.getSelection().getRangeAt(0);
    if (!editor.contains(range.startContainer) && !hasClosestByClassName(range.startContainer, "vditor-panel--none")) {
        return {
            left: 0,
            top: 0,
        };
    }
    var parentRect = editor.parentElement.getBoundingClientRect();
    var cursorRect;
    if (range.getClientRects().length === 0) {
        if (range.startContainer.nodeType === 3) {
            // 空行时，会出现没有 br 的情况，需要根据父元素 <p> 获取位置信息
            var parent_1 = range.startContainer.parentElement;
            if (parent_1 && parent_1.getClientRects().length > 0) {
                cursorRect = parent_1.getClientRects()[0];
            }
            else {
                return {
                    left: 0,
                    top: 0,
                };
            }
        }
        else {
            var children = range.startContainer.children;
            if (children[range.startOffset] &&
                children[range.startOffset].getClientRects().length > 0) {
                // markdown 模式回车
                cursorRect = children[range.startOffset].getClientRects()[0];
            }
            else if (range.startContainer.childNodes.length > 0) {
                // in table or code block
                var cloneRange = range.cloneRange();
                range.selectNode(range.startContainer.childNodes[Math.max(0, range.startOffset - 1)]);
                cursorRect = range.getClientRects()[0];
                range.setEnd(cloneRange.endContainer, cloneRange.endOffset);
                range.setStart(cloneRange.startContainer, cloneRange.startOffset);
            }
            else {
                cursorRect = range.startContainer.getClientRects()[0];
            }
            if (!cursorRect) {
                var parentElement = range.startContainer.childNodes[range.startOffset];
                while (!parentElement.getClientRects ||
                    (parentElement.getClientRects && parentElement.getClientRects().length === 0)) {
                    parentElement = parentElement.parentElement;
                }
                cursorRect = parentElement.getClientRects()[0];
            }
        }
    }
    else {
        cursorRect = range.getClientRects()[0];
    }
    return {
        left: cursorRect.left - parentRect.left,
        top: cursorRect.top - parentRect.top,
    };
};
var selectIsEditor = function (editor, range) {
    if (!range) {
        if (getSelection().rangeCount === 0) {
            return false;
        }
        else {
            range = getSelection().getRangeAt(0);
        }
    }
    var container = range.commonAncestorContainer;
    return editor.isEqualNode(container) || editor.contains(container);
};
var setSelectionFocus = function (range) {
    var selection = window.getSelection();
    selection.removeAllRanges();
    selection.addRange(range);
};
var getSelectPosition = function (selectElement, editorElement, range) {
    var position = {
        end: 0,
        start: 0,
    };
    if (!range) {
        if (getSelection().rangeCount === 0) {
            return position;
        }
        range = window.getSelection().getRangeAt(0);
    }
    if (selectIsEditor(editorElement, range)) {
        var preSelectionRange = range.cloneRange();
        if (selectElement.childNodes[0] && selectElement.childNodes[0].childNodes[0]) {
            preSelectionRange.setStart(selectElement.childNodes[0].childNodes[0], 0);
        }
        else {
            preSelectionRange.selectNodeContents(selectElement);
        }
        preSelectionRange.setEnd(range.startContainer, range.startOffset);
        position.start = preSelectionRange.toString().length;
        position.end = position.start + range.toString().length;
    }
    return position;
};
var setSelectionByPosition = function (start, end, editor) {
    var charIndex = 0;
    var line = 0;
    var pNode = editor.childNodes[line];
    var foundStart = false;
    var stop = false;
    start = Math.max(0, start);
    end = Math.max(0, end);
    var range = editor.ownerDocument.createRange();
    range.setStart(pNode || editor, 0);
    range.collapse(true);
    while (!stop && pNode) {
        var nextCharIndex = charIndex + pNode.textContent.length;
        if (!foundStart && start >= charIndex && start <= nextCharIndex) {
            if (start === 0) {
                range.setStart(pNode, 0);
            }
            else {
                if (pNode.childNodes[0].nodeType === 3) {
                    range.setStart(pNode.childNodes[0], start - charIndex);
                }
                else if (pNode.nextSibling) {
                    range.setStartBefore(pNode.nextSibling);
                }
                else {
                    range.setStartAfter(pNode);
                }
            }
            foundStart = true;
            if (start === end) {
                stop = true;
                break;
            }
        }
        if (foundStart && end >= charIndex && end <= nextCharIndex) {
            if (end === 0) {
                range.setEnd(pNode, 0);
            }
            else {
                if (pNode.childNodes[0].nodeType === 3) {
                    range.setEnd(pNode.childNodes[0], end - charIndex);
                }
                else if (pNode.nextSibling) {
                    range.setEndBefore(pNode.nextSibling);
                }
                else {
                    range.setEndAfter(pNode);
                }
            }
            stop = true;
        }
        charIndex = nextCharIndex;
        pNode = editor.childNodes[++line];
    }
    if (!stop && editor.childNodes[line - 1]) {
        range.setStartBefore(editor.childNodes[line - 1]);
    }
    setSelectionFocus(range);
    return range;
};
var setRangeByWbr = function (element, range) {
    var wbrElement = element.querySelector("wbr");
    if (!wbrElement) {
        return;
    }
    if (!wbrElement.previousElementSibling) {
        if (wbrElement.previousSibling) {
            // text<wbr>
            range.setStart(wbrElement.previousSibling, wbrElement.previousSibling.textContent.length);
        }
        else if (wbrElement.nextSibling) {
            if (wbrElement.nextSibling.nodeType === 3) {
                // <wbr>text
                range.setStart(wbrElement.nextSibling, 0);
            }
            else {
                // <wbr><br> https://github.com/Vanessa219/vditor/issues/400
                range.setStartBefore(wbrElement.nextSibling);
            }
        }
        else {
            // 内容为空
            range.setStart(wbrElement.parentElement, 0);
        }
    }
    else {
        if (wbrElement.previousElementSibling.isSameNode(wbrElement.previousSibling)) {
            if (wbrElement.previousElementSibling.lastChild) {
                // <em>text</em><wbr>
                range.setStartBefore(wbrElement);
                range.collapse(true);
                setSelectionFocus(range);
                // fix Chrome set range bug: **c**
                if (isChrome() && (wbrElement.previousElementSibling.tagName === "EM" ||
                    wbrElement.previousElementSibling.tagName === "STRONG" ||
                    wbrElement.previousElementSibling.tagName === "S")) {
                    range.insertNode(document.createTextNode(Constants.ZWSP));
                    range.collapse(false);
                }
                wbrElement.remove();
                return;
            }
            else {
                // <br><wbr>
                range.setStartAfter(wbrElement.previousElementSibling);
            }
        }
        else {
            // <em>text</em>text<wbr>
            range.setStart(wbrElement.previousSibling, wbrElement.previousSibling.textContent.length);
        }
    }
    range.collapse(true);
    wbrElement.remove();
    setSelectionFocus(range);
};
var insertHTML = function (html, vditor) {
    // 使用 lute 方法会添加 p 元素，只有一个 p 元素的时候进行删除
    var tempElement = document.createElement("div");
    tempElement.innerHTML = html;
    var tempBlockElement = tempElement.querySelectorAll("p");
    if (tempBlockElement.length === 1 && !tempBlockElement[0].previousSibling && !tempBlockElement[0].nextSibling &&
        vditor[vditor.currentMode].element.children.length > 0 && tempElement.firstElementChild.tagName === "P") {
        html = tempBlockElement[0].innerHTML.trim();
    }
    var pasteElement = document.createElement("div");
    pasteElement.innerHTML = html;
    var range = getEditorRange(vditor);
    if (range.toString() !== "") {
        if (vditor.currentMode === "ir") {
            vditor.ir.preventInput = true;
        }
        else if (vditor.currentMode === "wysiwyg") {
            vditor.wysiwyg.preventInput = true;
        }
        document.execCommand("delete", false, "");
    }
    if (pasteElement.firstElementChild &&
        pasteElement.firstElementChild.getAttribute("data-block") === "0") {
        // 粘贴内容为块元素时，应在下一段落中插入
        pasteElement.lastElementChild.insertAdjacentHTML("beforeend", "<wbr>");
        var blockElement = hasClosestBlock(range.startContainer);
        if (!blockElement) {
            vditor[vditor.currentMode].element.insertAdjacentHTML("beforeend", pasteElement.innerHTML);
        }
        else {
            var liElement = hasClosestByMatchTag(range.startContainer, "LI");
            if (liElement && pasteElement.childElementCount === 1 && (pasteElement.firstElementChild.tagName === "UL" ||
                pasteElement.firstElementChild.tagName === "OL")) {
                var before = range.cloneRange();
                before.selectNodeContents(liElement);
                before.setEnd(range.startContainer, range.startOffset);
                var prefix = document.createElement("div");
                prefix.appendChild(before.cloneContents());
                prefix.querySelectorAll(".vditor-ir__marker, input").forEach(function (item) { return item.remove(); });
                var atStart = prefix.textContent.replace(/\u200b/g, "").trim() === "" &&
                    !prefix.querySelector("img, video, audio, iframe, ul, ol, table, pre");
                liElement.insertAdjacentHTML(atStart ? "beforebegin" : "afterend", pasteElement.firstElementChild.innerHTML);
            }
            else {
                blockElement.insertAdjacentHTML("afterend", pasteElement.innerHTML);
            }
        }
        setRangeByWbr(vditor[vditor.currentMode].element, range);
    }
    else {
        var pasteTemplate = document.createElement("template");
        pasteTemplate.innerHTML = html;
        range.insertNode(pasteTemplate.content.cloneNode(true));
        range.collapse(false);
        setSelectionFocus(range);
    }
};


/***/ },

/***/ 476
(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   K: () => (/* binding */ markmapRender)
/* harmony export */ });
/* harmony import */ var _constants__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(802);
/* harmony import */ var _util_addScript__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(84);
/* harmony import */ var _adapterRender__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(586);



var enabled = {};
var transform = function (transformer, content) {
    var result = transformer.transform(content);
    var keys = Object.keys(result.features).filter(function (key) { return !enabled[key]; });
    keys.forEach(function (key) {
        enabled[key] = true;
    });
    var _a = transformer.getAssets(keys), styles = _a.styles, scripts = _a.scripts;
    var markmap = window.markmap;
    if (styles)
        markmap.loadCSS(styles);
    if (scripts)
        markmap.loadJS(scripts);
    return result;
};
var init = function (el, code) {
    var _a = window.markmap, Transformer = _a.Transformer, Markmap = _a.Markmap, deriveOptions = _a.deriveOptions, globalCSS = _a.globalCSS;
    var transformer = new Transformer();
    el.innerHTML = '<svg style="width:100%"></svg>';
    var svg = el.firstChild;
    var mm = Markmap.create(svg, null);
    var _b = transform(transformer, code), root = _b.root, frontmatter = _b.frontmatter;
    var markmapOptions = frontmatter === null || frontmatter === void 0 ? void 0 : frontmatter.markmap;
    var frontmatterOptions = deriveOptions(markmapOptions);
    mm.setData(root, frontmatterOptions);
    mm.fit();
};
var markmapRender = function (element, cdn) {
    if (element === void 0) { element = document; }
    if (cdn === void 0) { cdn = _constants__WEBPACK_IMPORTED_MODULE_0__/* .Constants */ .Y.CDN; }
    var markmapElements = _adapterRender__WEBPACK_IMPORTED_MODULE_2__.markmapRenderAdapter.getElements(element);
    if (markmapElements.length === 0) {
        return;
    }
    (0,_util_addScript__WEBPACK_IMPORTED_MODULE_1__/* .addScript */ .Z)("".concat(cdn, "/dist/js/markmap/markmap.min.js"), "vditorMarkerScript").then(function () {
        markmapElements.forEach(function (item) {
            var code = _adapterRender__WEBPACK_IMPORTED_MODULE_2__.markmapRenderAdapter.getCode(item);
            if (item.getAttribute("data-processed") === "true" || code.trim() === "") {
                return;
            }
            var render = document.createElement("div");
            render.className = "language-markmap";
            item.parentNode.appendChild(render);
            init(render, code);
            if (item.parentNode.childNodes[0].nodeName == "CODE") {
                item.parentNode.removeChild(item.parentNode.childNodes[0]);
            }
        });
    });
};


/***/ },

/***/ 483
(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   N: () => (/* binding */ outlineRender)
/* harmony export */ });
/* unused harmony export getOutlineHeadings */
/* harmony import */ var _util_hasClosestByHeadings__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(675);
/* harmony import */ var _mathRender__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(291);


var getOutlineHeadings = function (contentElement, assignIDs) {
    if (assignIDs === void 0) { assignIDs = false; }
    var headings = [];
    Array.from(contentElement.children).forEach(function (item, index) {
        if (!(0,_util_hasClosestByHeadings__WEBPACK_IMPORTED_MODULE_0__/* .hasClosestByHeadings */ .c)(item)) {
            return;
        }
        if (assignIDs) {
            var lastIndex = item.id.lastIndexOf("_");
            item.id = item.id.substring(0, lastIndex === -1 ? undefined : lastIndex) + "_" + index;
        }
        headings.push(item);
    });
    return headings;
};
var outlineRender = function (contentElement, targetElement, vditorOrClick) {
    var vditor = typeof vditorOrClick === "function" ? undefined : vditorOrClick;
    var click = typeof vditorOrClick === "function" ? vditorOrClick : undefined;
    var tocHTML = "";
    var ids = [];
    getOutlineHeadings(contentElement, !!vditor).forEach(function (item) {
        ids.push(item.id);
        tocHTML += item.outerHTML.replace("<wbr>", "");
    });
    if (tocHTML === "") {
        targetElement.innerHTML = "";
        return "";
    }
    var tempElement = document.createElement("div");
    if (vditor) {
        vditor.lute.SetToC(true);
        if (vditor.currentMode === "wysiwyg" && !vditor.preview.element.contains(contentElement)) {
            tempElement.innerHTML = vditor.lute.SpinVditorDOM("<p>[ToC]</p>" + tocHTML);
        }
        else if (vditor.currentMode === "ir" && !vditor.preview.element.contains(contentElement)) {
            tempElement.innerHTML = vditor.lute.SpinVditorIRDOM("<p>[ToC]</p>" + tocHTML);
        }
        else {
            tempElement.innerHTML = vditor.lute.HTML2VditorDOM("<p>[ToC]</p>" + tocHTML);
        }
        vditor.lute.SetToC(vditor.options.preview.markdown.toc);
    }
    else {
        targetElement.classList.add("vditor-outline");
        var lute = Lute.New();
        lute.SetToC(true);
        tempElement.innerHTML = lute.HTML2VditorDOM("<p>[ToC]</p>" + tocHTML);
    }
    var headingsElement = tempElement.firstElementChild.querySelectorAll("li > span[data-target-id]");
    headingsElement.forEach(function (item, index) {
        if (item.nextElementSibling && item.nextElementSibling.tagName === "UL") {
            var iconHTML = "<svg class='vditor-outline__action'><use xlink:href='#vditor-icon-down'></use></svg>";
            if (!document.getElementById("vditorIconScript")) {
                iconHTML = '<svg class="vditor-outline__action" viewBox="0 0 32 32"><path d="M3.76 6.12l12.24 12.213 12.24-12.213 3.76 3.76-16 16-16-16 3.76-3.76z"></path></svg>';
            }
            item.innerHTML = "".concat(iconHTML, "<span>").concat(item.innerHTML, "</span>");
        }
        else {
            item.innerHTML = "<svg></svg><span>".concat(item.innerHTML, "</span>");
        }
        item.setAttribute("data-target-id", ids[index]);
    });
    tocHTML = tempElement.firstElementChild.innerHTML;
    if (headingsElement.length === 0) {
        targetElement.innerHTML = "";
        return tocHTML;
    }
    targetElement.innerHTML = tocHTML;
    if (vditor) {
        (0,_mathRender__WEBPACK_IMPORTED_MODULE_1__/* .mathRender */ .T)(targetElement, {
            cdn: vditor.options.cdn,
            math: vditor.options.preview.math,
        });
    }
    targetElement.firstElementChild.addEventListener("click", function (event) {
        var target = event.target;
        while (target && !target.isEqualNode(targetElement)) {
            if (target.classList.contains("vditor-outline__action")) {
                if (target.classList.contains("vditor-outline__action--close")) {
                    target.classList.remove("vditor-outline__action--close");
                    target.parentElement.nextElementSibling.setAttribute("style", "display:block");
                }
                else {
                    target.classList.add("vditor-outline__action--close");
                    target.parentElement.nextElementSibling.setAttribute("style", "display:none");
                }
                event.preventDefault();
                event.stopPropagation();
                break;
            }
            else if (target.getAttribute("data-target-id")) {
                event.preventDefault();
                event.stopPropagation();
                var idElement = Array.from(contentElement.children).find(function (item) {
                    return item.id === target.getAttribute("data-target-id");
                });
                if (!idElement) {
                    return;
                }
                if (click) {
                    click(idElement, event);
                    return;
                }
                if (vditor) {
                    if (vditor.options.height === "auto") {
                        idElement.scrollIntoView({ block: "start", inline: "nearest" });
                        if (vditor.options.toolbarConfig.pin) {
                            var parent_1 = idElement.parentElement;
                            while (parent_1 && parent_1 !== document.documentElement) {
                                if (/auto|scroll/.test(getComputedStyle(parent_1).overflowY) &&
                                    parent_1.scrollHeight > parent_1.clientHeight) {
                                    break;
                                }
                                parent_1 = parent_1.parentElement;
                            }
                            var offset = -vditor.toolbar.element.offsetHeight;
                            if (parent_1 && parent_1 !== document.documentElement) {
                                parent_1.scrollTop += offset;
                            }
                            else {
                                window.scrollBy(0, offset);
                            }
                        }
                    }
                    else {
                        if (vditor.element.offsetTop < window.scrollY) {
                            window.scrollTo(window.scrollX, vditor.element.offsetTop);
                        }
                        if (vditor.preview.element.contains(contentElement)) {
                            contentElement.parentElement.scrollTop = idElement.offsetTop;
                        }
                        else {
                            contentElement.scrollTop = idElement.offsetTop;
                        }
                    }
                }
                else {
                    window.scrollTo(window.scrollX, idElement.offsetTop);
                }
                break;
            }
            target = target.parentElement;
        }
    });
    return tocHTML;
};


/***/ },

/***/ 546
(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   T: () => (/* binding */ addStyle)
/* harmony export */ });
var addStyle = function (url, id) {
    if (!document.getElementById(id)) {
        var styleElement = document.createElement("link");
        styleElement.id = id;
        styleElement.rel = "stylesheet";
        styleElement.type = "text/css";
        styleElement.href = url;
        document.getElementsByTagName("head")[0].appendChild(styleElement);
    }
};


/***/ },

/***/ 563
(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   l: () => (/* binding */ mindmapRender)
/* harmony export */ });
/* harmony import */ var _constants__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(802);
/* harmony import */ var _util_addScript__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(84);
/* harmony import */ var _adapterRender__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(586);



var mindmapRender = function (element, cdn, theme) {
    if (element === void 0) { element = document; }
    if (cdn === void 0) { cdn = _constants__WEBPACK_IMPORTED_MODULE_0__/* .Constants */ .Y.CDN; }
    var mindmapElements = _adapterRender__WEBPACK_IMPORTED_MODULE_2__.mindmapRenderAdapter.getElements(element);
    if (mindmapElements.length > 0) {
        (0,_util_addScript__WEBPACK_IMPORTED_MODULE_1__/* .addScript */ .Z)("".concat(cdn, "/dist/js/echarts/echarts.min.js?v=5.5.1"), "vditorEchartsScript").then(function () {
            mindmapElements.forEach(function (e) {
                if (e.parentElement.classList.contains("vditor-wysiwyg__pre") ||
                    e.parentElement.classList.contains("vditor-ir__marker--pre")) {
                    return;
                }
                var text = _adapterRender__WEBPACK_IMPORTED_MODULE_2__.mindmapRenderAdapter.getCode(e);
                if (!text) {
                    return;
                }
                try {
                    if (e.getAttribute("data-processed") === "true") {
                        return;
                    }
                    echarts.init(e, theme === "dark" ? "dark" : undefined).setOption({
                        series: [
                            {
                                data: [JSON.parse(decodeURIComponent(text))],
                                initialTreeDepth: -1,
                                itemStyle: {
                                    borderWidth: 0,
                                    color: "#4285f4",
                                },
                                label: {
                                    backgroundColor: "#f6f8fa",
                                    borderColor: "#d1d5da",
                                    borderRadius: 5,
                                    borderWidth: 0.5,
                                    color: "#586069",
                                    lineHeight: 20,
                                    offset: [-5, 0],
                                    padding: [0, 5],
                                    position: "insideRight",
                                },
                                lineStyle: {
                                    color: "#d1d5da",
                                    width: 1,
                                },
                                roam: true,
                                symbol: function (value, params) {
                                    var _a;
                                    if ((_a = params === null || params === void 0 ? void 0 : params.data) === null || _a === void 0 ? void 0 : _a.children) {
                                        return "circle";
                                    }
                                    else {
                                        return "path://";
                                    }
                                },
                                type: "tree",
                            },
                        ],
                        tooltip: {
                            trigger: "item",
                            triggerOn: "mousemove",
                        },
                    });
                    e.setAttribute("data-processed", "true");
                }
                catch (error) {
                    e.className = "vditor-reset--error";
                    e.innerHTML = "mindmap render error: <br>".concat(error);
                }
            });
        });
    }
};


/***/ },

/***/ 586
(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   SMILESRenderAdapter: () => (/* binding */ SMILESRenderAdapter),
/* harmony export */   abcRenderAdapter: () => (/* binding */ abcRenderAdapter),
/* harmony export */   chartRenderAdapter: () => (/* binding */ chartRenderAdapter),
/* harmony export */   flowchartRenderAdapter: () => (/* binding */ flowchartRenderAdapter),
/* harmony export */   graphvizRenderAdapter: () => (/* binding */ graphvizRenderAdapter),
/* harmony export */   markmapRenderAdapter: () => (/* binding */ markmapRenderAdapter),
/* harmony export */   mathRenderAdapter: () => (/* binding */ mathRenderAdapter),
/* harmony export */   mermaidRenderAdapter: () => (/* binding */ mermaidRenderAdapter),
/* harmony export */   mindmapRenderAdapter: () => (/* binding */ mindmapRenderAdapter),
/* harmony export */   plantumlRenderAdapter: () => (/* binding */ plantumlRenderAdapter),
/* harmony export */   wavedromRenderAdapter: () => (/* binding */ wavedromRenderAdapter)
/* harmony export */ });
var mathRenderAdapter = {
    getCode: function (el) { return el.textContent; },
    getElements: function (element) { return element.querySelectorAll(".language-math"); },
};
var SMILESRenderAdapter = {
    getCode: function (el) { return el.textContent; },
    getElements: function (element) { return element.querySelectorAll(".language-smiles"); },
};
var mermaidRenderAdapter = {
    /** 不仅要返回code，并且需要将 code 设置为 el 的 innerHTML */
    getCode: function (el) { return el.textContent; },
    getElements: function (element) { return element.querySelectorAll(".language-mermaid"); },
};
var markmapRenderAdapter = {
    getCode: function (el) { return el.textContent; },
    getElements: function (element) { return element.querySelectorAll(".language-markmap"); },
};
var mindmapRenderAdapter = {
    getCode: function (el) { return el.getAttribute("data-code"); },
    getElements: function (el) { return el.querySelectorAll(".language-mindmap"); },
};
var chartRenderAdapter = {
    getCode: function (el) { return el.innerText; },
    getElements: function (el) { return el.querySelectorAll(".language-echarts"); },
};
var abcRenderAdapter = {
    getCode: function (el) { return el.textContent; },
    getElements: function (el) { return el.querySelectorAll(".language-abc"); },
};
var graphvizRenderAdapter = {
    getCode: function (el) { return el.textContent; },
    getElements: function (el) { return el.querySelectorAll(".language-graphviz"); },
};
var wavedromRenderAdapter = {
    getCode: function (el) { return el.textContent; },
    getElements: function (el) { return el.querySelectorAll(".language-wavedrom"); },
};
var flowchartRenderAdapter = {
    getCode: function (el) { return el.textContent; },
    getElements: function (el) { return el.querySelectorAll(".language-flowchart"); },
};
var plantumlRenderAdapter = {
    getCode: function (el) { return el.textContent; },
    getElements: function (el) { return el.querySelectorAll(".language-plantuml"); },
};


/***/ },

/***/ 646
(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   e: () => (/* binding */ mermaidRender)
/* harmony export */ });
/* harmony import */ var _constants__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(802);
/* harmony import */ var _util_addScript__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(84);
/* harmony import */ var _adapterRender__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(586);
/* harmony import */ var _util_function__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(210);
var __awaiter = (undefined && undefined.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
var __generator = (undefined && undefined.__generator) || function (thisArg, body) {
    var _ = { label: 0, sent: function() { if (t[0] & 1) throw t[1]; return t[1]; }, trys: [], ops: [] }, f, y, t, g;
    return g = { next: verb(0), "throw": verb(1), "return": verb(2) }, typeof Symbol === "function" && (g[Symbol.iterator] = function() { return this; }), g;
    function verb(n) { return function (v) { return step([n, v]); }; }
    function step(op) {
        if (f) throw new TypeError("Generator is already executing.");
        while (g && (g = 0, op[0] && (_ = 0)), _) try {
            if (f = 1, y && (t = op[0] & 2 ? y["return"] : op[0] ? y["throw"] || ((t = y["return"]) && t.call(y), 0) : y.next) && !(t = t.call(y, op[1])).done) return t;
            if (y = 0, t) op = [op[0] & 2, t.value];
            switch (op[0]) {
                case 0: case 1: t = op; break;
                case 4: _.label++; return { value: op[1], done: false };
                case 5: _.label++; y = op[1]; op = [0]; continue;
                case 7: op = _.ops.pop(); _.trys.pop(); continue;
                default:
                    if (!(t = _.trys, t = t.length > 0 && t[t.length - 1]) && (op[0] === 6 || op[0] === 2)) { _ = 0; continue; }
                    if (op[0] === 3 && (!t || (op[1] > t[0] && op[1] < t[3]))) { _.label = op[1]; break; }
                    if (op[0] === 6 && _.label < t[1]) { _.label = t[1]; t = op; break; }
                    if (t && _.label < t[2]) { _.label = t[2]; _.ops.push(op); break; }
                    if (t[2]) _.ops.pop();
                    _.trys.pop(); continue;
            }
            op = body.call(thisArg, _);
        } catch (e) { op = [6, e]; y = 0; } finally { f = t = 0; }
        if (op[0] & 5) throw op[1]; return { value: op[0] ? op[1] : void 0, done: true };
    }
};




var mermaidRender = function (element, cdn, theme) {
    if (element === void 0) { element = document; }
    if (cdn === void 0) { cdn = _constants__WEBPACK_IMPORTED_MODULE_0__/* .Constants */ .Y.CDN; }
    var mermaidElements = _adapterRender__WEBPACK_IMPORTED_MODULE_2__.mermaidRenderAdapter.getElements(element);
    if (mermaidElements.length === 0) {
        return;
    }
    (0,_util_addScript__WEBPACK_IMPORTED_MODULE_1__/* .addScript */ .Z)("".concat(cdn, "/dist/js/mermaid/mermaid.min.js?v=11.17.2"), "vditorMermaidScript").then(function () {
        var config = {
            securityLevel: "loose",
            altFontFamily: "sans-serif",
            fontFamily: "sans-serif",
            startOnLoad: false,
            flowchart: {
                htmlLabels: true,
                useMaxWidth: !0
            },
            sequence: {
                useMaxWidth: true,
                diagramMarginX: 8,
                diagramMarginY: 8,
                boxMargin: 8,
                showSequenceNumbers: true // Mermaid 时序图增加序号 https://github.com/siyuan-note/siyuan/pull/6992 https://mermaid.js.org/syntax/sequenceDiagram.html#sequencenumbers
            },
            gantt: {
                leftPadding: 75,
                rightPadding: 20
            }
        };
        if (theme === "dark") {
            config.theme = "dark";
        }
        mermaid.initialize(config);
        mermaidElements.forEach(function (item) { return __awaiter(void 0, void 0, void 0, function () {
            var code, id, mermaidData, e_1, errorElement;
            var _a;
            return __generator(this, function (_b) {
                switch (_b.label) {
                    case 0:
                        code = _adapterRender__WEBPACK_IMPORTED_MODULE_2__.mermaidRenderAdapter.getCode(item);
                        if (item.getAttribute("data-processed") === "true" || code.trim() === "") {
                            return [2 /*return*/];
                        }
                        id = "mermaid" + (0,_util_function__WEBPACK_IMPORTED_MODULE_3__/* .genUUID */ .Ee)();
                        _b.label = 1;
                    case 1:
                        _b.trys.push([1, 3, , 4]);
                        return [4 /*yield*/, mermaid.render(id, item.textContent)];
                    case 2:
                        mermaidData = _b.sent();
                        item.innerHTML = mermaidData.svg;
                        (_a = mermaidData.bindFunctions) === null || _a === void 0 ? void 0 : _a.call(mermaidData, item);
                        return [3 /*break*/, 4];
                    case 3:
                        e_1 = _b.sent();
                        errorElement = document.querySelector("#" + id);
                        item.innerHTML = "".concat(errorElement.outerHTML, "<br>\n<div style=\"text-align: left\"><small>").concat(e_1.message.replace(/\n/, "<br>"), "</small></div>");
                        errorElement.parentElement.remove();
                        return [3 /*break*/, 4];
                    case 4:
                        item.setAttribute("data-processed", "true");
                        return [2 /*return*/];
                }
            });
        }); });
    });
};


/***/ },

/***/ 653
(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   d: () => (/* binding */ bindTableWheel)
/* harmony export */ });
var boundElements = new WeakSet();
var bindTableWheel = function (element) {
    if (boundElements.has(element)) {
        return;
    }
    boundElements.add(element);
    element.addEventListener("wheel", function (event) {
        if (!event.cancelable || event.defaultPrevented || event.ctrlKey || event.metaKey || event.altKey || event.shiftKey ||
            event.deltaX !== 0 || event.deltaY === 0) {
            return;
        }
        var target = event.target instanceof Element ? event.target : event.target.parentElement;
        var table = target === null || target === void 0 ? void 0 : target.closest("table");
        if (!table || !element.contains(table) || table.scrollWidth <= table.clientWidth) {
            return;
        }
        var style = getComputedStyle(table);
        if (!/auto|scroll/.test(style.overflowX)) {
            return;
        }
        var scale = event.deltaMode === WheelEvent.DOM_DELTA_LINE ? (parseFloat(style.lineHeight) || 20) :
            event.deltaMode === WheelEvent.DOM_DELTA_PAGE ? table.clientWidth : 1;
        var before = table.scrollLeft;
        table.scrollLeft += event.deltaY * scale * (style.direction === "rtl" ? -1 : 1);
        // 到达横向边界后交给页面滚动，避免滚轮被表格持续截留。
        if (table.scrollLeft !== before) {
            event.preventDefault();
        }
    }, { passive: false });
};


/***/ },

/***/ 656
(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   h: () => (/* binding */ merge)
/* harmony export */ });
var merge = function () {
    var options = [];
    for (var _i = 0; _i < arguments.length; _i++) {
        options[_i] = arguments[_i];
    }
    var target = {};
    var merger = function (obj) {
        for (var prop in obj) {
            if (obj.hasOwnProperty(prop)) {
                if (Object.prototype.toString.call(obj[prop]) === "[object Object]") {
                    target[prop] = merge(target[prop], obj[prop]);
                }
                else {
                    target[prop] = obj[prop];
                }
            }
        }
    };
    for (var i = 0; i < options.length; i++) {
        merger(options[i]);
    }
    return target;
};


/***/ },

/***/ 665
(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   X: () => (/* binding */ setLute)
/* harmony export */ });
/* harmony import */ var _util_codeDOM__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(71);

var setLute = function (options) {
    var lute = Lute.New();
    lute.PutEmojis(options.emojis);
    lute.SetEmojiSite(options.emojiSite);
    lute.SetHeadingAnchor(options.headingAnchor);
    lute.SetInlineMathAllowDigitAfterOpenMarker(options.inlineMathDigit);
    lute.SetAutoSpace(options.autoSpace);
    lute.SetCallout(options.callout);
    lute.SetInlineMath(options.inlineMath);
    lute.SetToC(options.toc);
    lute.SetFootnotes(options.footnotes);
    lute.SetFixTermTypo(options.fixTermTypo);
    lute.SetVditorCodeBlockPreview(options.codeBlockPreview);
    lute.SetVditorMathBlockPreview(options.mathBlockPreview);
    lute.SetSanitize(options.sanitize);
    lute.SetChineseParagraphBeginningSpace(options.paragraphBeginningSpace);
    lute.SetRenderListStyle(options.listStyle);
    lute.SetLinkBase(options.linkBase);
    lute.SetLinkPrefix(options.linkPrefix);
    lute.SetMark(options.mark);
    lute.SetGFMAutoLink(options.gfmAutoLink);
    if (options.lazyLoadImage) {
        lute.SetImageLazyLoading(options.lazyLoadImage);
    }
    lute.SetSup(options.sup);
    lute.SetSub(options.sub);
    lute.SetImgPathAllowSpace(options.imgPathAllowSpace);
    // 编辑区的高亮是临时展示，传入 Lute 的代码正文需保留纯文本和光标标记。
    var conversions = ["SpinVditorDOM", "SpinVditorIRDOM", "VditorDOM2Md", "VditorIRDOM2Md",
        "VditorDOM2HTML", "VditorIRDOM2HTML"];
    conversions.forEach(function (name) {
        var convert = lute[name].bind(lute);
        lute[name] = function (html) { return convert((0,_util_codeDOM__WEBPACK_IMPORTED_MODULE_0__/* .normalizeCodeHTML */ .q)(html)); };
    });
    return lute;
};


/***/ },

/***/ 675
(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   c: () => (/* binding */ hasClosestByHeadings)
/* harmony export */ });
/* unused harmony export hasClosestByTag */
// NOTE: 减少 method.ts 打包，故从 hasClosest.ts 中拆分
var hasClosestByTag = function (element, nodeName) {
    if (!element) {
        return false;
    }
    if (element.nodeType === 3) {
        element = element.parentElement;
    }
    var e = element;
    var isClosest = false;
    while (e && !isClosest && !e.classList.contains("vditor-reset")) {
        if (e.nodeName.indexOf(nodeName) === 0) {
            isClosest = true;
        }
        else {
            e = e.parentElement;
        }
    }
    return isClosest && e;
};
var hasClosestByHeadings = function (element) {
    var headingElement = hasClosestByTag(element, "H");
    if (headingElement && headingElement.tagName.length === 2 && headingElement.tagName !== "HR") {
        return headingElement;
    }
    return false;
};


/***/ },

/***/ 716
(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   m: () => (/* binding */ graphvizRender)
/* harmony export */ });
/* harmony import */ var _constants__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(802);
/* harmony import */ var _adapterRender__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(586);


var graphvizRender = function (element, cdn) {
    if (cdn === void 0) { cdn = _constants__WEBPACK_IMPORTED_MODULE_0__/* .Constants */ .Y.CDN; }
    var graphvizElements = _adapterRender__WEBPACK_IMPORTED_MODULE_1__.graphvizRenderAdapter.getElements(element);
    graphvizElements.forEach(function (e) {
        if (e.parentElement.classList.contains("vditor-wysiwyg__pre") ||
            e.parentElement.classList.contains("vditor-ir__marker--pre")) {
            return;
        }
        var code = _adapterRender__WEBPACK_IMPORTED_MODULE_1__.graphvizRenderAdapter.getCode(e);
        if (e.getAttribute("data-processed") === "true" || code.trim() === "") {
            return;
        }
        var worker;
        var blobUrl;
        var cleanup = function () {
            worker === null || worker === void 0 ? void 0 : worker.terminate();
            if (blobUrl) {
                URL.revokeObjectURL(blobUrl);
            }
        };
        var fail = function (error) {
            e.textContent = "graphviz render error: ".concat(error);
            e.className = "vditor-reset--error";
            cleanup();
        };
        try {
            var scriptUrl = new URL("".concat(cdn, "/dist/js/graphviz/viz.js"), document.baseURI).href;
            var blob = new Blob(["\n                importScripts(".concat(JSON.stringify(scriptUrl), ");\n                const renderer = Viz.instance();\n                self.onmessage = event => {\n                    renderer.then(viz => viz.renderString(event.data, {format: \"svg\"})).then(\n                        svg => self.postMessage({svg}),\n                        error => self.postMessage({error: String(error)})\n                    );\n                };\n            ")], { type: "application/javascript" });
            blobUrl = URL.createObjectURL(blob);
            worker = new Worker(blobUrl);
            worker.onmessage = function (event) {
                if (event.data.error) {
                    fail(event.data.error);
                    return;
                }
                e.innerHTML = event.data.svg;
                cleanup();
            };
            worker.onerror = function (event) {
                event.preventDefault();
                fail(event.message);
            };
            e.setAttribute("data-processed", "true");
            worker.postMessage(code);
        }
        catch (error) {
            fail(String(error));
        }
    });
};


/***/ },

/***/ 802
(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   Y: () => (/* binding */ Constants)
/* harmony export */ });
/* unused harmony export VDITOR_VERSION */
var _VDITOR_VERSION = (/* unused pure expression or super */ null && ("4.0.2-alpha.9"));

var Constants = /** @class */ (function () {
    function Constants() {
    }
    Constants.ZWSP = "\u200b";
    Constants.DROP_EDITOR = "application/editor";
    Constants.MOBILE_WIDTH = 520;
    Constants.CLASS_MENU_DISABLED = "vditor-menu--disabled";
    Constants.EDIT_TOOLBARS = ["emoji", "headings", "bold", "italic", "strike", "link", "list",
        "ordered-list", "outdent", "indent", "check", "line", "quote", "code", "inline-code", "insert-after",
        "insert-before", "upload", "record", "table"];
    Constants.CODE_THEME = ["a11y-dark", "agate", "an-old-hope", "androidstudio",
        "arta", "atom-one-dark", "atom-one-dark-reasonable", "base16/3024", "base16/apathy", "base16/apprentice", "base16/ashes", "base16/atelier-cave", "base16/atelier-dune",
        "base16/atelier-estuary", "base16/atelier-forest", "base16/atelier-heath", "base16/atelier-lakeside", "base16/atelier-plateau", "base16/atelier-savanna", "base16/atelier-seaside", "base16/atelier-sulphurpool",
        "base16/atlas", "base16/bespin", "base16/black-metal", "base16/black-metal-bathory", "base16/black-metal-burzum", "base16/black-metal-dark-funeral", "base16/black-metal-gorgoroth", "base16/black-metal-immortal", "base16/black-metal-khold", "base16/black-metal-marduk", "base16/black-metal-mayhem", "base16/black-metal-nile", "base16/black-metal-venom", "base16/brewer", "base16/bright", "base16/brogrammer",
        "base16/brush-trees-dark", "base16/chalk", "base16/circus", "base16/classic-dark", "base16/codeschool", "base16/colors", "base16/danqing", "base16/darcula", "base16/dark-violet",
        "base16/darkmoss", "base16/darktooth", "base16/decaf", "base16/default-dark", "base16/dracula", "base16/edge-dark", "base16/eighties", "base16/embers", "base16/equilibrium-dark",
        "base16/equilibrium-gray-dark", "base16/espresso", "base16/eva", "base16/eva-dim", "base16/flat", "base16/framer", "base16/gigavolt", "base16/google-dark", "base16/grayscale-dark", "base16/green-screen", "base16/gruvbox-dark-hard", "base16/gruvbox-dark-medium",
        "base16/gruvbox-dark-pale", "base16/gruvbox-dark-soft", "base16/hardcore", "base16/harmonic16-dark", "base16/heetch-dark", "base16/helios", "base16/hopscotch", "base16/horizon-dark", "base16/humanoid-dark", "base16/ia-dark", "base16/icy-dark", "base16/ir-black", "base16/isotope",
        "base16/kimber", "base16/london-tube", "base16/macintosh", "base16/marrakesh", "base16/materia", "base16/material", "base16/material-darker", "base16/material-palenight", "base16/material-vivid",
        "base16/mellow-purple", "base16/mocha", "base16/monokai", "base16/nebula", "base16/nord", "base16/nova", "base16/ocean", "base16/oceanicnext", "base16/onedark", "base16/outrun-dark",
        "base16/papercolor-dark", "base16/paraiso", "base16/pasque", "base16/phd", "base16/pico", "base16/pop", "base16/porple", "base16/qualia", "base16/railscasts", "base16/rebecca",
        "base16/ros-pine", "base16/ros-pine-moon", "base16/sandcastle", "base16/seti-ui", "base16/silk-dark", "base16/snazzy", "base16/solar-flare", "base16/solarized-dark", "base16/spacemacs", "base16/summercamp", "base16/summerfruit-dark",
        "base16/synth-midnight-terminal-dark", "base16/tango", "base16/tender", "base16/tomorrow-night", "base16/twilight", "base16/unikitty-dark", "base16/vulcan",
        "base16/windows-10", "base16/windows-95", "base16/windows-high-contrast", "base16/windows-nt", "base16/woodland", "base16/xcode-dusk", "base16/zenburn", "codepen-embed", "dark",
        "devibeans", "far", "felipec", "github-dark", "github-dark-dimmed", "gml", "gradient-dark", "hybrid", "ir-black", "isbl-editor-dark", "kimbie-dark", "lioshi",
        "monokai", "monokai-sublime", "night-owl", "nnfx-dark", "nord", "obsidian", "panda-syntax-dark", "paraiso-dark", "pojoaque", "qtcreator-dark", "rainbow", "shades-of-purple", "srcery", "stackoverflow-dark",
        "sunburst", "tomorrow-night-blue", "tomorrow-night-bright", "tokyo-night-dark", "vs2015", "xt256",
        "ant-design",
        "a11y-light", "arduino-light", "ascetic", "atom-one-light", "base16/atelier-cave-light",
        "base16/atelier-dune-light", "base16/atelier-estuary-light", "base16/atelier-forest-light", "base16/atelier-heath-light",
        "base16/atelier-lakeside-light", "base16/atelier-plateau-light", "base16/atelier-savanna-light", "base16/atelier-seaside-light", "base16/atelier-sulphurpool-light", "base16/brush-trees",
        "base16/classic-light", "base16/cupcake", "base16/cupertino", "base16/default-light", "base16/dirtysea", "base16/edge-light", "base16/equilibrium-gray-light", "base16/equilibrium-light",
        "base16/fruit-soda", "base16/github", "base16/google-light", "base16/grayscale-light", "base16/gruvbox-light-hard", "base16/gruvbox-light-medium", "base16/gruvbox-light-soft",
        "base16/harmonic16-light", "base16/heetch-light", "base16/humanoid-light", "base16/horizon-light", "base16/ia-light", "base16/material-lighter", "base16/mexico-light",
        "base16/one-light", "base16/papercolor-light", "base16/ros-pine-dawn", "base16/sagelight", "base16/shapeshifter",
        "base16/silk-light", "base16/solar-flare-light", "base16/solarized-light", "base16/summerfruit-light", "base16/synth-midnight-terminal-light", "base16/tomorrow",
        "base16/unikitty-light", "base16/windows-10-light", "base16/windows-95-light", "base16/windows-high-contrast-light", "brown-paper", "base16/windows-nt-light",
        "color-brewer", "docco", "foundation", "github", "googlecode", "gradient-light", "grayscale", "idea", "intellij-light", "isbl-editor-light", "kimbie-light",
        "lightfair", "magula", "mono-blue", "nnfx-light", "panda-syntax-light", "paraiso-light", "purebasic", "qtcreator-light", "routeros", "school-book",
        "stackoverflow-light", "tokyo-night-light", "vs", "xcode", "default"];
    Constants.ALIAS_CODE_LANGUAGES = [
        // 自定义
        "abc", "plantuml", "mermaid", "flowchart", "echarts", "mindmap", "graphviz", "wavedrom", "math", "markmap", "smiles",
        // 别名
        "js", "ts", "html", "toml", "c#", "bat"
    ];
    Constants.CDN = "https://unpkg.com/vditor@".concat("4.0.2-alpha.9");
    Constants.MARKDOWN_OPTIONS = {
        autoSpace: false,
        callout: true,
        inlineMath: true,
        gfmAutoLink: true,
        codeBlockPreview: true,
        fixTermTypo: false,
        footnotes: true,
        imgPathAllowSpace: false,
        imageCaption: false,
        linkBase: "",
        linkPrefix: "",
        listStyle: false,
        mark: false,
        mathBlockPreview: true,
        paragraphBeginningSpace: false,
        sanitize: true,
        sub: false,
        sup: false,
        toc: false,
    };
    Constants.HLJS_OPTIONS = {
        enable: true,
        lineNumber: false,
        defaultLang: "",
        style: "github",
    };
    Constants.MATH_OPTIONS = {
        engine: "KaTeX",
        inlineDigit: false,
        macros: {},
    };
    Constants.PLANTUML_OPTIONS = {
        server: "https://www.plantuml.com/plantuml/svg/",
    };
    Constants.THEME_OPTIONS = {
        current: "light",
        list: {
            "ant-design": "Ant Design",
            "dark": "Dark",
            "light": "Light",
            "wechat": "WeChat",
        },
        path: "".concat(Constants.CDN, "/dist/css/content-theme"),
    };
    return Constants;
}());



/***/ },

/***/ 814
(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   h: () => (/* binding */ setCodeTheme)
/* harmony export */ });
/* harmony import */ var _constants__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(802);
/* harmony import */ var _util_addStyle__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(546);


var setCodeTheme = function (codeTheme, cdn) {
    if (cdn === void 0) { cdn = _constants__WEBPACK_IMPORTED_MODULE_0__/* .Constants */ .Y.CDN; }
    if (!_constants__WEBPACK_IMPORTED_MODULE_0__/* .Constants */ .Y.CODE_THEME.includes(codeTheme)) {
        codeTheme = "github";
    }
    var vditorHljsStyle = document.getElementById("vditorHljsStyle");
    var href = "".concat(cdn, "/dist/js/highlight.js/styles/").concat(codeTheme, ".min.css");
    if (!vditorHljsStyle) {
        (0,_util_addStyle__WEBPACK_IMPORTED_MODULE_1__/* .addStyle */ .T)(href, "vditorHljsStyle");
    }
    else if (vditorHljsStyle.getAttribute('href') !== href) {
        vditorHljsStyle.remove();
        (0,_util_addStyle__WEBPACK_IMPORTED_MODULE_1__/* .addStyle */ .T)(href, "vditorHljsStyle");
    }
};


/***/ },

/***/ 828
(__unused_webpack_module, __webpack_exports__, __webpack_require__) {


// EXPORTS
__webpack_require__.d(__webpack_exports__, {
  $: () => (/* binding */ highlightRender)
});

// EXTERNAL MODULE: ./src/ts/constants.ts
var constants = __webpack_require__(802);
// EXTERNAL MODULE: ./src/ts/util/addScript.ts
var addScript = __webpack_require__(84);
// EXTERNAL MODULE: ./src/ts/util/addStyle.ts
var addStyle = __webpack_require__(546);
;// ./src/ts/util/codeSelection.ts
var setCodeHighlight = function (code, html) {
    var selection = getSelection();
    var endpoints = [selection.anchorNode, selection.focusNode].map(function (node, index) {
        var offset = index === 0 ? selection.anchorOffset : selection.focusOffset;
        if (!node || !code.contains(node)) {
            return { node: node, offset: offset, inside: false };
        }
        var range = document.createRange();
        range.selectNodeContents(code);
        range.setEnd(node, offset);
        return { node: node, offset: range.toString().length, inside: true };
    });
    code.innerHTML = html;
    if (!endpoints.some(function (endpoint) { return endpoint.inside; })) {
        return;
    }
    // 高亮会重建嵌套文本节点，按正文偏移恢复正向、反向及跨代码块选区。
    endpoints.forEach(function (endpoint) {
        if (!endpoint.inside) {
            return;
        }
        var walker = document.createTreeWalker(code, NodeFilter.SHOW_TEXT);
        var node = walker.nextNode();
        while (node) {
            if (endpoint.offset <= node.textContent.length) {
                endpoint.node = node;
                return;
            }
            endpoint.offset -= node.textContent.length;
            node = walker.nextNode();
        }
        endpoint.node = code;
        endpoint.offset = code.childNodes.length;
    });
    selection.setBaseAndExtent(endpoints[0].node, endpoints[0].offset, endpoints[1].node, endpoints[1].offset);
};

;// ./src/ts/markdown/highlightRender.ts




var highlightRender = function (hljsOption, element, cdn, canRenderEditable) {
    if (element === void 0) { element = document; }
    if (cdn === void 0) { cdn = constants/* Constants */.Y.CDN; }
    var style = hljsOption.style;
    if (!constants/* Constants */.Y.CODE_THEME.includes(style)) {
        style = "github";
    }
    var vditorHljsStyle = document.getElementById("vditorHljsStyle");
    var href = "".concat(cdn, "/dist/js/highlight.js/styles/").concat(style, ".min.css");
    if (vditorHljsStyle && vditorHljsStyle.getAttribute('href') !== href) {
        vditorHljsStyle.remove();
    }
    (0,addStyle/* addStyle */.T)("".concat(cdn, "/dist/js/highlight.js/styles/").concat(style, ".min.css"), "vditorHljsStyle");
    if (hljsOption.enable === false) {
        return;
    }
    var codes = element.querySelectorAll("pre > code");
    if (codes.length === 0) {
        return;
    }
    (0,addScript/* addScript */.Z)("".concat(cdn, "/dist/js/highlight.js/highlight.min.js?v=11.7.0"), "vditorHljsScript").then(function () {
        (0,addScript/* addScript */.Z)("".concat(cdn, "/dist/js/highlight.js/third-languages.js?v=1.0.1"), "vditorHljsThirdScript").then(function () {
            element.querySelectorAll("pre > code").forEach(function (block) {
                var _a;
                if (canRenderEditable && (!canRenderEditable() || block.querySelector("wbr"))) {
                    return;
                }
                if (!canRenderEditable && (block.parentElement.classList.contains("vditor-ir__marker--pre") ||
                    block.parentElement.classList.contains("vditor-wysiwyg__pre"))) {
                    return;
                }
                if (block.classList.contains("language-mermaid") || block.classList.contains("language-flowchart") ||
                    block.classList.contains("language-echarts") || block.classList.contains("language-mindmap") ||
                    block.classList.contains("language-plantuml") || block.classList.contains("language-smiles") ||
                    block.classList.contains("language-abc") || block.classList.contains("language-graphviz") ||
                    block.classList.contains("language-math")) {
                    return;
                }
                if (!canRenderEditable && hljsOption.defaultLang !== "" && block.className.indexOf("language-") === -1) {
                    block.classList.add("language-" + hljsOption.defaultLang);
                }
                block.querySelectorAll(".vditor-linenumber__temp, .vditor-linenumber__rows").forEach(function (item) { return item.remove(); });
                block.classList.remove("vditor-linenumber");
                var language = ((_a = Array.from(block.classList).find(function (name) { return name.startsWith("language-"); })) === null || _a === void 0 ? void 0 : _a.slice(9)) ||
                    hljsOption.defaultLang;
                if (!window.hljs.getLanguage(language)) {
                    language = "plaintext";
                }
                var html = window.hljs.highlight(block.textContent, {
                    language: language,
                    ignoreIllegals: true
                }).value;
                if (canRenderEditable) {
                    block.setAttribute("data-code-highlight", "true");
                    setCodeHighlight(block, html);
                }
                else {
                    block.innerHTML = html;
                }
                block.classList.add("hljs");
                if (canRenderEditable || !hljsOption.lineNumber) {
                    return;
                }
                block.classList.add("vditor-linenumber");
                var linenNumberTemp = block.querySelector(".vditor-linenumber__temp");
                if (!linenNumberTemp) {
                    linenNumberTemp = document.createElement("div");
                    linenNumberTemp.className = "vditor-linenumber__temp";
                    block.insertAdjacentElement("beforeend", linenNumberTemp);
                }
                var whiteSpace = getComputedStyle(block).whiteSpace;
                var isSoftWrap = false;
                if (whiteSpace === "pre-wrap" || whiteSpace === "pre-line") {
                    isSoftWrap = true;
                }
                var lineNumberHTML = "";
                var lineList = block.textContent.split(/\r\n|\r|\n/g);
                if (lineList.length > 1 && lineList[lineList.length - 1] === "") {
                    lineList.pop();
                }
                lineList.map(function (line) {
                    var lineHeight = "";
                    if (isSoftWrap) {
                        linenNumberTemp.textContent = line || "\n";
                        lineHeight = " style=\"height:".concat(linenNumberTemp.getBoundingClientRect().height, "px\"");
                    }
                    lineNumberHTML += "<span".concat(lineHeight, "></span>");
                });
                linenNumberTemp.remove();
                lineNumberHTML = "<span class=\"vditor-linenumber__rows\">".concat(lineNumberHTML, "</span>");
                block.insertAdjacentHTML("beforeend", lineNumberHTML);
            });
        });
    });
};


/***/ },

/***/ 841
(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   o: () => (/* binding */ previewImage)
/* harmony export */ });
var previewImage = function (oldImgElement, lang, theme) {
    if (lang === void 0) { lang = "zh_CN"; }
    if (theme === void 0) { theme = "classic"; }
    var oldImgRect = oldImgElement.getBoundingClientRect();
    var height = 36;
    document.body.insertAdjacentHTML("beforeend", "<div class=\"vditor vditor-img".concat(theme === "dark" ? " vditor--dark" : "", "\">\n    <div class=\"vditor-img__bar\">\n      <span class=\"vditor-img__btn\" data-deg=\"0\">\n        <svg><use xlink:href=\"#vditor-icon-redo\"></use></svg>\n        ").concat(window.VditorI18n.spin, "\n      </span>\n      <span class=\"vditor-img__btn\"  onclick=\"this.parentElement.parentElement.outerHTML = '';document.body.style.overflow = ''\">\n        X &nbsp;").concat(window.VditorI18n.close, "\n      </span>\n    </div>\n    <div class=\"vditor-img__img\" onclick=\"this.parentElement.outerHTML = '';document.body.style.overflow = ''\">\n      <img style=\"width: ").concat(oldImgElement.width, "px;height:").concat(oldImgElement.height, "px;transform: translate3d(").concat(oldImgRect.left, "px, ").concat(oldImgRect.top - height, "px, 0)\" src=\"").concat(oldImgElement.getAttribute("src"), "\">\n    </div>\n</div>"));
    document.body.style.overflow = "hidden";
    // 图片从原始位置移动到预览正中间的动画效果
    var imgElement = document.querySelector(".vditor-img img");
    var translate3d = "translate3d(".concat(Math.max(0, window.innerWidth - oldImgElement.naturalWidth) / 2, "px, ").concat(Math.max(0, window.innerHeight - height - oldImgElement.naturalHeight) / 2, "px, 0)");
    setTimeout(function () {
        imgElement.setAttribute("style", "transition: transform .3s ease-in-out;transform: ".concat(translate3d));
        setTimeout(function () {
            imgElement.parentElement.scrollTo((imgElement.parentElement.scrollWidth - imgElement.parentElement.clientWidth) / 2, (imgElement.parentElement.scrollHeight - imgElement.parentElement.clientHeight) / 2);
        }, 400);
    });
    // 旋转
    var btnElement = document.querySelector(".vditor-img__btn");
    btnElement.addEventListener("click", function () {
        var deg = parseInt(btnElement.getAttribute("data-deg"), 10) + 90;
        if ((deg / 90) % 2 === 1 && oldImgElement.naturalWidth > imgElement.parentElement.clientHeight) {
            imgElement.style.transform = "translate3d(".concat(Math.max(0, window.innerWidth - oldImgElement.naturalWidth) / 2, "px, ").concat(oldImgElement.naturalWidth / 2 - oldImgElement.naturalHeight / 2, "px, 0) rotateZ(").concat(deg, "deg)");
        }
        else {
            imgElement.style.transform = "".concat(translate3d, " rotateZ(").concat(deg, "deg)");
        }
        btnElement.setAttribute("data-deg", deg.toString());
        setTimeout(function () {
            imgElement.parentElement.scrollTo((imgElement.parentElement.scrollWidth - imgElement.parentElement.clientWidth) / 2, (imgElement.parentElement.scrollHeight - imgElement.parentElement.clientHeight) / 2);
        }, 400);
    });
};


/***/ },

/***/ 858
(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   I: () => (/* binding */ wavedromRender)
/* harmony export */ });
/* harmony import */ var _constants__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(802);
/* harmony import */ var _util_addScript__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(84);
/* harmony import */ var _util_function__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(210);
/* harmony import */ var _adapterRender__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(586);
var __awaiter = (undefined && undefined.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
var __generator = (undefined && undefined.__generator) || function (thisArg, body) {
    var _ = { label: 0, sent: function() { if (t[0] & 1) throw t[1]; return t[1]; }, trys: [], ops: [] }, f, y, t, g;
    return g = { next: verb(0), "throw": verb(1), "return": verb(2) }, typeof Symbol === "function" && (g[Symbol.iterator] = function() { return this; }), g;
    function verb(n) { return function (v) { return step([n, v]); }; }
    function step(op) {
        if (f) throw new TypeError("Generator is already executing.");
        while (g && (g = 0, op[0] && (_ = 0)), _) try {
            if (f = 1, y && (t = op[0] & 2 ? y["return"] : op[0] ? y["throw"] || ((t = y["return"]) && t.call(y), 0) : y.next) && !(t = t.call(y, op[1])).done) return t;
            if (y = 0, t) op = [op[0] & 2, t.value];
            switch (op[0]) {
                case 0: case 1: t = op; break;
                case 4: _.label++; return { value: op[1], done: false };
                case 5: _.label++; y = op[1]; op = [0]; continue;
                case 7: op = _.ops.pop(); _.trys.pop(); continue;
                default:
                    if (!(t = _.trys, t = t.length > 0 && t[t.length - 1]) && (op[0] === 6 || op[0] === 2)) { _ = 0; continue; }
                    if (op[0] === 3 && (!t || (op[1] > t[0] && op[1] < t[3]))) { _.label = op[1]; break; }
                    if (op[0] === 6 && _.label < t[1]) { _.label = t[1]; t = op; break; }
                    if (t && _.label < t[2]) { _.label = t[2]; _.ops.push(op); break; }
                    if (t[2]) _.ops.pop();
                    _.trys.pop(); continue;
            }
            op = body.call(thisArg, _);
        } catch (e) { op = [6, e]; y = 0; } finally { f = t = 0; }
        if (op[0] & 5) throw op[1]; return { value: op[0] ? op[1] : void 0, done: true };
    }
};




var wavedromIndex = 0;
var wavedromRender = function (element, cdn) {
    if (element === void 0) { element = document; }
    if (cdn === void 0) { cdn = _constants__WEBPACK_IMPORTED_MODULE_0__/* .Constants */ .Y.CDN; }
    var wavedromElements = _adapterRender__WEBPACK_IMPORTED_MODULE_3__.wavedromRenderAdapter.getElements(element);
    if (wavedromElements.length === 0) {
        return;
    }
    (0,_util_addScript__WEBPACK_IMPORTED_MODULE_1__/* .addScript */ .Z)("".concat(cdn, "/dist/js/wavedrom/wavedrom.min.js?v=3.6.2"), "vditorWavedromScript").then(function () {
        wavedromElements.forEach(function (item) { return __awaiter(void 0, void 0, void 0, function () {
            var code, renderElement, source, error_1, message, lineBreak;
            return __generator(this, function (_a) {
                switch (_a.label) {
                    case 0:
                        if (item.parentElement.classList.contains("vditor-wysiwyg__pre") ||
                            item.parentElement.classList.contains("vditor-ir__marker--pre")) {
                            return [2 /*return*/];
                        }
                        code = _adapterRender__WEBPACK_IMPORTED_MODULE_3__.wavedromRenderAdapter.getCode(item);
                        if (item.getAttribute("data-processed") === "true" || code.trim() === "") {
                            return [2 /*return*/];
                        }
                        renderElement = item;
                        if (item.tagName === "CODE") {
                            renderElement = document.createElement("div");
                            Array.from(item.attributes).forEach(function (attribute) {
                                renderElement.setAttribute(attribute.name, attribute.value);
                            });
                            item.replaceWith(renderElement);
                        }
                        _a.label = 1;
                    case 1:
                        _a.trys.push([1, 3, , 4]);
                        return [4 /*yield*/, (0,_util_function__WEBPACK_IMPORTED_MODULE_2__/* .looseJsonParse */ .kY)(code)];
                    case 2:
                        source = _a.sent();
                        wavedrom.renderWaveElement(wavedromIndex, source, renderElement, wavedrom.waveSkin, false);
                        wavedromIndex++;
                        return [3 /*break*/, 4];
                    case 3:
                        error_1 = _a.sent();
                        message = error_1 instanceof Error ? error_1.message : String(error_1);
                        lineBreak = document.createElement("br");
                        renderElement.replaceChildren(document.createTextNode("wavedrom render error:"), lineBreak, document.createTextNode(message));
                        renderElement.classList.add("vditor-reset--error");
                        return [3 /*break*/, 4];
                    case 4:
                        renderElement.setAttribute("data-processed", "true");
                        return [2 /*return*/];
                }
            });
        }); });
    });
};


/***/ },

/***/ 948
(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   Y: () => (/* binding */ SMILESRender)
/* harmony export */ });
/* harmony import */ var _constants__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(802);
/* harmony import */ var _util_addScript__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(84);
/* harmony import */ var _adapterRender__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(586);
/* harmony import */ var _util_function__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(210);




var SMILESRender = function (element, cdn, theme) {
    if (element === void 0) { element = document; }
    if (cdn === void 0) { cdn = _constants__WEBPACK_IMPORTED_MODULE_0__/* .Constants */ .Y.CDN; }
    var SMILESElements = _adapterRender__WEBPACK_IMPORTED_MODULE_2__.SMILESRenderAdapter.getElements(element);
    if (SMILESElements.length > 0) {
        (0,_util_addScript__WEBPACK_IMPORTED_MODULE_1__/* .addScript */ .Z)("".concat(cdn, "/dist/js/smiles-drawer/smiles-drawer.min.js?v=2.1.7"), "vditorAbcjsScript").then(function () {
            var sd = new SmiDrawer({}, {});
            SMILESElements.forEach(function (item) {
                var code = _adapterRender__WEBPACK_IMPORTED_MODULE_2__.SMILESRenderAdapter.getCode(item).trim();
                if (item.getAttribute("data-processed") === "true" || code.trim() === "") {
                    return;
                }
                var id = "smiles" + (0,_util_function__WEBPACK_IMPORTED_MODULE_3__/* .genUUID */ .Ee)();
                item.innerHTML = "<svg id=\"".concat(id, "\"></svg>");
                sd.draw(code, '#' + id, theme === "dark" ? "dark" : undefined);
                item.setAttribute("data-processed", "true");
            });
        });
    }
};


/***/ },

/***/ 988
(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   H: () => (/* binding */ setContentTheme)
/* harmony export */ });
/* harmony import */ var _util_addStyle__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(546);

var setContentTheme = function (contentTheme, path) {
    if (!contentTheme || !path) {
        return;
    }
    var vditorContentTheme = document.getElementById("vditorContentTheme");
    var cssPath = "".concat(path, "/").concat(contentTheme, ".css");
    if (!vditorContentTheme) {
        (0,_util_addStyle__WEBPACK_IMPORTED_MODULE_0__/* .addStyle */ .T)(cssPath, "vditorContentTheme");
    }
    else if (vditorContentTheme.getAttribute("href") !== cssPath) {
        vditorContentTheme.remove();
        (0,_util_addStyle__WEBPACK_IMPORTED_MODULE_0__/* .addStyle */ .T)(cssPath, "vditorContentTheme");
    }
};


/***/ },

/***/ 994
(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   p: () => (/* binding */ code160to32)
/* harmony export */ });
var code160to32 = function (text) {
    // 非打断空格转换为空格
    return text.replace(/\u00a0/g, " ");
};


/***/ }

/******/ });
/************************************************************************/
/******/ // The module cache
/******/ var __webpack_module_cache__ = {};
/******/ 
/******/ // The require function
/******/ function __webpack_require__(moduleId) {
/******/ 	// Check if module is in cache
/******/ 	var cachedModule = __webpack_module_cache__[moduleId];
/******/ 	if (cachedModule !== undefined) {
/******/ 		return cachedModule.exports;
/******/ 	}
/******/ 	// Create a new module (and put it into the cache)
/******/ 	var module = __webpack_module_cache__[moduleId] = {
/******/ 		// no module.id needed
/******/ 		// no module.loaded needed
/******/ 		exports: {}
/******/ 	};
/******/ 
/******/ 	// Execute the module function
/******/ 	__webpack_modules__[moduleId](module, module.exports, __webpack_require__);
/******/ 
/******/ 	// Return the exports of the module
/******/ 	return module.exports;
/******/ }
/******/ 
/************************************************************************/
/******/ /* webpack/runtime/define property getters */
/******/ (() => {
/******/ 	// define getter functions for harmony exports
/******/ 	__webpack_require__.d = (exports, definition) => {
/******/ 		for(var key in definition) {
/******/ 			if(__webpack_require__.o(definition, key) && !__webpack_require__.o(exports, key)) {
/******/ 				Object.defineProperty(exports, key, { enumerable: true, get: definition[key] });
/******/ 			}
/******/ 		}
/******/ 	};
/******/ })();
/******/ 
/******/ /* webpack/runtime/hasOwnProperty shorthand */
/******/ (() => {
/******/ 	__webpack_require__.o = (obj, prop) => (Object.prototype.hasOwnProperty.call(obj, prop))
/******/ })();
/******/ 
/******/ /* webpack/runtime/make namespace object */
/******/ (() => {
/******/ 	// define __esModule on exports
/******/ 	__webpack_require__.r = (exports) => {
/******/ 		if(typeof Symbol !== 'undefined' && Symbol.toStringTag) {
/******/ 			Object.defineProperty(exports, Symbol.toStringTag, { value: 'Module' });
/******/ 		}
/******/ 		Object.defineProperty(exports, '__esModule', { value: true });
/******/ 	};
/******/ })();
/******/ 
/************************************************************************/
var __webpack_exports__ = {};

// EXTERNAL MODULE: ./src/ts/markdown/abcRender.ts
var abcRender = __webpack_require__(305);
// EXTERNAL MODULE: ./src/ts/markdown/adapterRender.ts
var adapterRender = __webpack_require__(586);
// EXTERNAL MODULE: ./src/ts/markdown/chartRender.ts
var chartRender = __webpack_require__(345);
// EXTERNAL MODULE: ./src/ts/markdown/codeRender.ts + 1 modules
var codeRender = __webpack_require__(63);
// EXTERNAL MODULE: ./src/ts/markdown/flowchartRender.ts
var flowchartRender = __webpack_require__(225);
// EXTERNAL MODULE: ./src/ts/markdown/graphvizRender.ts
var graphvizRender = __webpack_require__(716);
// EXTERNAL MODULE: ./src/ts/markdown/highlightRender.ts + 1 modules
var highlightRender = __webpack_require__(828);
;// ./src/ts/markdown/lazyLoadImageRender.ts
var lazyLoadImageRender = function (element) {
    if (element === void 0) { element = document; }
    var loadImg = function (it) {
        var testImage = document.createElement("img");
        testImage.src = it.getAttribute("data-src");
        testImage.addEventListener("load", function () {
            if (!it.getAttribute("style") && !it.getAttribute("class") &&
                !it.getAttribute("width") && !it.getAttribute("height")) {
                if (testImage.naturalHeight > testImage.naturalWidth &&
                    testImage.naturalWidth / testImage.naturalHeight <
                        document.querySelector(".vditor-reset").clientWidth / (window.innerHeight - 40) &&
                    testImage.naturalHeight > (window.innerHeight - 40)) {
                    it.style.height = (window.innerHeight - 40) + "px";
                }
            }
            it.src = testImage.src;
        });
        it.removeAttribute("data-src");
    };
    if (!("IntersectionObserver" in window)) {
        element.querySelectorAll("img").forEach(function (imgElement) {
            if (imgElement.getAttribute("data-src")) {
                loadImg(imgElement);
            }
        });
        return false;
    }
    if (window.vditorImageIntersectionObserver) {
        window.vditorImageIntersectionObserver.disconnect();
        element.querySelectorAll("img").forEach(function (imgElement) {
            window.vditorImageIntersectionObserver.observe(imgElement);
        });
    }
    else {
        window.vditorImageIntersectionObserver = new IntersectionObserver(function (entries) {
            entries.forEach(function (entrie) {
                if ((typeof entrie.isIntersecting === "undefined"
                    ? entrie.intersectionRatio !== 0
                    : entrie.isIntersecting)
                    && entrie.target.getAttribute("data-src")) {
                    loadImg(entrie.target);
                }
            });
        });
        element.querySelectorAll("img").forEach(function (imgElement) {
            window.vditorImageIntersectionObserver.observe(imgElement);
        });
    }
};

// EXTERNAL MODULE: ./src/ts/markdown/mathRender.ts
var mathRender = __webpack_require__(291);
// EXTERNAL MODULE: ./src/ts/markdown/mediaRender.ts
var mediaRender = __webpack_require__(45);
// EXTERNAL MODULE: ./src/ts/markdown/mermaidRender.ts
var mermaidRender = __webpack_require__(646);
// EXTERNAL MODULE: ./src/ts/markdown/SMILESRender.ts
var SMILESRender = __webpack_require__(948);
// EXTERNAL MODULE: ./src/ts/markdown/markmapRender.ts
var markmapRender = __webpack_require__(476);
// EXTERNAL MODULE: ./src/ts/markdown/mindmapRender.ts
var mindmapRender = __webpack_require__(563);
// EXTERNAL MODULE: ./src/ts/markdown/outlineRender.ts
var outlineRender = __webpack_require__(483);
// EXTERNAL MODULE: ./src/ts/markdown/plantumlRender.ts
var plantumlRender = __webpack_require__(320);
// EXTERNAL MODULE: ./src/ts/markdown/wavedromRender.ts
var wavedromRender = __webpack_require__(858);
// EXTERNAL MODULE: ./src/ts/constants.ts
var constants = __webpack_require__(802);
// EXTERNAL MODULE: ./src/ts/ui/setContentTheme.ts
var setContentTheme = __webpack_require__(988);
// EXTERNAL MODULE: ./src/ts/util/addScript.ts
var addScript = __webpack_require__(84);
// EXTERNAL MODULE: ./src/ts/util/hasClosest.ts
var hasClosest = __webpack_require__(57);
// EXTERNAL MODULE: ./src/ts/util/merge.ts
var merge = __webpack_require__(656);
// EXTERNAL MODULE: ./src/ts/util/tableWheel.ts
var tableWheel = __webpack_require__(653);
;// ./src/ts/markdown/anchorRender.ts
var anchorRender = function (type) {
    document.querySelectorAll(".vditor-anchor").forEach(function (anchor) {
        if (type === 1) {
            anchor.classList.add("vditor-anchor--left");
        }
        anchor.onclick = function () {
            var id = anchor.getAttribute("href").substr(1);
            var top = document.getElementById("vditorAnchor-" + id).offsetTop;
            document.querySelector("html").scrollTop = top;
        };
    });
    window.onhashchange = function () {
        var element = document.getElementById("vditorAnchor-" + decodeURIComponent(window.location.hash.substr(1)));
        if (element) {
            document.querySelector("html").scrollTop = element.offsetTop;
        }
    };
};

// EXTERNAL MODULE: ./src/ts/markdown/imageCaptionRender.ts
var imageCaptionRender = __webpack_require__(140);
// EXTERNAL MODULE: ./src/ts/markdown/setLute.ts
var setLute = __webpack_require__(665);
// EXTERNAL MODULE: ./src/ts/util/selection.ts
var selection = __webpack_require__(382);
;// ./src/ts/markdown/speechRender.ts

var speechRender = function (element, lang) {
    if (lang === void 0) { lang = "zh_CN"; }
    if (typeof speechSynthesis === "undefined" || typeof SpeechSynthesisUtterance === "undefined") {
        return;
    }
    var getVoice = function () {
        var voices = speechSynthesis.getVoices();
        var currentVoice;
        var defaultVoice;
        voices.forEach(function (item) {
            if (item.lang === lang.replace("_", "-")) {
                currentVoice = item;
            }
            if (item.default) {
                defaultVoice = item;
            }
        });
        if (!currentVoice) {
            currentVoice = defaultVoice;
        }
        return currentVoice;
    };
    var playSVG = '<svg><use xlink:href="#vditor-icon-play"></use></svg>';
    var pauseSVG = '<svg><use xlink:href="#vditor-icon-pause"></use></svg>';
    if (!document.getElementById("vditorIconScript")) {
        playSVG = '<svg viewBox="0 0 32 32"><path d="M3.436 0l25.128 16-25.128 16v-32z"></path></svg>';
        pauseSVG = '<svg viewBox="0 0 32 32"><path d="M20.617 0h9.128v32h-9.128v-32zM2.255 32v-32h9.128v32h-9.128z"></path></svg>';
    }
    var speechDom = document.querySelector(".vditor-speech");
    if (!speechDom) {
        speechDom = document.createElement("button");
        speechDom.className = "vditor-speech";
        element.insertAdjacentElement("beforeend", speechDom);
        if (speechSynthesis.onvoiceschanged !== undefined) {
            speechSynthesis.onvoiceschanged = getVoice;
        }
    }
    var voice = getVoice();
    var utterThis = new SpeechSynthesisUtterance();
    utterThis.voice = voice;
    utterThis.onend = utterThis.onerror = function () {
        speechDom.style.display = "none";
        speechSynthesis.cancel();
        speechDom.classList.remove("vditor-speech--current");
        speechDom.innerHTML = playSVG;
    };
    element.addEventListener(window.ontouchstart !== undefined ? "touchend" : "click", function (event) {
        var target = event.target;
        if (target.classList.contains("vditor-speech") || target.parentElement.classList.contains("vditor-speech")) {
            if (!speechDom.classList.contains("vditor-speech--current")) {
                utterThis.text = speechDom.getAttribute("data-text");
                speechSynthesis.speak(utterThis);
                speechDom.classList.add("vditor-speech--current");
                speechDom.innerHTML = pauseSVG;
            }
            else {
                if (speechSynthesis.speaking) {
                    if (speechSynthesis.paused) {
                        speechSynthesis.resume();
                        speechDom.innerHTML = pauseSVG;
                    }
                    else {
                        speechSynthesis.pause();
                        speechDom.innerHTML = playSVG;
                    }
                }
            }
            (0,selection/* setSelectionFocus */.jl)(window.vditorSpeechRange);
            element.focus();
            return;
        }
        speechDom.style.display = "none";
        speechSynthesis.cancel();
        speechDom.classList.remove("vditor-speech--current");
        speechDom.innerHTML = playSVG;
        if (getSelection().rangeCount === 0) {
            return;
        }
        var range = getSelection().getRangeAt(0);
        var text = range.toString().trim();
        if (!text) {
            return;
        }
        window.vditorSpeechRange = range.cloneRange();
        var rect = range.getBoundingClientRect();
        speechDom.innerHTML = playSVG;
        speechDom.style.display = "block";
        speechDom.style.top = (rect.top + rect.height + document.querySelector("html").scrollTop - 20) + "px";
        if (window.ontouchstart !== undefined) {
            speechDom.style.left = (event.changedTouches[event.changedTouches.length - 1].pageX + 2) + "px";
        }
        else {
            speechDom.style.left = (event.clientX + 2) + "px";
        }
        speechDom.setAttribute("data-text", text);
    });
};

;// ./src/ts/markdown/previewRender.ts
var __awaiter = (undefined && undefined.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
var __generator = (undefined && undefined.__generator) || function (thisArg, body) {
    var _ = { label: 0, sent: function() { if (t[0] & 1) throw t[1]; return t[1]; }, trys: [], ops: [] }, f, y, t, g;
    return g = { next: verb(0), "throw": verb(1), "return": verb(2) }, typeof Symbol === "function" && (g[Symbol.iterator] = function() { return this; }), g;
    function verb(n) { return function (v) { return step([n, v]); }; }
    function step(op) {
        if (f) throw new TypeError("Generator is already executing.");
        while (g && (g = 0, op[0] && (_ = 0)), _) try {
            if (f = 1, y && (t = op[0] & 2 ? y["return"] : op[0] ? y["throw"] || ((t = y["return"]) && t.call(y), 0) : y.next) && !(t = t.call(y, op[1])).done) return t;
            if (y = 0, t) op = [op[0] & 2, t.value];
            switch (op[0]) {
                case 0: case 1: t = op; break;
                case 4: _.label++; return { value: op[1], done: false };
                case 5: _.label++; y = op[1]; op = [0]; continue;
                case 7: op = _.ops.pop(); _.trys.pop(); continue;
                default:
                    if (!(t = _.trys, t = t.length > 0 && t[t.length - 1]) && (op[0] === 6 || op[0] === 2)) { _ = 0; continue; }
                    if (op[0] === 3 && (!t || (op[1] > t[0] && op[1] < t[3]))) { _.label = op[1]; break; }
                    if (op[0] === 6 && _.label < t[1]) { _.label = t[1]; t = op; break; }
                    if (t && _.label < t[2]) { _.label = t[2]; _.ops.push(op); break; }
                    if (t[2]) _.ops.pop();
                    _.trys.pop(); continue;
            }
            op = body.call(thisArg, _);
        } catch (e) { op = [6, e]; y = 0; } finally { f = t = 0; }
        if (op[0] & 5) throw op[1]; return { value: op[0] ? op[1] : void 0, done: true };
    }
};

























var mergeOptions = function (options) {
    var _a;
    var defaultOption = {
        anchor: 0,
        cdn: constants/* Constants */.Y.CDN,
        customEmoji: {},
        emojiPath: "".concat(constants/* Constants */.Y.CDN, "/dist/images/emoji"),
        hljs: constants/* Constants */.Y.HLJS_OPTIONS,
        icon: "ant",
        lang: "zh_CN",
        markdown: constants/* Constants */.Y.MARKDOWN_OPTIONS,
        math: constants/* Constants */.Y.MATH_OPTIONS,
        mode: "light",
        plantuml: constants/* Constants */.Y.PLANTUML_OPTIONS,
        speech: {
            enable: false,
        },
        render: {
            media: {
                enable: true,
            }
        },
        theme: constants/* Constants */.Y.THEME_OPTIONS,
    };
    if (options.cdn) {
        if (!((_a = options.theme) === null || _a === void 0 ? void 0 : _a.path)) {
            defaultOption.theme.path = "".concat(options.cdn, "/dist/css/content-theme");
        }
        if (!options.emojiPath) {
            defaultOption.emojiPath = "".concat(options.cdn, "/dist/images/emoji");
        }
    }
    return (0,merge/* merge */.h)(defaultOption, options);
};
var md2html = function (mdText, options) {
    var mergedOptions = mergeOptions(options);
    return (0,addScript/* addScript */.Z)("".concat(mergedOptions.cdn, "/dist/js/lute/lute.min.js"), "vditorLuteScript").then(function () {
        var lute = (0,setLute/* setLute */.X)({
            autoSpace: mergedOptions.markdown.autoSpace,
            callout: mergedOptions.markdown.callout,
            inlineMath: mergedOptions.markdown.inlineMath,
            gfmAutoLink: mergedOptions.markdown.gfmAutoLink,
            codeBlockPreview: mergedOptions.markdown.codeBlockPreview,
            emojiSite: mergedOptions.emojiPath,
            emojis: mergedOptions.customEmoji,
            fixTermTypo: mergedOptions.markdown.fixTermTypo,
            footnotes: mergedOptions.markdown.footnotes,
            headingAnchor: mergedOptions.anchor !== 0,
            imgPathAllowSpace: mergedOptions.markdown.imgPathAllowSpace,
            inlineMathDigit: mergedOptions.math.inlineDigit,
            lazyLoadImage: mergedOptions.lazyLoadImage,
            linkBase: mergedOptions.markdown.linkBase,
            linkPrefix: mergedOptions.markdown.linkPrefix,
            listStyle: mergedOptions.markdown.listStyle,
            mark: mergedOptions.markdown.mark,
            mathBlockPreview: mergedOptions.markdown.mathBlockPreview,
            paragraphBeginningSpace: mergedOptions.markdown.paragraphBeginningSpace,
            sanitize: mergedOptions.markdown.sanitize,
            sub: mergedOptions.markdown.sub,
            sup: mergedOptions.markdown.sup,
            toc: mergedOptions.markdown.toc,
        });
        if (options === null || options === void 0 ? void 0 : options.renderers) {
            lute.SetJSRenderers({
                renderers: {
                    Md2HTML: options.renderers,
                },
            });
        }
        lute.SetHeadingID(true);
        return (0,imageCaptionRender/* renderImageCaptionHTML */.T)(lute.Md2HTML(mdText), mergedOptions.markdown.imageCaption);
    });
};
var previewRender = function (previewElement, markdown, options) { return __awaiter(void 0, void 0, void 0, function () {
    var mergedOptions, html, i18nScriptPrefix, i18nScriptID_1;
    return __generator(this, function (_a) {
        switch (_a.label) {
            case 0:
                mergedOptions = mergeOptions(options);
                return [4 /*yield*/, md2html(markdown, mergedOptions)];
            case 1:
                html = _a.sent();
                if (mergedOptions.transform) {
                    html = mergedOptions.transform(html);
                }
                previewElement.innerHTML = html;
                previewElement.classList.add("vditor-reset");
                (0,tableWheel/* bindTableWheel */.d)(previewElement);
                if (!!mergedOptions.i18n) return [3 /*break*/, 5];
                if (!!["de_DE", "en_US", "es_ES", "fr_FR", "ja_JP", "ko_KR", "pt_BR", "ru_RU", "sv_SE", "vi_VN", "zh_CN", "zh_TW"].includes(mergedOptions.lang)) return [3 /*break*/, 2];
                throw new Error("options.lang error, see https://ld246.com/article/1549638745630#options");
            case 2:
                i18nScriptPrefix = "vditorI18nScript";
                i18nScriptID_1 = i18nScriptPrefix + mergedOptions.lang;
                document.querySelectorAll("head script[id^=\"".concat(i18nScriptPrefix, "\"]")).forEach(function (el) {
                    if (el.id !== i18nScriptID_1) {
                        document.head.removeChild(el);
                    }
                });
                return [4 /*yield*/, (0,addScript/* addScript */.Z)("".concat(mergedOptions.cdn, "/dist/js/i18n/").concat(mergedOptions.lang, ".js"), i18nScriptID_1)];
            case 3:
                _a.sent();
                _a.label = 4;
            case 4: return [3 /*break*/, 6];
            case 5:
                window.VditorI18n = mergedOptions.i18n;
                _a.label = 6;
            case 6:
                if (!mergedOptions.icon) return [3 /*break*/, 8];
                return [4 /*yield*/, (0,addScript/* addScript */.Z)("".concat(mergedOptions.cdn, "/dist/js/icons/").concat(mergedOptions.icon, ".js"), "vditorIconScript")];
            case 7:
                _a.sent();
                _a.label = 8;
            case 8:
                (0,setContentTheme/* setContentTheme */.H)(mergedOptions.theme.current, mergedOptions.theme.path);
                if (mergedOptions.anchor === 1) {
                    previewElement.classList.add("vditor-reset--anchor");
                }
                (0,codeRender/* codeRender */.o)(previewElement, mergedOptions.hljs);
                (0,highlightRender/* highlightRender */.$)(mergedOptions.hljs, previewElement, mergedOptions.cdn);
                (0,mathRender/* mathRender */.T)(previewElement, {
                    cdn: mergedOptions.cdn,
                    math: mergedOptions.math,
                });
                (0,mermaidRender/* mermaidRender */.e)(previewElement, mergedOptions.cdn, mergedOptions.mode);
                (0,SMILESRender/* SMILESRender */.Y)(previewElement, mergedOptions.cdn, mergedOptions.mode);
                (0,markmapRender/* markmapRender */.K)(previewElement, mergedOptions.cdn);
                (0,flowchartRender/* flowchartRender */.D)(previewElement, mergedOptions.cdn);
                (0,graphvizRender/* graphvizRender */.m)(previewElement, mergedOptions.cdn);
                (0,wavedromRender/* wavedromRender */.I)(previewElement, mergedOptions.cdn);
                (0,chartRender/* chartRender */.v)(previewElement, mergedOptions.cdn, mergedOptions.mode);
                (0,mindmapRender/* mindmapRender */.l)(previewElement, mergedOptions.cdn, mergedOptions.mode);
                (0,plantumlRender/* plantumlRender */.M)(previewElement, mergedOptions.cdn, mergedOptions.plantuml);
                (0,abcRender/* abcRender */.$)(previewElement, mergedOptions.cdn);
                if (mergedOptions.render.media.enable) {
                    (0,mediaRender/* mediaRender */.l)(previewElement);
                }
                if (mergedOptions.speech.enable) {
                    speechRender(previewElement);
                }
                if (mergedOptions.anchor !== 0) {
                    anchorRender(mergedOptions.anchor);
                }
                if (mergedOptions.after) {
                    mergedOptions.after();
                }
                if (mergedOptions.lazyLoadImage) {
                    lazyLoadImageRender(previewElement);
                }
                previewElement.addEventListener("click", function (event) {
                    var spanElement = (0,hasClosest/* hasClosestByMatchTag */._Y)(event.target, "SPAN");
                    if (spanElement && (0,hasClosest/* hasClosestByClassName */.KJ)(spanElement, "vditor-toc")) {
                        var headingElement = previewElement.querySelector("#" + spanElement.getAttribute("data-target-id"));
                        if (headingElement) {
                            window.scrollTo(window.scrollX, headingElement.offsetTop);
                        }
                        return;
                    }
                });
                return [2 /*return*/];
        }
    });
}); };

// EXTERNAL MODULE: ./src/ts/preview/image.ts
var preview_image = __webpack_require__(841);
// EXTERNAL MODULE: ./src/ts/ui/setCodeTheme.ts
var setCodeTheme = __webpack_require__(814);
;// ./src/method.ts






















var Vditor = /** @class */ (function () {
    function Vditor() {
    }
    /** 点击图片放大 */
    Vditor.adapterRender = adapterRender;
    /** 点击图片放大 */
    Vditor.previewImage = preview_image/* previewImage */.o;
    /** 为 element 中的代码块添加复制按钮 */
    Vditor.codeRender = codeRender/* codeRender */.o;
    /** 对 graphviz 进行渲染 */
    Vditor.graphvizRender = graphvizRender/* graphvizRender */.m;
    /** 对数字波形图进行渲染 */
    Vditor.wavedromRender = wavedromRender/* wavedromRender */.I;
    /** 为 element 中的代码块进行高亮渲染 */
    Vditor.highlightRender = highlightRender/* highlightRender */.$;
    /** 对数学公式进行渲染 */
    Vditor.mathRender = mathRender/* mathRender */.T;
    /** 流程图/时序图/甘特图渲染 */
    Vditor.mermaidRender = mermaidRender/* mermaidRender */.e;
    /** 化学物质结构渲染 */
    Vditor.SMILESRender = SMILESRender/* SMILESRender */.Y;
    /** 支持 markdown 的思维导图 */
    Vditor.markmapRender = markmapRender/* markmapRender */.K;
    /** flowchart.js 渲染 */
    Vditor.flowchartRender = flowchartRender/* flowchartRender */.D;
    /** 图表渲染 */
    Vditor.chartRender = chartRender/* chartRender */.v;
    /** 五线谱渲染 */
    Vditor.abcRender = abcRender/* abcRender */.$;
    /** 脑图渲染 */
    Vditor.mindmapRender = mindmapRender/* mindmapRender */.l;
    /** plantuml渲染 */
    Vditor.plantumlRender = plantumlRender/* plantumlRender */.M;
    /** 大纲渲染 */
    Vditor.outlineRender = outlineRender/* outlineRender */.N;
    /** 为[特定链接](https://github.com/Vanessa219/vditor/issues/7)分别渲染为视频、音频、嵌入的 iframe */
    Vditor.mediaRender = mediaRender/* mediaRender */.l;
    /** 对选中的文字进行阅读 */
    Vditor.speechRender = speechRender;
    /** 对图片进行懒加载 */
    Vditor.lazyLoadImageRender = lazyLoadImageRender;
    /** Markdown 文本转换为 HTML，该方法需使用[异步编程](https://ld246.com/article/1546828434083?r=Vaness) */
    Vditor.md2html = md2html;
    /** 页面 Markdown 文章渲染 */
    Vditor.preview = previewRender;
    /** 设置代码主题 */
    Vditor.setCodeTheme = setCodeTheme/* setCodeTheme */.h;
    /** 设置内容主题 */
    Vditor.setContentTheme = setContentTheme/* setContentTheme */.H;
    return Vditor;
}());
/* harmony default export */ const method = (Vditor);

export { method as default };
