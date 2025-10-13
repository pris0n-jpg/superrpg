// 代码高亮管理器
class HighlightManager {
    constructor() {
        this.isInitialized = false;
        this.highlightedElements = new Set();
    }
    
    init() {
        this.setupCodeBlocks();
        this.isInitialized = true;
    }
    
    setupCodeBlocks() {
        // 为所有代码块添加高亮
        this.highlightAll();
        
        // 监听内容变化，重新高亮
        this.observeContentChanges();
    }
    
    highlightAll() {
        const codeBlocks = document.querySelectorAll('pre code');
        
        codeBlocks.forEach((block) => {
            if (!this.highlightedElements.has(block)) {
                this.highlightBlock(block);
                this.highlightedElements.add(block);
            }
        });
    }
    
    highlightBlock(block) {
        const language = this.detectLanguage(block);
        const code = block.textContent;
        
        // 应用语法高亮
        const highlightedCode = this.applySyntaxHighlight(code, language);
        block.innerHTML = highlightedCode;
        
        // 添加语言标识
        this.addLanguageIndicator(block, language);
        
        // 添加复制按钮
        this.addCopyButton(block);
        
        // 添加行号（如果需要）
        this.addLineNumbers(block);
        
        // 添加工具栏
        this.addToolbar(block);
    }
    
    detectLanguage(block) {
        // 从类名检测语言
        const classList = Array.from(block.classList);
        
        for (const className of classList) {
            if (className.startsWith('language-')) {
                return className.substring(9);
            }
        }
        
        // 从父元素检测
        const pre = block.parentElement;
        if (pre && pre.className) {
            const preClasses = pre.className.split(' ');
            for (const className of preClasses) {
                if (className.startsWith('language-')) {
                    return className.substring(9);
                }
            }
        }
        
        // 根据内容推断语言
        return this.inferLanguage(block.textContent);
    }
    
