// 导航管理器
class NavigationManager {
    constructor() {
        this.currentPage = null;
        this.navLinks = [];
        this.isInitialized = false;
    }
    
    init() {
        this.setupNavigation();
        this.setupKeyboardNavigation();
        this.setupSmoothScrolling();
        this.isInitialized = true;
    }
    
    setupNavigation() {
        // 获取所有导航链接
        this.navLinks = document.querySelectorAll('.nav-link');
        
        // 为每个导航链接添加点击事件
        this.navLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const pageName = link.getAttribute('data-page');
                if (pageName) {
                    this.navigateToPage(pageName);
                }
            });
        });
        
        // 处理初始页面
        const hash = window.location.hash.substring(1);
        if (hash) {
            this.navigateToPage(hash, false);
        } else {
            this.navigateToPage('overview', false);
        }
    }
    
    setupKeyboardNavigation() {
        document.addEventListener('keydown', (e) => {
            // 只在非输入元素上响应键盘导航
            if (e.target.matches('input, textarea, select')) {
                return;
            }
            
            switch (e.key) {
                case 'ArrowLeft':
                    e.preventDefault();
                    this.navigatePrevious();
                    break;
                case 'ArrowRight':
                    e.preventDefault();
                    this.navigateNext();
                    break;
                case 'Home':
                    e.preventDefault();
                    this.navigateFirst();
                    break;
                case 'End':
                    e.preventDefault();
                    this.navigateLast();
                    break;
            }
        });
    }
    
    setupSmoothScrolling() {
        // 为页面内的锚点链接添加平滑滚动
        document.addEventListener('click', (e) => {
            if (e.target.matches('a[href^="#"]')) {
                const targetId = e.target.getAttribute('href').substring(1);
                const targetElement = document.getElementById(targetId);
                
                if (targetElement) {
                    e.preventDefault();
                    targetElement.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            }
        });
    }
    
    navigateToPage(pageName, addToHistory = true) {
        if (this.currentPage === pageName) {
            return;
        }
        
        // 更新当前页面
        this.currentPage = pageName;
        
        // 更新导航状态
        this.updateNavigationState(pageName, addToHistory);
        
        // 触发页面加载
        if (window.superRPGDocs) {
            window.superRPGDocs.loadPage(pageName, addToHistory);
        }
        
        // 移动端自动关闭侧边栏
        if (window.innerWidth <= 768) {
            const sidebar = document.getElementById('sidebar');
            if (sidebar) {
                sidebar.classList.remove('open');
            }
        }
    }
    
    updateNavigationState(pageName, addToHistory = true) {
        // 更新导航链接的激活状态
        this.navLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('data-page') === pageName) {
                link.classList.add('active');
            }
        });
        
        // 更新浏览器历史
        if (addToHistory) {
            const url = `#${pageName}`;
            history.pushState({ page: pageName }, '', url);
        }
    }
    
    navigatePrevious() {
        const currentIndex = this.getCurrentPageIndex();
        if (currentIndex > 0) {
            const prevLink = this.navLinks[currentIndex - 1];
            const pageName = prevLink.getAttribute('data-page');
            this.navigateToPage(pageName);
        }
    }
    
    navigateNext() {
        const currentIndex = this.getCurrentPageIndex();
        if (currentIndex < this.navLinks.length - 1) {
            const nextLink = this.navLinks[currentIndex + 1];
            const pageName = nextLink.getAttribute('data-page');
            this.navigateToPage(pageName);
        }
    }
    
    navigateFirst() {
        if (this.navLinks.length > 0) {
            const firstLink = this.navLinks[0];
            const pageName = firstLink.getAttribute('data-page');
            this.navigateToPage(pageName);
        }
    }
    
    navigateLast() {
        if (this.navLinks.length > 0) {
            const lastLink = this.navLinks[this.navLinks.length - 1];
            const pageName = lastLink.getAttribute('data-page');
            this.navigateToPage(pageName);
        }
    }
    
    getCurrentPageIndex() {
        return this.navLinks.findIndex(link => 
            link.getAttribute('data-page') === this.currentPage
        );
    }
    
    // 获取页面的导航信息
    getPageNavigation(pageName) {
        const pageIndex = this.navLinks.findIndex(link => 
            link.getAttribute('data-page') === pageName
        );
        
        if (pageIndex === -1) {
            return null;
        }
        
        return {
            currentPage: pageName,
            currentIndex: pageIndex,
            totalPages: this.navLinks.length,
            hasNext: pageIndex < this.navLinks.length - 1,
            hasPrevious: pageIndex > 0,
            nextPage: pageIndex < this.navLinks.length - 1 ? 
                this.navLinks[pageIndex + 1].getAttribute('data-page') : null,
            previousPage: pageIndex > 0 ? 
                this.navLinks[pageIndex - 1].getAttribute('data-page') : null
        };
    }
    
    // 生成导航提示
    generateNavigationHints() {
        const nav = this.getPageNavigation(this.currentPage);
        if (!nav) return '';
        
        let hints = [];
        
        if (nav.hasPrevious) {
            hints.push(`← 上一页 (${this.getShortcutText('ArrowLeft')})`);
        }
        
        if (nav.hasNext) {
            hints.push(`下一页 → (${this.getShortcutText('ArrowRight')})`);
        }
        
        hints.push(`搜索 (${this.getShortcutText('Ctrl+K')})`);
        
        return hints.join(' • ');
    }
    
    getShortcutText(shortcut) {
        const isMac = /Mac|iPod|iPhone|iPad/.test(navigator.platform);
        
        switch (shortcut) {
            case 'Ctrl+K':
                return isMac ? '⌘K' : 'Ctrl+K';
            case 'ArrowLeft':
                return '←';
            case 'ArrowRight':
                return '→';
            default:
                return shortcut;
        }
    }
    
    // 创建面包屑导航
    createBreadcrumb(pageName) {
        const breadcrumbMap = {
            'overview': { text: '项目介绍', parent: null },
            'architecture': { text: '架构设计', parent: 'overview' },
            'principles': { text: '设计原则', parent: 'architecture' },
            'domain-layer': { text: '领域层', parent: 'architecture' },
            'application-layer': { text: '应用层', parent: 'architecture' },
            'infrastructure-layer': { text: '基础设施层', parent: 'architecture' },
            'adapters-layer': { text: '适配器层', parent: 'architecture' },
            'game-engine': { text: '游戏引擎', parent: 'application-layer' },
            'turn-manager': { text: '回合管理器', parent: 'application-layer' },
            'message-handler': { text: '消息处理器', parent: 'application-layer' },
            'agent-service': { text: '代理服务', parent: 'application-layer' },
            'commands': { text: '命令接口', parent: 'application-layer' },
            'queries': { text: '查询接口', parent: 'application-layer' },
            'events': { text: '事件系统', parent: 'application-layer' },
            'character-example': { text: '角色管理示例', parent: 'commands' },
            'world-example': { text: '世界状态示例', parent: 'commands' },
            'combat-example': { text: '战斗系统示例', parent: 'commands' },
            'event-example': { text: '事件处理示例', parent: 'commands' }
        };
        
        const pageInfo = breadcrumbMap[pageName];
        if (!pageInfo) {
            return `<span class="breadcrumb-item">${pageName}</span>`;
        }
        
        let breadcrumb = [];
        
        // 构建面包屑路径
        let current = pageName;
        while (current) {
            const info = breadcrumbMap[current];
            if (!info) break;
            
            breadcrumb.unshift({
                page: current,
                text: info.text
            });
            
            current = info.parent;
        }
        
        // 生成面包屑HTML
        let html = '';
        breadcrumb.forEach((item, index) => {
            const isActive = item.page === pageName;
            const className = `breadcrumb-item ${isActive ? 'active' : ''}`;
            
            if (isActive) {
                html += `<span class="${className}">${item.text}</span>`;
            } else {
                html += `<a href="#${item.page}" class="${className}" data-page="${item.page}">${item.text}</a>`;
            }
            
            if (index < breadcrumb.length - 1) {
                html += '<span class="breadcrumb-separator">/</span>';
            }
        });
        
        return html;
    }
    
    // 创建页面导航（上一页/下一页）
    createPageNavigation(pageName) {
        const nav = this.getPageNavigation(pageName);
        if (!nav) return '';
        
        let html = '<nav class="page-navigation">';
        
        if (nav.hasPrevious) {
            html += `
                <a href="#${nav.previousPage}" class="nav-prev" data-page="${nav.previousPage}">
                    <i class="fas fa-arrow-left"></i>
                    <span>${this.getPageTitle(nav.previousPage)}</span>
                </a>
            `;
        }
        
        if (nav.hasNext) {
            html += `
                <a href="#${nav.nextPage}" class="nav-next" data-page="${nav.nextPage}">
                    <span>${this.getPageTitle(nav.nextPage)}</span>
                    <i class="fas fa-arrow-right"></i>
                </a>
            `;
        }
        
        html += '</nav>';
        
        return html;
    }
    
    getPageTitle(pageName) {
        const navLink = Array.from(this.navLinks).find(link => 
            link.getAttribute('data-page') === pageName
        );
        
        if (navLink) {
            return navLink.textContent.trim();
        }
        
        // 备用标题映射
        const titleMap = {
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
        
        return titleMap[pageName] || pageName;
    }
    
    // 高亮当前页面的导航项
    highlightCurrentPage() {
        this.navLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('data-page') === this.currentPage) {
                link.classList.add('active');
            }
        });
    }
    
    // 展开当前页面的父级菜单（如果有折叠菜单）
    expandParentMenu() {
        const currentLink = Array.from(this.navLinks).find(link => 
            link.getAttribute('data-page') === this.currentPage
        );
        
        if (currentLink) {
            let parent = currentLink.closest('.nav-section');
            while (parent) {
                parent.classList.add('expanded');
                parent = parent.parentElement.closest('.nav-section');
            }
        }
    }
}

// 全局导航管理器实例
window.navigationManager = new NavigationManager();
