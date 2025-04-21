/**
 * ui_utils.js
 * 通用UI辅助函数和增强功能
 */

// 自动刷新文件列表
function autoRefreshFiles() {
    if (document.visibilityState === 'visible') {
        const refreshButtons = document.querySelectorAll('.refresh-btn');
        if (refreshButtons.length > 0) {
            refreshButtons[0].click();
        }
    }
}

// 监测窗口大小变化
function checkWindowSize() {
    const isSmall = window.innerWidth <= 768;
    const isVerySmall = window.innerWidth <= 480;
    
    // 更新顶栏布局
    const headerBar = document.querySelector('.header-bar');
    if (headerBar) {
        if (isSmall) {
            headerBar.classList.add('small-screen');
        } else {
            headerBar.classList.remove('small-screen');
        }
        
        if (isVerySmall) {
            headerBar.classList.add('very-small-screen');
        } else {
            headerBar.classList.remove('very-small-screen');
        }
    }
    
    // 记录状态用于侧边栏切换
    window.isSmallScreen = isSmall;
    window.isVerySmallScreen = isVerySmall;
    
    // 在左侧边栏切换按钮上添加标记
    document.querySelectorAll('.sidebar-toggle').forEach(btn => {
        btn.setAttribute('data-small-screen', isSmall);
    });
    
    // 调整侧边栏的响应式行为
    if (typeof adjustSidebarsForScreenSize === 'function') {
        adjustSidebarsForScreenSize(isSmall);
    }
}

// 移除头像容器的样式
function removeAvatars() {
    const style = document.createElement('style');
    style.textContent = `
        .message-avatar, .user-avatar, .bot-avatar {
            display: none !important;
        }
        .message-wrap {
            grid-template-columns: 1fr !important;
        }
        .message, .user-message, .bot-message {
            margin-left: 0 !important;
            grid-column: 1 !important;
        }
        .copy-icon {
            opacity: 1 !important;
            visibility: visible !important;
        }
    `;
    document.head.appendChild(style);
}

// 增强聊天界面功能
function enhanceChatInterface() {
    // 确保复制按钮始终可见
    const style = document.createElement('style');
    style.textContent = `
        .chatbot-copy-button {
            display: inline-block !important;
            opacity: 1 !important;
            visibility: visible !important;
        }
        
        /* 增强聊天消息样式 */
        .chat-message {
            padding: 10px 15px;
            border-radius: 8px;
            margin-bottom: 10px;
            position: relative;
        }
        
        .user-message {
            background-color: #2a2a2a;
            align-self: flex-end;
            margin-left: 20%;
        }
        
        .bot-message {
            background-color: #1e1e1e;
            align-self: flex-start;
            margin-right: 20%;
        }
        
        /* 确保工具输出区域样式正确 */
        .tool-progress, .tool-summary, .error-message {
            margin: 10px 0;
            border-radius: 6px;
            padding: 12px;
            white-space: pre-wrap;
            word-break: break-word;
            overflow-x: auto;
        }
    `;
    document.head.appendChild(style);
    
    // 监听新消息的添加，确保复制按钮可见
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                // 查找新添加的消息中的复制按钮
                const copyButtons = document.querySelectorAll('.copy-icon, .chatbot-copy-button');
                copyButtons.forEach(button => {
                    button.style.opacity = '1';
                    button.style.visibility = 'visible';
                });
            }
        });
    });
    
    // 观察聊天区域的变化
    const chatbotArea = document.querySelector('.chatbot-area');
    if (chatbotArea) {
        observer.observe(chatbotArea, { childList: true, subtree: true });
    }
}

// 调整侧边栏适应不同屏幕大小
function adjustSidebarsForScreenSize(isSmall) {
    if (isSmall) {
        // 小屏幕，对可见的侧边栏应用全屏样式
        const leftSidebar = document.querySelector('.left-sidebar:not(.hidden)');
        const rightSidebar = document.querySelector('.right-sidebar:not(.hidden)');
        
        if (leftSidebar) {
            leftSidebar.classList.add('fullscreen-mobile');
        }
        
        if (rightSidebar) {
            rightSidebar.classList.add('fullscreen-mobile');
        }
    } else {
        // 大屏幕，移除全屏样式
        document.querySelectorAll('.fullscreen-mobile').forEach(sidebar => {
            sidebar.classList.remove('fullscreen-mobile');
        });
    }
}

