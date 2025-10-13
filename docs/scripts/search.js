// 搜索管理器
class SearchManager {
    constructor() {
        this.searchIndex = [];
        this.isInitialized = false;
        this.searchModal = null;
        this.searchInput = null;
        this.searchResults = null;
        this.isSearchOpen = false;
    }
    
    async init() {
        this.setupSearchElements();
        this.setupSearchEvents();
        await this.buildSearchIndex();
        this.isInitialized = true;
    }
    
    setupSearchElements() {
        this.searchModal = document.getElementById('search-modal');
        this.searchInput = document.getElementById('search-input');
        this.searchResults = document.getElementById('search-results');
        
        // 如果没有搜索模态框，创建一个
        if (!this.searchModal) {
            this.createSearchModal();
        }
    }
    
    createSearchModal() {
        const modalHtml = `
            <div id="search-modal" class="modal">
                <div class="modal-content">
                    <div class="modal-header">
                        <h3>搜索文档</h3>
                        <button class="modal-close">&times;</button>
                    </div>
                    <div class="modal-body">
                        <div class="search-input-container">
                            <i class="fas fa-search search-icon"></i>
                            <input type="text" id="modal-search-input" 
                                   placeholder="输入关键词搜索..." 
                                   class="search-input" 
                                   autocomplete="off">
                            <div class="search-shortcut">ESC</div>
                        </div>
                        <div id="search-results" class="search-results"></div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        this.searchModal = document.getElementById('search-modal');
        this.searchResults = document.getElementById('search-results');
    }
    
    setupSearchEvents() {
        // 侧边栏搜索输入框
        if (this.searchInput) {
            this.searchInput.addEventListener('input', (e) => {
                this.handleSearch(e.target.value);
            });
            
            this.searchInput.addEventListener('keydown', (e) => {
                this.handleSearchKeydown(e);
            });
        }
        
        // 模态框搜索输入框
        const modalSearchInput = document.getElementById('modal-search-input');
        if (modalSearchInput) {
            modalSearchInput.addEventListener('input', (e) => {
                this.handleSearch(e.target.value);
            });
            
            modalSearchInput.addEventListener('keydown', (e) => {
                this.handleSearchKeydown(e);
            });
        }
        
        // 模态框关闭按钮
        const modalClose = this.searchModal?.querySelector('.modal-close');
        if (modalClose) {
            modalClose.addEventListener('click', () => {
                this.closeSearch();
            });
        }
        
        // 点击模态框外部关闭
        if (this.searchModal) {
            this.searchModal.addEventListener('click', (e) => {
                if (e.target === this.searchModal) {
                    this.closeSearch();
                }
            });
        }
        
        // 全局键盘快捷键
        document.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                this.openSearch();
            } else if (e.key === 'Escape' && this.isSearchOpen) {
                this.closeSearch();
            }
        });
    }
    
    async buildSearchIndex() {
        // 构建搜索索引
        this.searchIndex = [
            {
                title: '项目介绍',
                content: 'SuperRPG项目是一个基于Python的RPG游戏系统，采用现代化的分层架构设计，遵循领域驱动设计(DDD)、命令查询职责分离(CQRS)和事件驱动架构(EDA)原则。',
                url: '#overview',
                category: '架构概览',
                keywords: ['SuperRPG', 'RPG', '游戏系统', 'DDD', 'CQRS', 'EDA', '架构']
            },
            {
                title: '架构设计',
                content: 'SuperRPG采用分层架构设计，包括表示层、应用层、领域层、适配器层和基础设施层。每个层次都有明确的职责分工，确保系统的可维护性和可扩展性。',
                url: '#architecture',
                category: '架构概览',
                keywords: ['分层架构', 'DDD', '领域驱动设计', '架构模式', '系统设计']
            },
            {
                title: '设计原则',
                content: 'SuperRPG项目严格遵循SOLID设计原则：单一职责原则(SRP)、开放/封闭原则(OCP)、里氏替换原则(LSP)、接口隔离原则(ISP)、依赖倒置原则(DIP)。',
                url: '#principles',
                category: '架构概览',
                keywords: ['SOLID', 'SRP', 'OCP', 'LSP', 'ISP', 'DIP', '设计原则', '面向对象']
            },
            {
                title: '领域层',
                content: '领域层是整个架构的核心，包含了业务逻辑、领域模型和领域服务。包括角色模型、战斗模型、世界模型、关系模型、目标模型等核心实体。',
                url: '#domain-layer',
                category: '分层架构',
                keywords: ['领域层', '领域模型', '业务逻辑', '实体', '值对象', '聚合根', '领域服务']
            },
            {
                title: '应用层',
                content: '应用层负责协调领域层和基础设施层，处理应用程序的业务流程。包括游戏引擎、回合管理器、消息处理器、代理服务等核心服务。',
                url: '#application-layer',
                category: '分层架构',
                keywords: ['应用层', '业务流程', '应用服务', '游戏引擎', '回合管理', '消息处理']
            },
            {
                title: '基础设施层',
                content: '基础设施层提供技术支持，包括事件总线、日志系统、配置管理、仓储实现等。为上层提供稳定的技术基础。',
                url: '#infrastructure-layer',
                category: '分层架构',
                keywords: ['基础设施层', '事件总线', '日志系统', '配置管理', '仓储模式', '技术支持']
            },
            {
                title: '适配器层',
                content: '适配器层负责与外部系统的集成，包括代理适配器、工具适配器、世界适配器等。实现新旧架构的平滑过渡。',
                url: '#adapters-layer',
                category: '分层架构',
                keywords: ['适配器层', '系统集成', '外部适配器', '代理适配器', '工具适配器', '世界适配器']
            },
            {
                title: '游戏引擎',
                content: '游戏引擎服务负责游戏的核心逻辑协调，包括游戏流程控制、状态管理和事件处理。是整个系统的核心协调器。',
                url: '#game-engine',
                category: '核心服务',
                keywords: ['游戏引擎', '核心逻辑', '流程控制', '状态管理', '事件处理', '游戏协调']
            },
            {
                title: '回合管理器',
                content: '回合管理器负责游戏回合的管理，包括回合流程控制、角色行动顺序维护和状态跟踪。确保游戏回合的有序进行。',
                url: '#turn-manager',
                category: '核心服务',
                keywords: ['回合管理', '流程控制', '行动顺序', '状态跟踪', '游戏回合', '超时处理']
            },
            {
                title: '消息处理器',
                content: '消息处理器负责处理游戏中的消息和工具调用，包括消息解析、工具调用识别和执行。支持复杂的消息处理逻辑。',
                url: '#message-handler',
                category: '核心服务',
                keywords: ['消息处理', '工具调用', '消息解析', '工具执行', '消息路由', '错误处理']
            },
            {
                title: '代理服务',
                content: '代理服务负责游戏中的代理(AI角色)管理，包括代理创建、状态管理和交互协调。支持多种类型的AI代理。',
                url: '#agent-service',
                category: '核心服务',
                keywords: ['代理服务', 'AI角色', '代理管理', '状态管理', '交互协调', '智能体']
            },
            {
                title: '命令接口',
                content: '命令接口定义了系统状态修改的操作，包括角色管理命令、世界管理命令、战斗管理命令等。遵循CQRS模式。',
                url: '#commands',
                category: 'API文档',
                keywords: ['命令接口', 'CQRS', '状态修改', '角色管理', '世界管理', '战斗管理']
            },
            {
                title: '查询接口',
                content: '查询接口定义了系统状态查询的操作，包括角色查询、世界查询、战斗查询等。提供只读的数据访问接口。',
                url: '#queries',
                category: 'API文档',
                keywords: ['查询接口', 'CQRS', '状态查询', '角色查询', '世界查询', '数据访问']
            },
            {
                title: '事件系统',
                content: '事件系统实现了组件间的松耦合通信，包括领域事件、应用事件、集成事件等。支持事件发布订阅模式。',
                url: '#events',
                category: 'API文档',
                keywords: ['事件系统', '事件驱动', '发布订阅', '领域事件', '应用事件', '松耦合']
            },
            {
                title: '角色管理示例',
                content: '角色管理示例展示了如何创建、修改和查询角色信息，包括角色属性设置、能力值计算、状态管理等。',
                url: '#character-example',
                category: '示例代码',
                keywords: ['角色管理', '示例代码', '角色创建', '属性设置', '能力值', '状态管理']
            },
            {
                title: '世界状态示例',
                content: '世界状态示例展示了如何管理游戏世界状态，包括世界创建、场景设置、时间推进、关系管理等。',
                url: '#world-example',
                category: '示例代码',
                keywords: ['世界状态', '示例代码', '世界创建', '场景设置', '时间推进', '关系管理']
            },
            {
                title: '战斗系统示例',
                content: '战斗系统示例展示了如何实现战斗逻辑，包括攻击计算、伤害处理、状态效果、战斗流程等。',
                url: '#combat-example',
                category: '示例代码',
                keywords: ['战斗系统', '示例代码', '攻击计算', '伤害处理', '状态效果', '战斗流程']
            },
            {
                title: '事件处理示例',
                content: '事件处理示例展示了如何使用事件系统，包括事件发布、事件订阅、事件处理、事件溯源等。',
                url: '#event-example',
                category: '示例代码',
                keywords: ['事件处理', '示例代码', '事件发布', '事件订阅', '事件处理', '事件溯源']
            }
        ];
    }
    
    handleSearch(query) {
        if (!query || query.trim().length < 2) {
            this.clearResults();
            return;
        }
        
        const results = this.search(query.trim());
        this.displayResults(results, query);
    }
    
    search(query) {
        const normalizedQuery = query.toLowerCase();
        const results = [];
        
        for (const item of this.searchIndex) {
            const score = this.calculateScore(item, normalizedQuery);
            if (score > 0) {
                results.push({
                    ...item,
                    score: score
                });
            }
        }
        
        // 按分数排序
        results.sort((a, b) => b.score - a.score);
        
        return results.slice(0, 10); // 限制结果数量
    }
    
    calculateScore(item, query) {
        let score = 0;
        
        // 标题匹配权重最高
        if (item.title.toLowerCase().includes(query)) {
            score += 100;
            if (item.title.toLowerCase() === query) {
                score += 50; // 完全匹配额外加分
            }
        }
        
        // 关键词匹配
        for (const keyword of item.keywords) {
            if (keyword.toLowerCase().includes(query)) {
                score += 50;
                if (keyword.toLowerCase() === query) {
                    score += 25; // 完全匹配额外加分
                }
            }
        }
        
        // 内容匹配
        if (item.content.toLowerCase().includes(query)) {
            score += 20;
        }
        
        // 分类匹配
        if (item.category.toLowerCase().includes(query)) {
            score += 10;
        }
        
        return score;
    }
    
    displayResults(results, query) {
        if (!this.searchResults) return;
        
        if (results.length === 0) {
            this.searchResults.innerHTML = `
                <div class="search-no-results">
                    <i class="fas fa-search"></i>
                    <p>未找到与 "<strong>${this.escapeHtml(query)}</strong>" 相关的内容</p>
                    <div class="search-suggestions">
                        <p>建议：</p>
                        <ul>
                            <li>检查拼写是否正确</li>
                            <li>尝试使用更通用的关键词</li>
                            <li>使用不同的搜索词</li>
                        </ul>
                    </div>
                </div>
            `;
            return;
        }
        
        const resultsHtml = results.map(result => {
            const highlightedTitle = this.highlightText(result.title, query);
            const highlightedContent = this.highlightText(
                this.extractSnippet(result.content, query), 
                query
            );
            
            return `
                <div class="search-result-item" data-url="${result.url}">
                    <div class="search-result-title">${highlightedTitle}</div>
                    <div class="search-result-category">${result.category}</div>
                    <div class="search-result-content">${highlightedContent}</div>
                </div>
            `;
        }).join('');
        
        this.searchResults.innerHTML = `
            <div class="search-results-header">
                <span class="search-results-count">${results.length} 个结果</span>
                <span class="search-query">"${this.escapeHtml(query)}"</span>
            </div>
            <div class="search-results-list">
                ${resultsHtml}
            </div>
        `;
        
        // 添加点击事件
        this.searchResults.querySelectorAll('.search-result-item').forEach(item => {
            item.addEventListener('click', () => {
                const url = item.getAttribute('data-url');
                if (url) {
                    this.navigateToResult(url);
                }
            });
        });
    }
    
    highlightText(text, query) {
        if (!text || !query) return this.escapeHtml(text);
        
        const escapedText = this.escapeHtml(text);
        const escapedQuery = this.escapeHtml(query);
        const regex = new RegExp(`(${escapedQuery})`, 'gi');
        
        return escapedText.replace(regex, '<mark>$1</mark>');
    }
    
    extractSnippet(content, query, maxLength = 150) {
        if (!content || !query) return content;
        
        const lowerContent = content.toLowerCase();
        const lowerQuery = query.toLowerCase();
        const index = lowerContent.indexOf(lowerQuery);
        
        if (index === -1) {
            return content.length > maxLength ? 
                content.substring(0, maxLength) + '...' : content;
        }
        
        const start = Math.max(0, index - 50);
        const end = Math.min(content.length, index + query.length + 100);
        
        let snippet = content.substring(start, end);
        
        if (start > 0) snippet = '...' + snippet;
        if (end < content.length) snippet = snippet + '...';
        
        return snippet;
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    clearResults() {
        if (this.searchResults) {
            this.searchResults.innerHTML = '';
        }
    }
    
    openSearch() {
        if (!this.searchModal) return;
        
        this.isSearchOpen = true;
        this.searchModal.classList.add('show');
        
        // 聚焦搜索输入框
        const modalSearchInput = document.getElementById('modal-search-input');
        if (modalSearchInput) {
            setTimeout(() => {
                modalSearchInput.focus();
                modalSearchInput.select();
            }, 100);
        }
    }
    
    closeSearch() {
        if (!this.searchModal) return;
        
        this.isSearchOpen = false;
        this.searchModal.classList.remove('show');
        this.clearResults();
        
        // 清空搜索输入框
        const modalSearchInput = document.getElementById('modal-search-input');
        if (modalSearchInput) {
            modalSearchInput.value = '';
        }
        
        if (this.searchInput) {
            this.searchInput.value = '';
        }
    }
    
    navigateToResult(url) {
        this.closeSearch();
        
        // 解析URL并导航到对应页面
        if (url.startsWith('#')) {
            const pageName = url.substring(1);
            if (window.superRPGDocs) {
                window.superRPGDocs.loadPage(pageName);
            }
        } else {
            window.location.href = url;
        }
    }
    
    handleSearchKeydown(e) {
        const results = this.searchResults?.querySelectorAll('.search-result-item');
        if (!results || results.length === 0) return;
        
        let currentIndex = -1;
        const currentSelected = this.searchResults.querySelector('.search-result-item.selected');
        if (currentSelected) {
            currentIndex = Array.from(results).indexOf(currentSelected);
        }
        
        switch (e.key) {
            case 'ArrowDown':
                e.preventDefault();
                currentIndex = Math.min(currentIndex + 1, results.length - 1);
                this.selectResult(results, currentIndex);
                break;
                
            case 'ArrowUp':
                e.preventDefault();
                currentIndex = Math.max(currentIndex - 1, 0);
                this.selectResult(results, currentIndex);
                break;
                
            case 'Enter':
                e.preventDefault();
                if (currentIndex >= 0 && results[currentIndex]) {
                    const url = results[currentIndex].getAttribute('data-url');
                    if (url) {
                        this.navigateToResult(url);
                    }
                }
                break;
        }
    }
    
    selectResult(results, index) {
        // 移除所有选中状态
        results.forEach(result => result.classList.remove('selected'));
        
        // 添加选中状态
        if (index >= 0 && results[index]) {
            results[index].classList.add('selected');
            results[index].scrollIntoView({ block: 'nearest' });
        }
    }
}

// 全局搜索管理器实例
window.searchManager = new SearchManager();