// 主要应用逻辑
class SuperRPGDocs {
    constructor() {
        this.currentPage = 'overview';
        this.contentCache = new Map();
        this.isInitialized = false;
        
        this.init();
    }
    
    async init() {
        try {
            // 初始化各个模块
            await this.initializeModules();
            
            // 加载初始页面
            await this.loadPage('overview');
            
            // 设置事件监听器
            this.setupEventListeners();
            
            this.isInitialized = true;
            console.log('SuperRPG文档系统初始化完成');
        } catch (error) {
            console.error('初始化失败:', error);
            this.showError('文档系统初始化失败，请刷新页面重试');
        }
    }
    
    async initializeModules() {
        // 初始化主题
        if (window.themeManager) {
            window.themeManager.init();
        }
        
        // 初始化搜索
        if (window.searchManager) {
            await window.searchManager.init();
        }
        
        // 初始化导航
        if (window.navigationManager) {
            window.navigationManager.init();
        }
        
        // 初始化代码高亮
        if (window.highlightManager) {
            window.highlightManager.init();
        }
    }
    
    setupEventListeners() {
        // 侧边栏切换
        const sidebarToggle = document.getElementById('sidebar-toggle');
        const sidebar = document.getElementById('sidebar');
        
        if (sidebarToggle && sidebar) {
            sidebarToggle.addEventListener('click', () => {
                sidebar.classList.toggle('open');
            });
            
            // 点击外部关闭侧边栏
            document.addEventListener('click', (e) => {
                if (window.innerWidth <= 768 && 
                    !sidebar.contains(e.target) && 
                    !sidebarToggle.contains(e.target)) {
                    sidebar.classList.remove('open');
                }
            });
        }
        
        // 打印按钮
        const printBtn = document.getElementById('print-btn');
        if (printBtn) {
            printBtn.addEventListener('click', () => {
                window.print();
            });
        }
        
        // 键盘快捷键
        document.addEventListener('keydown', (e) => {
            this.handleKeyboardShortcuts(e);
        });
        
        // 窗口大小变化
        window.addEventListener('resize', () => {
            this.handleResize();
        });
        
        // 浏览器前进后退
        window.addEventListener('popstate', (e) => {
            if (e.state && e.state.page) {
                this.loadPage(e.state.page, false);
            }
        });
    }
    
    handleKeyboardShortcuts(e) {
        // Ctrl/Cmd + K 打开搜索
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            if (window.searchManager) {
                window.searchManager.openSearch();
            }
        }
        
        // ESC 关闭模态框
        if (e.key === 'Escape') {
            this.closeModals();
        }
        
