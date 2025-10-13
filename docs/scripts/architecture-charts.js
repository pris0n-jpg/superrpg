// 架构图表管理器
class ArchitectureCharts {
    constructor() {
        this.charts = new Map();
        this.isInitialized = false;
    }
    
    init() {
        this.setupCharts();
        this.isInitialized = true;
    }
    
    setupCharts() {
        // 创建分层架构图
        this.createLayeredArchitectureChart();
        
        // 创建组件依赖图
        this.createComponentDependencyChart();
        
        // 创建数据流图
        this.createDataFlowChart();
        
        // 创建事件流图
        this.createEventFlowChart();
    }
    
    createLayeredArchitectureChart() {
        const container = document.getElementById('layered-architecture-chart');
        if (!container) return;
        
        const svg = this.createSVG(container.width || 800, container.height || 600);
        
        // 定义层级
        const layers = [
            { name: '表示层', y: 50, color: '#10b981', components: ['用户界面', 'API接口'] },
            { name: '应用层', y: 150, color: '#3b82f6', components: ['游戏引擎', '回合管理器', '消息处理器', '代理服务'] },
            { name: '领域层', y: 250, color: '#f59e0b', components: ['角色模型', '战斗模型', '世界模型', '领域服务'] },
            { name: '适配器层', y: 350, color: '#8b5cf6', components: ['代理适配器', '工具适配器', '世界适配器'] },
            { name: '基础设施层', y: 450, color: '#ef4444', components: ['事件总线', '日志系统', '配置管理', '仓储实现'] }
        ];
        
        // 绘制层级
        layers.forEach((layer, index) => {
            // 绘制层级背景
            const rect = this.createRect(50, layer.y, 700, 80, layer.color, 0.1);
            rect.setAttribute('stroke', layer.color);
            rect.setAttribute('stroke-width', '2');
            svg.appendChild(rect);
            
            // 绘制层级标题
            const text = this.createText(60, layer.y + 25, layer.name, 'bold', 16);
            text.setAttribute('fill', layer.color);
            svg.appendChild(text);
            
            // 绘制组件
            layer.components.forEach((component, compIndex) => {
                const compX = 200 + compIndex * 150;
                const compRect = this.createRect(compX, layer.y + 35, 120, 30, layer.color, 0.2);
                compRect.setAttribute('stroke', layer.color);
                compRect.setAttribute('stroke-width', '1');
                compRect.setAttribute('rx', '5');
                svg.appendChild(compRect);
                
                const compText = this.createText(compX + 60, layer.y + 52, component, 'normal', 12);
                compText.setAttribute('fill', this.getTextColor());
                svg.appendChild(compText);
            });
        });
        
        // 绘制连接线
        this.drawConnections(svg, layers);
        
        container.appendChild(svg);
        this.charts.set('layered-architecture', svg);
    }
    
    createComponentDependencyChart() {
        const container = document.getElementById('component-dependency-chart');
        if (!container) return;
        
        const svg = this.createSVG(container.width || 800, container.height || 600);
        
        // 定义组件和依赖关系
        const components = [
            { id: 'game-engine', name: '游戏引擎', x: 400, y: 100, color: '#3b82f6' },
            { id: 'turn-manager', name: '回合管理器', x: 200, y: 200, color: '#3b82f6' },
            { id: 'message-handler', name: '消息处理器', x: 600, y: 200, color: '#3b82f6' },
            { id: 'agent-service', name: '代理服务', x: 400, y: 300, color: '#3b82f6' },
            { id: 'character-service', name: '角色服务', x: 100, y: 400, color: '#f59e0b' },
            { id: 'world-service', name: '世界服务', x: 300, y: 400, color: '#f59e0b' },
            { id: 'combat-service', name: '战斗服务', x: 500, y: 400, color: '#f59e0b' },
            { id: 'event-bus', name: '事件总线', x: 700, y: 400, color: '#ef4444' }
        ];
        
        // 定义依赖关系
        const dependencies = [
            { from: 'game-engine', to: 'turn-manager' },
            { from: 'game-engine', to: 'message-handler' },
            { from: 'game-engine', to: 'agent-service' },
            { from: 'turn-manager', to: 'world-service' },
            { from: 'message-handler', to: 'character-service' },
            { from: 'agent-service', to: 'character-service' },
            { from: 'agent-service', to: 'world-service' },
            { from: 'character-service', to: 'event-bus' },
            { from: 'world-service', to: 'event-bus' },
            { from: 'combat-service', to: 'event-bus' }
        ];
        
        // 绘制组件
        components.forEach(component => {
            const group = this.createGroup();
            
            // 组件背景
            const rect = this.createRect(component.x - 60, component.y - 25, 120, 50, component.color, 0.1);
            rect.setAttribute('stroke', component.color);
            rect.setAttribute('stroke-width', '2');
            rect.setAttribute('rx', '8');
            group.appendChild(rect);
            
            // 组件名称
            const text = this.createText(component.x, component.y + 5, component.name, 'bold', 14);
            text.setAttribute('fill', component.color);
            text.setAttribute('text-anchor', 'middle');
            group.appendChild(text);
            
            // 添加交互
            group.style.cursor = 'pointer';
            group.addEventListener('mouseenter', () => {
                rect.setAttribute('fill-opacity', '0.2');
                rect.setAttribute('stroke-width', '3');
            });
            
            group.addEventListener('mouseleave', () => {
                rect.setAttribute('fill-opacity', '0.1');
                rect.setAttribute('stroke-width', '2');
            });
            
            svg.appendChild(group);
        });
        
        // 绘制依赖关系
        dependencies.forEach(dep => {
            const fromComponent = components.find(c => c.id === dep.from);
            const toComponent = components.find(c => c.id === dep.to);
            
            if (fromComponent && toComponent) {
                const arrow = this.createArrow(
                    fromComponent.x, fromComponent.y + 25,
                    toComponent.x, toComponent.y - 25,
                    '#64748b', 2
                );
                svg.appendChild(arrow);
            }
        });
        
        container.appendChild(svg);
        this.charts.set('component-dependency', svg);
    }
    
