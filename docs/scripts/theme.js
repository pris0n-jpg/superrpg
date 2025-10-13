// 主题管理器
class ThemeManager {
    constructor() {
        this.currentTheme = 'light';
        this.isInitialized = false;
        this.themeToggle = null;
        this.systemPreference = null;
    }
    
    init() {
        this.setupThemeToggle();
        this.detectSystemPreference();
        this.loadSavedTheme();
        this.applyTheme(this.currentTheme);
        this.setupSystemPreferenceListener();
        this.isInitialized = true;
    }
    
    setupThemeToggle() {
        this.themeToggle = document.getElementById('theme-toggle');
        
        if (this.themeToggle) {
            this.themeToggle.addEventListener('click', () => {
                this.toggleTheme();
            });
        }
    }
    
    detectSystemPreference() {
        // 检测系统主题偏好
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            this.systemPreference = 'dark';
        } else {
            this.systemPreference = 'light';
        }
    }
    
    setupSystemPreferenceListener() {
        // 监听系统主题变化
        if (window.matchMedia) {
            const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
            mediaQuery.addEventListener('change', (e) => {
                this.systemPreference = e.matches ? 'dark' : 'light';
                
                // 如果用户没有手动设置主题，跟随系统
                if (!this.getSavedTheme()) {
                    this.applyTheme(this.systemPreference);
                }
            });
        }
    }
    
    loadSavedTheme() {
        // 从localStorage加载保存的主题
        const savedTheme = this.getSavedTheme();
        if (savedTheme) {
            this.currentTheme = savedTheme;
        } else {
            // 如果没有保存的主题，使用系统偏好
            this.currentTheme = this.systemPreference;
        }
    }
    
    getSavedTheme() {
        try {
            return localStorage.getItem('superrpg-theme');
        } catch (e) {
            console.warn('无法访问localStorage:', e);
            return null;
        }
    }
    
    saveTheme(theme) {
        try {
            localStorage.setItem('superrpg-theme', theme);
        } catch (e) {
            console.warn('无法保存主题到localStorage:', e);
        }
    }
    
    toggleTheme() {
        const newTheme = this.currentTheme === 'light' ? 'dark' : 'light';
        this.setTheme(newTheme);
    }
    
    setTheme(theme) {
        if (theme !== 'light' && theme !== 'dark') {
            console.warn('无效的主题:', theme);
            return;
        }
        
        this.currentTheme = theme;
        this.applyTheme(theme);
        this.saveTheme(theme);
        this.updateThemeToggle();
        
        // 触发主题变化事件
        this.dispatchThemeChangeEvent(theme);
    }
    
    applyTheme(theme) {
        // 应用主题到document
        document.documentElement.setAttribute('data-theme', theme);
        
        // 更新meta标签（用于移动端）
        this.updateMetaThemeColor(theme);
        
        // 更新主题相关的CSS变量
        this.updateThemeVariables(theme);
    }
    
    updateMetaThemeColor(theme) {
        // 更新主题色meta标签
        let metaThemeColor = document.querySelector('meta[name="theme-color"]');
        if (!metaThemeColor) {
            metaThemeColor = document.createElement('meta');
            metaThemeColor.name = 'theme-color';
            document.head.appendChild(metaThemeColor);
        }
        
        const themeColors = {
            light: '#ffffff',
            dark: '#0f172a'
        };
        
        metaThemeColor.content = themeColors[theme] || themeColors.light;
    }
    
    updateThemeVariables(theme) {
        // 可以在这里动态调整一些主题变量
        const root = document.documentElement;
        
        if (theme === 'dark') {
            // 暗色主题的特殊调整
            root.style.setProperty('--chart-grid-color', 'rgba(255, 255, 255, 0.1)');
            root.style.setProperty('--chart-text-color', 'rgba(255, 255, 255, 0.8)');
        } else {
            // 亮色主题的特殊调整
            root.style.setProperty('--chart-grid-color', 'rgba(0, 0, 0, 0.1)');
            root.style.setProperty('--chart-text-color', 'rgba(0, 0, 0, 0.8)');
        }
    }
    
    updateThemeToggle() {
        if (!this.themeToggle) return;
        
        const icon = this.themeToggle.querySelector('i');
        if (icon) {
            // 更新图标
            if (this.currentTheme === 'dark') {
                icon.className = 'fas fa-sun';
                this.themeToggle.title = '切换到亮色主题';
            } else {
                icon.className = 'fas fa-moon';
                this.themeToggle.title = '切换到暗色主题';
            }
        }
    }
    
    dispatchThemeChangeEvent(theme) {
        // 触发自定义主题变化事件
        const event = new CustomEvent('themechange', {
            detail: { theme: theme }
        });
        document.dispatchEvent(event);
    }
    
    // 获取当前主题
    getCurrentTheme() {
        return this.currentTheme;
    }
    
    // 获取系统主题偏好
    getSystemPreference() {
        return this.systemPreference;
    }
    
    // 重置为系统主题
    resetToSystemTheme() {
        this.setTheme(this.systemPreference);
        try {
            localStorage.removeItem('superrpg-theme');
        } catch (e) {
            console.warn('无法清除localStorage中的主题设置:', e);
        }
    }
    
    // 检查是否为暗色主题
    isDarkTheme() {
        return this.currentTheme === 'dark';
    }
    
    // 检查是否为亮色主题
    isLightTheme() {
        return this.currentTheme === 'light';
    }
    
    // 获取主题配置
    getThemeConfig() {
        return {
            current: this.currentTheme,
            system: this.systemPreference,
            isFollowingSystem: !this.getSavedTheme(),
            availableThemes: ['light', 'dark']
        };
    }
    
    // 应用主题到特定元素
    applyThemeToElement(element, theme) {
        if (!element) return;
        
        element.setAttribute('data-theme', theme);
    }
    
    // 为图表等组件获取主题颜色
    getThemeColors() {
        const colors = {
            light: {
                primary: '#2563eb',
                secondary: '#64748b',
                background: '#ffffff',
                surface: '#f8fafc',
                text: '#1e293b',
                textSecondary: '#64748b',
                border: '#e2e8f0',
                grid: 'rgba(0, 0, 0, 0.1)',
                success: '#10b981',
                warning: '#f59e0b',
                error: '#ef4444'
            },
            dark: {
                primary: '#3b82f6',
                secondary: '#94a3b8',
                background: '#0f172a',
                surface: '#1e293b',
                text: '#f1f5f9',
                textSecondary: '#cbd5e1',
                border: '#334155',
                grid: 'rgba(255, 255, 255, 0.1)',
                success: '#22c55e',
                warning: '#fbbf24',
                error: '#f87171'
            }
        };
        
        return colors[this.currentTheme] || colors.light;
    }
    
    // 为代码高亮获取主题
    getCodeTheme() {
        return this.currentTheme === 'dark' ? 'dark' : 'light';
    }
    
    // 创建主题切换按钮（如果需要动态创建）
    createThemeToggle(container) {
        const button = document.createElement('button');
        button.id = 'theme-toggle';
        button.className = 'theme-toggle-btn';
        button.title = '切换主题';
        button.setAttribute('aria-label', '切换主题');
        
        const icon = document.createElement('i');
        icon.className = this.currentTheme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
        
        button.appendChild(icon);
        
        if (container) {
            container.appendChild(button);
        }
        
        // 重新设置事件监听器
        button.addEventListener('click', () => {
            this.toggleTheme();
        });
        
        this.themeToggle = button;
        return button;
    }
    
    // 监听主题变化
    onThemeChange(callback) {
        if (typeof callback === 'function') {
            document.addEventListener('themechange', (e) => {
                callback(e.detail.theme);
            });
        }
    }
    
    // 获取主题过渡动画类
    getThemeTransitionClass() {
        return 'theme-transitioning';
    }
    
    // 添加主题过渡效果
    addThemeTransition() {
        document.documentElement.classList.add(this.getThemeTransitionClass());
        
        // 移除过渡类（确保过渡效果只应用一次）
        setTimeout(() => {
            document.documentElement.classList.remove(this.getThemeTransitionClass());
        }, 300);
    }
    
    // 设置主题（带过渡效果）
    setThemeWithTransition(theme) {
        this.addThemeTransition();
        setTimeout(() => {
            this.setTheme(theme);
        }, 50);
    }
}

// 全局主题管理器实例
window.themeManager = new ThemeManager();

// 主题过渡CSS（如果需要动态添加）
const themeTransitionCSS = `
.theme-transitioning,
.theme-transitioning * {
    transition: background-color 300ms ease-in-out, 
                color 300ms ease-in-out, 
                border-color 300ms ease-in-out !important;
}
`;

// 动态添加过渡CSS
if (typeof document !== 'undefined') {
    const style = document.createElement('style');
    style.textContent = themeTransitionCSS;
    document.head.appendChild(style);
}

// 导出主题管理器（如果使用模块系统）
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ThemeManager;
}