        // 左右箭头导航
        if (e.key === 'ArrowLeft' && !e.target.matches('input, textarea')) {
            this.navigatePrevious();
        } else if (e.key === 'ArrowRight' && !e.target.matches('input, textarea')) {
            this.navigateNext();
        }
    }
    
    handleResize() {
        // 移动端自动关闭侧边栏
        if (window.innerWidth > 768) {
            const sidebar = document.getElementById('sidebar');
            if (sidebar) {
                sidebar.classList.remove('open');
            }
        }
    }
    
    closeModals() {
        const modals = document.querySelectorAll('.modal.show');
        modals.forEach(modal => {
            modal.classList.remove('show');
        });
    }
    
    async loadPage(pageName, addToHistory = true) {
        if (this.currentPage === pageName && this.contentCache.has(pageName)) {
            return;
        }
        
        try {
            // 显示加载状态
            this.showLoading();
            
            // 获取内容
            let content;
            if (this.contentCache.has(pageName)) {
                content = this.contentCache.get(pageName);
            } else {
                content = await this.fetchPageContent(pageName);
                this.contentCache.set(pageName, content);
            }
            
            // 更新内容
            this.updateContent(content, pageName);
            
            // 更新导航状态
            this.updateNavigation(pageName);
            
            // 更新浏览器历史
            if (addToHistory) {
                const url = `#${pageName}`;
                history.pushState({ page: pageName }, '', url);
            }
            
            this.currentPage = pageName;
            
            // 重新高亮代码
            if (window.highlightManager) {
                window.highlightManager.highlightAll();
            }
            
        } catch (error) {
            console.error('加载页面失败:', error);
            this.showError(`加载页面 "${pageName}" 失败`);
        }
    }
    
    async fetchPageContent(pageName) {
        // 根据页面名称生成内容
        switch (pageName) {
            case 'overview':
                return this.generateOverviewContent();
            case 'architecture':
                return this.generateArchitectureContent();
            case 'principles':
                return this.generatePrinciplesContent();
            case 'domain-layer':
                return this.generateDomainLayerContent();
            case 'application-layer':
                return this.generateApplicationLayerContent();
            case 'infrastructure-layer':
                return this.generateInfrastructureLayerContent();
            case 'adapters-layer':
                return this.generateAdaptersLayerContent();
            case 'game-engine':
                return this.generateGameEngineContent();
            case 'turn-manager':
                return this.generateTurnManagerContent();
            case 'message-handler':
                return this.generateMessageHandlerContent();
            case 'agent-service':
                return this.generateAgentServiceContent();
            case 'commands':
                return this.generateCommandsContent();
            case 'queries':
                return this.generateQueriesContent();
            case 'events':
                return this.generateEventsContent();
            case 'character-example':
                return this.generateCharacterExampleContent();
            case 'world-example':
                return this.generateWorldExampleContent();
            case 'combat-example':
                return this.generateCombatExampleContent();
            case 'event-example':
                return this.generateEventExampleContent();
            default:
                throw new Error(`未知页面: ${pageName}`);
        }
    }
    
    updateContent(content, pageName) {
        const contentElement = document.getElementById('content');
        if (contentElement) {
            contentElement.innerHTML = content;
            
            // 滚动到顶部
            contentElement.scrollTop = 0;
        }
        
        // 更新面包屑
        this.updateBreadcrumb(pageName);
    }
    
    updateNavigation(pageName) {
        // 更新导航链接状态
        const navLinks = document.querySelectorAll('.nav-link');
        navLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('data-page') === pageName) {
                link.classList.add('active');
            }
        });
    }
    
    updateBreadcrumb(pageName) {
        const breadcrumb = document.getElementById('breadcrumb');
        if (!breadcrumb) return;
        
        const pageMap = {
            'overview': '项目介绍',
            'architecture': '架构设计',
            'principles': '设计原则',
            'domain-layer': '领域层',
            'application-layer': '应用层',
            'infrastructure-layer': '基础设施层',
            'adapters-layer': '适配器层',
            'game-engine': '游戏引擎',
            'turn-manager': '回合管理器',
            'message-handler': '消息处理器',
            'agent-service': '代理服务',
            'commands': '命令接口',
            'queries': '查询接口',
            'events': '事件系统',
            'character-example': '角色管理示例',
            'world-example': '世界状态示例',
            'combat-example': '战斗系统示例',
            'event-example': '事件处理示例'
        };
        
        const pageNameText = pageMap[pageName] || pageName;
        breadcrumb.innerHTML = `<span class="breadcrumb-item">${pageNameText}</span>`;
    }
    
    navigatePrevious() {
        const navLinks = Array.from(document.querySelectorAll('.nav-link'));
        const currentIndex = navLinks.findIndex(link => 
            link.getAttribute('data-page') === this.currentPage
        );
        
        if (currentIndex > 0) {
            const prevLink = navLinks[currentIndex - 1];
            const pageName = prevLink.getAttribute('data-page');
            this.loadPage(pageName);
        }
    }
    
    navigateNext() {
        const navLinks = Array.from(document.querySelectorAll('.nav-link'));
        const currentIndex = navLinks.findIndex(link => 
            link.getAttribute('data-page') === this.currentPage
        );
        
        if (currentIndex < navLinks.length - 1) {
            const nextLink = navLinks[currentIndex + 1];
            const pageName = nextLink.getAttribute('data-page');
            this.loadPage(pageName);
        }
    }
    
    showLoading() {
        const contentElement = document.getElementById('content');
        if (contentElement) {
            contentElement.innerHTML = `
                <div class="loading">
                    <i class="fas fa-spinner fa-spin"></i>
                    <span>加载中...</span>
                </div>
            `;
        }
    }
    
    showError(message) {
        const contentElement = document.getElementById('content');
        if (contentElement) {
            contentElement.innerHTML = `
                <div class="card">
                    <div class="card-header">
                        <h2 class="card-title">错误</h2>
                    </div>
                    <div class="card-body">
                        <div class="alert alert-error">
                            <i class="fas fa-exclamation-triangle"></i>
                            ${message}
                        </div>
                        <button class="btn btn-primary" onclick="location.reload()">
                            <i class="fas fa-refresh"></i>
                            刷新页面
                        </button>
                    </div>
                </div>
            `;
        }
    }
    
    // 页面内容生成方法
    generateOverviewContent() {
        return window.pageGeneratorsComplete ? window.pageGeneratorsComplete.overview() : '';
    }
    
    generateArchitectureContent() {
        return window.pageGeneratorsComplete ? window.pageGeneratorsComplete.architecture() : '';
    }
    
    generatePrinciplesContent() {
        return window.pageGeneratorsComplete ? window.pageGeneratorsComplete.principles() : '';
    }
    
    generateDomainLayerContent() {
        return window.pageGeneratorsComplete ? window.pageGeneratorsComplete.domainLayer() : '';
    }
    
    generateApplicationLayerContent() {
        return window.pageGeneratorsComplete ? window.pageGeneratorsComplete.applicationLayer() : '';
    }
    
    generateInfrastructureLayerContent() {
        return window.pageGeneratorsComplete ? window.pageGeneratorsComplete.infrastructureLayer() : '';
    }
    
    generateAdaptersLayerContent() {
        return window.pageGeneratorsComplete ? window.pageGeneratorsComplete.adaptersLayer() : '';
    }
    
    generateGameEngineContent() {
        return window.pageGeneratorsComplete ? window.pageGeneratorsComplete.gameEngine() : '';
    }
    
    generateTurnManagerContent() {
        return window.pageGeneratorsComplete ? window.pageGeneratorsComplete.turnManager() : '';
    }
    
    generateMessageHandlerContent() {
        return window.pageGeneratorsComplete ? window.pageGeneratorsComplete.messageHandler() : '';
    }
    
    generateAgentServiceContent() {
        return window.pageGeneratorsComplete ? window.pageGeneratorsComplete.agentService() : '';
    }
    
    generateCommandsContent() {
        return window.pageGeneratorsComplete ? window.pageGeneratorsComplete.commands() : '';
    }
    
    generateQueriesContent() {
        return window.pageGeneratorsComplete ? window.pageGeneratorsComplete.queries() : '';
    }
    
    generateEventsContent() {
        return window.pageGeneratorsComplete ? window.pageGeneratorsComplete.events() : '';
    }
    
    generateCharacterExampleContent() {
        return window.pageGeneratorsComplete ? window.pageGeneratorsComplete.characterExample() : '';
    }
    
    generateWorldExampleContent() {
        return window.pageGeneratorsComplete ? window.pageGeneratorsComplete.worldExample() : '';
    }
    
    generateCombatExampleContent() {
        return window.pageGeneratorsComplete ? window.pageGeneratorsComplete.combatExample() : '';
    }
    
    generateEventExampleContent() {
        return window.pageGeneratorsComplete ? window.pageGeneratorsComplete.eventExample() : '';
    }
}

// 全局实例
window.superRPGDocs = new SuperRPGDocs();

// 页面加载完成后的初始化
document.addEventListener('DOMContentLoaded', () => {
    // 处理初始URL hash
    if (window.location.hash) {
        const pageName = window.location.hash.substring(1);
        window.superRPGDocs.loadPage(pageName, false);
    }
});