// 确保侧边栏关闭按钮在全屏模式下可点击
function setupFullscreenSidebarCloseButtons() {
    // 添加点击事件委托
    document.body.addEventListener('click', function(e) {
        // 检查是否点击了关闭按钮的区域
        const rect = e.target.getBoundingClientRect();
        const sidebarFullscreen = document.querySelector('.fullscreen-mobile');
        
        if (sidebarFullscreen && 
            e.clientX >= sidebarFullscreen.getBoundingClientRect().right - 50 && 
            e.clientX <= sidebarFullscreen.getBoundingClientRect().right - 10 &&
            e.clientY >= sidebarFullscreen.getBoundingClientRect().top + 10 &&
            e.clientY <= sidebarFullscreen.getBoundingClientRect().top + 50) {
            
            // 判断是哪个侧边栏并触发相应按钮点击
            if (sidebarFullscreen.classList.contains('left-sidebar')) {
                document.querySelector('.header-left .sidebar-toggle').click();
            } else {
                document.querySelector('.header-right .sidebar-toggle').click();
            }
        }
    });
}

// 处理侧边栏返回按钮点击
function setupSidebarCloseHandlers() {
    document.addEventListener('click', function(e) {
        // 检查点击的是否是侧边栏的返回按钮
        if (e.target.closest('.fullscreen-mobile::before')) {
            const sidebar = e.target.closest('.fullscreen-mobile');
            if (sidebar) {
                // 判断是左侧还是右侧侧边栏
                if (sidebar.classList.contains('left-sidebar')) {
                    document.querySelector('.sidebar-toggle[aria-label="Toggle left sidebar"]').click();
                } else {
                    document.querySelector('.sidebar-toggle[aria-label="Toggle right sidebar"]').click();
                }
            }
        }
    });
}

// 增强侧边栏切换按钮功能
function enhanceSidebarToggleButtons() {
    // 标记侧边栏切换按钮
    const leftToggle = document.querySelector('.header-left .sidebar-toggle');
    const rightToggle = document.querySelector('.header-right .sidebar-toggle');
    
    if (leftToggle) {
        leftToggle.setAttribute('aria-label', 'Toggle left sidebar');
    }
    
    if (rightToggle) {
        rightToggle.setAttribute('aria-label', 'Toggle right sidebar');
    }
}

// 初始化所有UI增强功能
function initializeUI() {
    // 应用头像移除
    removeAvatars();
    
    // 检测屏幕大小
    checkWindowSize();
    
    // 增强聊天界面
    enhanceChatInterface();
    
    // 设置自动刷新
    setInterval(autoRefreshFiles, 5000);
    
    // 添加窗口大小变化监听
    window.addEventListener('resize', checkWindowSize);
    
    // 初始化侧边栏功能
    enhanceSidebarToggleButtons();
    setupFullscreenSidebarCloseButtons();
    setupSidebarCloseHandlers();
    
    // 在小屏幕上初始隐藏两侧侧边栏
    if (window.innerWidth <= 768) {
        const leftSidebar = document.querySelector('.left-sidebar');
        const rightSidebar = document.querySelector('.right-sidebar');
        const centerContent = document.querySelector('.center-content');
        
        if (leftSidebar && rightSidebar && centerContent) {
            leftSidebar.classList.add('hidden');
            rightSidebar.classList.add('hidden');
            centerContent.classList.add('left-hidden', 'right-hidden');
        }
    }
    
    // 添加全局快捷键
    document.addEventListener('keydown', function(e) {
        // Alt+左箭头：切换左侧边栏
        if (e.altKey && e.key === 'ArrowLeft') {
            const leftToggle = document.querySelector('.header-left .sidebar-toggle');
            if (leftToggle) leftToggle.click();
        }
        
        // Alt+右箭头：切换右侧边栏
        if (e.altKey && e.key === 'ArrowRight') {
            const rightToggle = document.querySelector('.header-right .sidebar-toggle');
            if (rightToggle) rightToggle.click();
        }
    });
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', initializeUI);

// 如果DOM已经加载完成，立即执行初始化
if (document.readyState === 'interactive' || document.readyState === 'complete') {
    initializeUI();
}