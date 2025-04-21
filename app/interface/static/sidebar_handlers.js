/**
 * sidebar_handlers.js
 * 侧边栏处理和交互功能
 */

// 增强侧边栏切换按钮功能
function enhanceSidebarToggleButtons() {
    // 标记侧边栏切换按钮
    const leftToggle = document.querySelector('.header-left .sidebar-toggle');
    const rightToggle = document.querySelector('.header-right .sidebar-toggle');
    
    if (leftToggle) {
        leftToggle.setAttribute('aria-label', 'Toggle left sidebar');
        leftToggle.onclick = function() {
            const leftSidebar = document.querySelector('.left-sidebar');
            const isHidden = leftSidebar.classList.contains('hidden');
            
            if (!isHidden) {
                // 当前可见，需要隐藏
                leftSidebar.classList.add('hidden');
                leftSidebar.classList.remove('fullscreen-mobile');
                document.querySelector('.center-content').classList.add('left-hidden');
            } else {
                // 当前隐藏，需要显示
                leftSidebar.classList.remove('hidden');
                document.querySelector('.center-content').classList.remove('left-hidden');
                
                // 小屏幕应用全屏模式
                if (window.isSmallScreen) {
                    leftSidebar.classList.add('fullscreen-mobile');
                }
            }
        };
    }
    
    if (rightToggle) {
        rightToggle.setAttribute('aria-label', 'Toggle right sidebar');
        rightToggle.onclick = function() {
            const rightSidebar = document.querySelector('.right-sidebar');
            const isHidden = rightSidebar.classList.contains('hidden');
            
            if (!isHidden) {
                // 当前可见，需要隐藏
                rightSidebar.classList.add('hidden');
                rightSidebar.classList.remove('fullscreen-mobile');
                document.querySelector('.center-content').classList.add('right-hidden');
            } else {
                // 当前隐藏，需要显示
                rightSidebar.classList.remove('hidden');
                document.querySelector('.center-content').classList.remove('right-hidden');
                
                // 小屏幕应用全屏模式
                if (window.isSmallScreen) {
                    rightSidebar.classList.add('fullscreen-mobile');
                }
            }
        };
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

// 确保侧边栏关闭按钮在全屏模式下可点击
function setupFullscreenSidebarCloseButtons() {
    const style = document.createElement('style');
    style.textContent = `
        .fullscreen-mobile::before {
            content: '←';
            position: absolute;
            top: 10px;
            right: 10px;
            width: 36px;
            height: 36px;
            background-color: #333;
            color: white;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            font-size: 18px;
            z-index: 95;
        }
    `;
    document.head.appendChild(style);
    
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