    inferLanguage(code) {
        // 简单的语言推断逻辑
        const trimmedCode = code.trim();
        
        // Python
        if (/^(import |from |def |class |#|"""|'''|\t|    )/m.test(trimmedCode)) {
            return 'python';
        }
        
        // JavaScript
        if (/^(const |let |var |function |class |=>|\/\/|\/\*|\*\/|import |export )/m.test(trimmedCode)) {
            return 'javascript';
        }
        
        // JSON
        if (/^\s*\{[\s\S]*\}\s*$/.test(trimmedCode) || /^\s*\[[\s\S]*\]\s*$/.test(trimmedCode)) {
            try {
                JSON.parse(trimmedCode);
                return 'json';
            } catch (e) {
                // 不是有效的JSON
            }
        }
        
        // HTML
        if (/^<[^>]+>/.test(trimmedCode) || /<\/[^>]+>$/.test(trimmedCode)) {
            return 'html';
        }
        
        // CSS
        if (/^[.#]?[\w-]+\s*\{[\s\S]*\}/m.test(trimmedCode) || /@import|@media|@font-face/.test(trimmedCode)) {
            return 'css';
        }
        
        // SQL
        if (/^(SELECT|INSERT|UPDATE|DELETE|CREATE|DROP|ALTER|WITH)\s/i.test(trimmedCode)) {
            return 'sql';
        }
        
        // Shell/Bash
        if (/^(#!\/bin\/bash|#!\/bin\/sh|export |alias |function |\$\(|\$\{)/m.test(trimmedCode)) {
            return 'bash';
        }
        
        // YAML
        if (/^[a-zA-Z_][a-zA-Z0-9_]*:\s/m.test(trimmedCode) && /^[ \t]*-[ ]/m.test(trimmedCode)) {
            return 'yaml';
        }
        
        return 'text';
    }
    
    applySyntaxHighlight(code, language) {
        // 简单的语法高亮实现
        let highlightedCode = this.escapeHtml(code);
        
        switch (language) {
            case 'python':
                highlightedCode = this.highlightPython(highlightedCode);
                break;
            case 'javascript':
                highlightedCode = this.highlightJavaScript(highlightedCode);
                break;
            case 'json':
                highlightedCode = this.highlightJson(highlightedCode);
                break;
            case 'html':
                highlightedCode = this.highlightHtml(highlightedCode);
                break;
            case 'css':
                highlightedCode = this.highlightCss(highlightedCode);
                break;
            case 'sql':
                highlightedCode = this.highlightSql(highlightedCode);
                break;
            case 'bash':
                highlightedCode = this.highlightBash(highlightedCode);
                break;
            case 'yaml':
                highlightedCode = this.highlightYaml(highlightedCode);
                break;
            default:
                // 通用高亮
                highlightedCode = this.highlightGeneric(highlightedCode);
        }
        
        return highlightedCode;
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    highlightPython(code) {
        const keywords = [
            'and', 'as', 'assert', 'break', 'class', 'continue', 'def', 'del',
            'elif', 'else', 'except', 'finally', 'for', 'from', 'global',
            'if', 'import', 'in', 'is', 'lambda', 'nonlocal', 'not', 'or',
            'pass', 'raise', 'return', 'try', 'while', 'with', 'yield',
            'True', 'False', 'None', 'async', 'await'
        ];
        
        const builtins = [
            'abs', 'all', 'any', 'bin', 'bool', 'bytearray', 'bytes',
            'callable', 'chr', 'classmethod', 'compile', 'complex',
            'delattr', 'dict', 'dir', 'divmod', 'enumerate', 'eval',
            'exec', 'filter', 'float', 'format', 'frozenset', 'getattr',
            'globals', 'hasattr', 'hash', 'help', 'hex', 'id', 'input',
            'int', 'isinstance', 'issubclass', 'iter', 'len', 'list',
            'locals', 'map', 'max', 'memoryview', 'min', 'next',
            'object', 'oct', 'open', 'ord', 'pow', 'print', 'property',
            'range', 'repr', 'reversed', 'round', 'set', 'setattr',
            'slice', 'sorted', 'staticmethod', 'str', 'sum', 'super',
            'tuple', 'type', 'vars', 'zip'
        ];
        
        // 高亮关键字
        code = this.highlightKeywords(code, keywords, 'keyword');
        
        // 高亮内置函数
        code = this.highlightKeywords(code, builtins, 'builtin');
        
        // 高亮字符串
        code = this.highlightStrings(code, ['"""', "'''", '"', "'"]);
        
        // 高亮注释
        code = this.highlightComments(code, '#');
        
        // 高亮数字
        code = this.highlightNumbers(code);
        
        // 高亮函数定义
        code = code.replace(/\b(def|class)\s+([a-zA-Z_][a-zA-Z0-9_]*)/g, 
            '<span class="keyword">$1</span> <span class="function">$2</span>');
        
        return code;
    }
    
    highlightJavaScript(code) {
        const keywords = [
            'break', 'case', 'catch', 'class', 'const', 'continue', 'debugger',
            'default', 'delete', 'do', 'else', 'export', 'extends', 'finally',
            'for', 'function', 'if', 'import', 'in', 'instanceof', 'let',
            'new', 'return', 'super', 'switch', 'this', 'throw', 'try',
            'typeof', 'var', 'void', 'while', 'with', 'yield', 'async', 'await'
        ];
        
        const builtins = [
            'Array', 'Boolean', 'Date', 'Error', 'Function', 'JSON', 'Math',
            'Number', 'Object', 'RegExp', 'String', 'console', 'document',
            'window', 'setTimeout', 'setInterval', 'clearTimeout', 'clearInterval'
        ];
        
        // 高亮关键字
        code = this.highlightKeywords(code, keywords, 'keyword');
        
        // 高亮内置对象
        code = this.highlightKeywords(code, builtins, 'builtin');
        
        // 高亮字符串
        code = this.highlightStrings(code, ['"', "'", '`']);
        
        // 高亮注释
        code = this.highlightComments(code, '//');
        code = this.highlightBlockComments(code, '/*', '*/');
        
        // 高亮数字
        code = this.highlightNumbers(code);
        
        // 高亮正则表达式
        code = code.replace(/\/([^\/\n\\]+(?:\\.[^\/\n\\]*)*)\/[gimuy]*/g, '<span class="regex">/$1/</span>');
        
        return code;
    }
    
    highlightJson(code) {
        // 高亮字符串
        code = code.replace(/"([^"\\]*(\\.[^"\\]*)*)"/g, 
            '<span class="string">"$1"</span>');
        
        // 高亮数字
        code = this.highlightNumbers(code);
        
        // 高亮布尔值和null
        code = code.replace(/\b(true|false|null)\b/g, 
            '<span class="literal">$1</span>');
        
        // 高亮属性名
        code = code.replace(/"([^"\\]*(\\.[^"\\]*)*)":/g, 
            '<span class="property">"$1"</span>:');
        
        return code;
    }
    
    highlightHtml(code) {
        // 高亮标签
        code = code.replace(/(<\/?)([a-zA-Z][a-zA-Z0-9]*)(.*?)(>)/g, 
            '<span class="tag">$1</span><span class="tag-name">$2</span><span class="attribute">$3</span><span class="tag">$4</span>');
        
        // 高亮属性值
        code = code.replace(/([a-zA-Z-]+)(=)(["'])(.*?)\3/g, 
            '<span class="attribute-name">$1</span><span class="operator">$2</span><span class="string">$3$4$3</span>');
        
        // 高亮注释
        code = code.replace(/(<!--.*?-->)/gs, '<span class="comment">$1</span>');
        
        return code;
    }
    
    highlightCss(code) {
        // 高亮选择器
        code = code.replace(/^([.#]?[\w-]+|[{},])\s*/gm, 
            '<span class="selector">$1</span> ');
        
        // 高亮属性名
        code = code.replace(/([a-zA-Z-]+)(:)/g, 
            '<span class="property">$1</span><span class="operator">$2</span>');
        
        // 高亮属性值
        code = code.replace(/(:\s*)([^;{}]+)/g, 
            '$1<span class="value">$2</span>');
        
        // 高亮字符串
        code = code.replace(/(["'])(.*?)\1/g, '<span class="string">$1$2$1</span>');
        
        // 高亮注释
        code = code.replace(/(\/\*.*?\*\/)/gs, '<span class="comment">$1</span>');
        
        // 高亮数字
        code = this.highlightNumbers(code);
        
        return code;
    }
    
    highlightSql(code) {
        const keywords = [
            'SELECT', 'FROM', 'WHERE', 'INSERT', 'UPDATE', 'DELETE', 'CREATE',
            'DROP', 'ALTER', 'TABLE', 'INDEX', 'DATABASE', 'WITH', 'AS', 'JOIN',
            'INNER', 'LEFT', 'RIGHT', 'FULL', 'OUTER', 'ON', 'GROUP', 'BY',
            'HAVING', 'ORDER', 'LIMIT', 'OFFSET', 'UNION', 'ALL', 'DISTINCT',
            'INTO', 'VALUES', 'SET', 'AND', 'OR', 'NOT', 'NULL', 'IS', 'BETWEEN',
            'LIKE', 'IN', 'EXISTS', 'CASE', 'WHEN', 'THEN', 'ELSE', 'END'
        ];
        
        // 高亮关键字
        code = this.highlightKeywords(code, keywords, 'keyword');
        
        // 高亮字符串
        code = this.highlightStrings(code, ['"', "'"]);
        
        // 高亮注释
        code = this.highlightComments(code, '--');
        code = this.highlightBlockComments(code, '/*', '*/');
        
        // 高亮数字
        code = this.highlightNumbers(code);
        
        return code;
    }
    
    highlightBash(code) {
        const keywords = [
            'if', 'then', 'else', 'elif', 'fi', 'for', 'while', 'do', 'done',
            'case', 'esac', 'function', 'return', 'exit', 'export', 'local',
            'readonly', 'declare', 'typeset', 'unset', 'alias', 'unalias',
            'bg', 'fg', 'jobs', 'kill', 'wait', 'cd', 'pwd', 'echo', 'printf',
            'read', 'source', 'exec', 'test', '[', ']', 'true', 'false'
        ];
        
        const builtins = [
            'ls', 'cat', 'grep', 'sed', 'awk', 'sort', 'uniq', 'wc', 'head',
            'tail', 'find', 'xargs', 'tar', 'gzip', 'gunzip', 'cp', 'mv', 'rm',
            'mkdir', 'rmdir', 'chmod', 'chown', 'chgrp', 'ps', 'top', 'kill',
            'killall', 'nohup', 'bg', 'fg', 'jobs', 'export', 'env', 'printenv',
            'set', 'unset'
        ];
        
        // 高亮关键字
        code = this.highlightKeywords(code, keywords, 'keyword');
        
        // 高亮内置命令
        code = this.highlightKeywords(code, builtins, 'builtin');
        
        // 高亮字符串
        code = this.highlightStrings(code, ['"', "'"]);
        
        // 高亮注释
        code = this.highlightComments(code, '#');
        
        // 高亮变量
        code = code.replace(/\$([a-zA-Z_][a-zA-Z0-9_]*)/g, 
            '<span class="variable">$$1</span>');
        code = code.replace(/\$\{([a-zA-Z_][a-zA-Z0-9_]*)\}/g, 
            '<span class="variable">$${$1}</span>');
        
        return code;
    }
    
    highlightYaml(code) {
        // 高亮键
        code = code.replace(/^([ \t]*[a-zA-Z_][a-zA-Z0-9_-]*)(:)/gm, 
            '<span class="property">$1</span><span class="operator">$2</span>');
        
        // 高亮字符串
        code = code.replace(/(["'])(.*?)\1/g, '<span class="string">$1$2$1</span>');
        
        // 高亮注释
        code = code.replace(/(#.*)$/gm, '<span class="comment">$1</span>');
        
        // 高亮布尔值
        code = code.replace(/\b(true|false|null)\b/g, 
            '<span class="literal">$1</span>');
        
        // 高亮数字
        code = this.highlightNumbers(code);
        
        return code;
    }
    
    highlightGeneric(code) {
        // 通用高亮：字符串、注释、数字
        code = this.highlightStrings(code, ['"', "'"]);
        code = this.highlightComments(code, '//');
        code = this.highlightComments(code, '#');
        code = this.highlightNumbers(code);
        
        return code;
    }
    
    highlightKeywords(code, keywords, className) {
        const regex = new RegExp('\\b(' + keywords.join('|') + ')\\b', 'gi');
        return code.replace(regex, `<span class="${className}">$1</span>`);
    }
    
    highlightStrings(code, delimiters) {
        for (const delimiter of delimiters) {
            const regex = new RegExp(this.escapeRegex(delimiter) + '([^' + this.escapeRegex(delimiter) + '\\\\]*(\\\\.[^' + this.escapeRegex(delimiter) + '\\\\]*)*)' + this.escapeRegex(delimiter), 'g');
            code = code.replace(regex, '<span class="string">' + delimiter + '$1' + delimiter + '</span>');
        }
        return code;
    }
    
    highlightComments(code, delimiter) {
        const regex = new RegExp('(' + this.escapeRegex(delimiter) + '.*$)', 'gm');
        return code.replace(regex, '<span class="comment">$1</span>');
    }
    
    highlightBlockComments(code, startDelimiter, endDelimiter) {
        const regex = new RegExp('(' + this.escapeRegex(startDelimiter) + '[\\s\\S]*?' + this.escapeRegex(endDelimiter) + ')', 'g');
        return code.replace(regex, '<span class="comment">$1</span>');
    }
    
    highlightNumbers(code) {
        return code.replace(/\b(\d+\.?\d*|\.\d+)\b/g, '<span class="number">$1</span>');
    }
    
    escapeRegex(string) {
        return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }
    
    addLanguageIndicator(block, language) {
        const pre = block.parentElement;
        if (!pre) return;
        
        // 移除现有的语言指示器
        const existingIndicator = pre.querySelector('.code-language');
        if (existingIndicator) {
            existingIndicator.remove();
        }
        
        const indicator = document.createElement('div');
        indicator.className = 'code-language';
        indicator.textContent = language.toUpperCase();
        
        pre.insertBefore(indicator, block);
    }
    
    addCopyButton(block) {
        const pre = block.parentElement;
        if (!pre) return;
        
        // 移除现有的复制按钮
        const existingButton = pre.querySelector('.code-copy-btn');
        if (existingButton) {
            existingButton.remove();
        }
        
        const button = document.createElement('button');
        button.className = 'code-copy-btn';
        button.innerHTML = '<i class="fas fa-copy"></i>';
        button.title = '复制代码';
        
        button.addEventListener('click', () => {
            this.copyToClipboard(block.textContent);
            this.showCopyFeedback(button);
        });
        
        pre.appendChild(button);
    }
    
    addLineNumbers(block) {
        const pre = block.parentElement;
        if (!pre) return;
        
        // 检查是否已经有行号
        if (pre.classList.contains('line-numbers')) {
            return;
        }
        
        const lines = block.textContent.split('\n');
        if (lines.length <= 1) return;
        
        pre.classList.add('line-numbers');
        
        const lineNumbersContainer = document.createElement('div');
        lineNumbersContainer.className = 'line-numbers-rows';
        
        for (let i = 1; i <= lines.length; i++) {
            const lineNumber = document.createElement('span');
            lineNumber.textContent = i;
            lineNumbersContainer.appendChild(lineNumber);
        }
        
        pre.appendChild(lineNumbersContainer);
    }
    
    addToolbar(block) {
        const pre = block.parentElement;
        if (!pre) return;
        
        // 移除现有的工具栏
        const existingToolbar = pre.querySelector('.code-toolbar');
        if (existingToolbar) {
            existingToolbar.remove();
        }
        
        const toolbar = document.createElement('div');
        toolbar.className = 'code-toolbar';
        
        // 添加复制按钮
        const copyBtn = document.createElement('button');
        copyBtn.className = 'toolbar-btn copy-btn';
        copyBtn.innerHTML = '<i class="fas fa-copy"></i>';
        copyBtn.title = '复制代码';
        
        copyBtn.addEventListener('click', () => {
            this.copyToClipboard(block.textContent);
            this.showCopyFeedback(copyBtn);
        });
        
        toolbar.appendChild(copyBtn);
        
        pre.appendChild(toolbar);
    }
    
    copyToClipboard(text) {
        if (navigator.clipboard) {
            navigator.clipboard.writeText(text).catch(err => {
                console.error('复制失败:', err);
                this.fallbackCopyToClipboard(text);
            });
        } else {
            this.fallbackCopyToClipboard(text);
        }
    }
    
    fallbackCopyToClipboard(text) {
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        textArea.style.top = '-999999px';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        
        try {
            document.execCommand('copy');
        } catch (err) {
            console.error('复制失败:', err);
        }
        
        document.body.removeChild(textArea);
    }
    
    showCopyFeedback(button) {
        const originalHTML = button.innerHTML;
        button.innerHTML = '<i class="fas fa-check"></i>';
        button.classList.add('copied');
        
        setTimeout(() => {
            button.innerHTML = originalHTML;
            button.classList.remove('copied');
        }, 2000);
    }
    
    observeContentChanges() {
        // 监听内容变化，重新高亮
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                mutation.addedNodes.forEach((node) => {
                    if (node.nodeType === Node.ELEMENT_NODE) {
                        const codeBlocks = node.querySelectorAll ? 
                            node.querySelectorAll('pre code') : [];
                        codeBlocks.forEach((block) => {
                            if (!this.highlightedElements.has(block)) {
                                this.highlightBlock(block);
                                this.highlightedElements.add(block);
                            }
                        });
                    }
                });
            });
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }
    
    // 重新高亮所有代码块
    rehighlightAll() {
        this.highlightedElements.clear();
        this.highlightAll();
    }
}

// 全局代码高亮管理器实例
window.highlightManager = new HighlightManager();