    createDataFlowChart() {
        const container = document.getElementById('data-flow-chart');
        if (!container) return;
        
        const canvas = this.createCanvas(container.width || 800, container.height || 400);
        const ctx = canvas.getContext('2d');
        
        // 定义数据流步骤
        const steps = [
            { name: '客户端请求', x: 100, y: 200, color: '#10b981' },
            { name: 'API接口', x: 250, y: 200, color: '#3b82f6' },
            { name: '命令处理器', x: 400, y: 200, color: '#3b82f6' },
            { name: '领域服务', x: 550, y: 200, color: '#f59e0b' },
            { name: '仓储持久化', x: 700, y: 200, color: '#ef4444' }
        ];
        
        // 绘制步骤
        steps.forEach(step => {
            // 绘制圆形节点
            ctx.beginPath();
            ctx.arc(step.x, step.y, 30, 0, 2 * Math.PI);
            ctx.fillStyle = step.color + '20';
            ctx.fill();
            ctx.strokeStyle = step.color;
            ctx.lineWidth = 2;
            ctx.stroke();
            
            // 绘制文字
            ctx.fillStyle = this.getTextColor();
            ctx.font = '12px Arial';
            ctx.textAlign = 'center';
            ctx.fillText(step.name, step.x, step.y + 50);
        });
        
        // 绘制流向箭头
        for (let i = 0; i < steps.length - 1; i++) {
            this.drawCanvasArrow(ctx, steps[i].x + 30, steps[i].y, steps[i + 1].x - 30, steps[i + 1].y);
        }
        
        container.appendChild(canvas);
        this.charts.set('data-flow', canvas);
    }
    
    createEventFlowChart() {
        const container = document.getElementById('event-flow-chart');
        if (!container) return;
        
        const svg = this.createSVG(container.width || 800, container.height || 500);
        
        // 定义事件流程
        const events = [
            { name: '领域事件发布', x: 100, y: 100, type: 'domain' },
            { name: '事件总线分发', x: 300, y: 100, type: 'infrastructure' },
            { name: '事件处理器A', x: 200, y: 250, type: 'handler' },
            { name: '事件处理器B', x: 400, y: 250, type: 'handler' },
            { name: '事件处理器C', x: 300, y: 400, type: 'handler' }
        ];
        
        // 颜色映射
        const colors = {
            domain: '#f59e0b',
            infrastructure: '#ef4444',
            handler: '#3b82f6'
        };
        
        // 绘制事件节点
        events.forEach((event, index) => {
            const group = this.createGroup();
            
            // 事件节点
            const circle = this.createCircle(event.x, event.y, 40, colors[event.type], 0.2);
            circle.setAttribute('stroke', colors[event.type]);
            circle.setAttribute('stroke-width', '2');
            group.appendChild(circle);
            
            // 事件名称
            const text = this.createText(event.x, event.y + 60, event.name, 'normal', 12);
            text.setAttribute('text-anchor', 'middle');
            text.setAttribute('fill', this.getTextColor());
            group.appendChild(text);
            
            svg.appendChild(group);
        });
        
        // 绘制事件流向
        this.drawEventFlow(svg, events);
        
        container.appendChild(svg);
        this.charts.set('event-flow', svg);
    }
    
    drawConnections(svg, layers) {
        const connections = [
            { from: '表示层', to: '应用层', fromComp: 0, toComp: 0 },
            { from: '应用层', to: '领域层', fromComp: 0, toComp: 0 },
            { from: '应用层', to: '适配器层', fromComp: 2, toComp: 1 },
            { from: '适配器层', to: '基础设施层', fromComp: 1, toComp: 0 }
        ];
        
        connections.forEach(conn => {
            const fromLayer = layers.find(l => l.name === conn.from);
            const toLayer = layers.find(l => l.name === conn.to);
            
            if (fromLayer && toLayer) {
                const fromX = 200 + conn.fromComp * 150 + 60;
                const fromY = fromLayer.y + 65;
                const toX = 200 + conn.toComp * 150 + 60;
                const toY = toLayer.y + 35;
                
                const arrow = this.createArrow(fromX, fromY, toX, toY, '#64748b', 2);
                svg.appendChild(arrow);
            }
        });
    }
    
    drawEventFlow(svg, events) {
        const flows = [
            { from: 0, to: 1 },
            { from: 1, to: 2 },
            { from: 1, to: 3 },
            { from: 1, to: 4 }
        ];
        
        flows.forEach(flow => {
            const fromEvent = events[flow.from];
            const toEvent = events[flow.to];
            
            if (fromEvent && toEvent) {
                const arrow = this.createArrow(
                    fromEvent.x, fromEvent.y + 40,
                    toEvent.x, toEvent.y - 40,
                    '#64748b', 2
                );
                svg.appendChild(arrow);
            }
        });
    }
    
    // SVG创建方法
    createSVG(width, height) {
        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('width', width);
        svg.setAttribute('height', height);
        svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
        svg.style.width = '100%';
        svg.style.height = 'auto';
        return svg;
    }
    
    createGroup() {
        return document.createElementNS('http://www.w3.org/2000/svg', 'g');
    }
    
    createRect(x, y, width, height, fill, opacity = 1) {
        const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        rect.setAttribute('x', x);
        rect.setAttribute('y', y);
        rect.setAttribute('width', width);
        rect.setAttribute('height', height);
        rect.setAttribute('fill', fill);
        rect.setAttribute('fill-opacity', opacity);
        return rect;
    }
    
    createCircle(cx, cy, r, fill, opacity = 1) {
        const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        circle.setAttribute('cx', cx);
        circle.setAttribute('cy', cy);
        circle.setAttribute('r', r);
        circle.setAttribute('fill', fill);
        circle.setAttribute('fill-opacity', opacity);
        return circle;
    }
    
    createText(x, y, content, weight = 'normal', size = 14) {
        const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        text.setAttribute('x', x);
        text.setAttribute('y', y);
        text.setAttribute('font-weight', weight);
        text.setAttribute('font-size', size);
        text.setAttribute('font-family', 'Arial, sans-serif');
        text.textContent = content;
        return text;
    }
    
    createArrow(x1, y1, x2, y2, color, width) {
        const group = this.createGroup();
        
        // 计算箭头角度
        const angle = Math.atan2(y2 - y1, x2 - x1);
        
        // 创建箭头线
        const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        line.setAttribute('x1', x1);
        line.setAttribute('y1', y1);
        line.setAttribute('x2', x2);
        line.setAttribute('y2', y2);
        line.setAttribute('stroke', color);
        line.setAttribute('stroke-width', width);
        group.appendChild(line);
        
        // 创建箭头头部
        const arrowLength = 10;
        const arrowAngle = Math.PI / 6;
        
        const x3 = x2 - arrowLength * Math.cos(angle - arrowAngle);
        const y3 = y2 - arrowLength * Math.sin(angle - arrowAngle);
        const x4 = x2 - arrowLength * Math.cos(angle + arrowAngle);
        const y4 = y2 - arrowLength * Math.sin(angle + arrowAngle);
        
        const arrowHead = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
        arrowHead.setAttribute('points', `${x2},${y2} ${x3},${y3} ${x4},${y4}`);
        arrowHead.setAttribute('fill', color);
        group.appendChild(arrowHead);
        
        return group;
    }
    
    // Canvas创建方法
    createCanvas(width, height) {
        const canvas = document.createElement('canvas');
        canvas.width = width;
        canvas.height = height;
        canvas.style.width = '100%';
        canvas.style.height = 'auto';
        return canvas;
    }
    
    drawCanvasArrow(ctx, x1, y1, x2, y2) {
        const headlen = 10;
        const angle = Math.atan2(y2 - y1, x2 - x1);
        
        // 绘制线条
        ctx.beginPath();
        ctx.moveTo(x1, y1);
        ctx.lineTo(x2, y2);
        ctx.strokeStyle = '#64748b';
        ctx.lineWidth = 2;
        ctx.stroke();
        
        // 绘制箭头
        ctx.beginPath();
        ctx.moveTo(x2, y2);
        ctx.lineTo(x2 - headlen * Math.cos(angle - Math.PI / 6), y2 - headlen * Math.sin(angle - Math.PI / 6));
        ctx.moveTo(x2, y2);
        ctx.lineTo(x2 - headlen * Math.cos(angle + Math.PI / 6), y2 - headlen * Math.sin(angle + Math.PI / 6));
        ctx.stroke();
    }
    
    getTextColor() {
        const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        return isDark ? '#f1f5f9' : '#1e293b';
    }
    
    // 重新渲染所有图表
    rerenderAll() {
        this.charts.clear();
        this.setupCharts();
    }
    
    // 获取指定图表
    getChart(name) {
        return this.charts.get(name);
    }
}

// 全局架构图表管理器实例
window.architectureCharts = new ArchitectureCharts();

// 监听主题变化，重新渲染图表
if (typeof document !== 'undefined') {
    document.addEventListener('themechange', () => {
        if (window.architectureCharts) {
            window.architectureCharts.rerenderAll();
        }
    });
}