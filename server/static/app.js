// 排行榜页面 JavaScript

const REFRESH_INTERVAL = 10; // 刷新间隔（秒）
let countdown = REFRESH_INTERVAL;
let countdownTimer = null;
let refreshTimer = null;

// 格式化游戏时长（毫秒 -> MM:SS）
function formatDuration(ms) {
    const totalSeconds = Math.floor(ms / 1000);
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
}

// 格式化日期（ISO -> M/D）
function formatDate(isoString) {
    const date = new Date(isoString);
    return `${date.getMonth() + 1}/${date.getDate()}`;
}

// 显示/隐藏元素
function showElement(id) {
    document.getElementById(id).style.display = '';
}

function hideElement(id) {
    document.getElementById(id).style.display = 'none';
}

// 获取排行榜数据
async function fetchLeaderboard() {
    hideElement('error');
    hideElement('empty');
    hideElement('leaderboard');
    showElement('loading');

    try {
        const response = await fetch('/api/leaderboard?limit=50');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        const leaderboard = data.leaderboard || [];

        hideElement('loading');

        if (leaderboard.length === 0) {
            showElement('empty');
        } else {
            renderLeaderboard(leaderboard);
            showElement('leaderboard');
        }

        // 重置倒计时
        resetCountdown();

    } catch (error) {
        console.error('Failed to fetch leaderboard:', error);
        hideElement('loading');
        showElement('error');
    }
}

// 渲染排行榜
function renderLeaderboard(data) {
    const tbody = document.getElementById('leaderboard-body');
    tbody.innerHTML = '';

    data.forEach((entry, index) => {
        const rank = index + 1;
        const tr = document.createElement('tr');

        // 为前三名添加特殊样式
        if (rank === 1) tr.className = 'rank-1';
        else if (rank === 2) tr.className = 'rank-2';
        else if (rank === 3) tr.className = 'rank-3';

        tr.innerHTML = `
            <td>${rank}</td>
            <td>${escapeHtml(entry.name || '未知')}</td>
            <td>${escapeHtml(entry.employee_id || '-')}</td>
            <td>${entry.score || 0}</td>
            <td>${formatDuration(entry.game_duration || 0)}</td>
            <td>${entry.created_at ? formatDate(entry.created_at) : '-'}</td>
        `;

        tbody.appendChild(tr);
    });
}

// HTML 转义防止 XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 重置倒计时
function resetCountdown() {
    countdown = REFRESH_INTERVAL;
    updateCountdownDisplay();
}

// 更新倒计时显示
function updateCountdownDisplay() {
    document.getElementById('countdown').textContent = countdown;
}

// 开始倒计时
function startCountdown() {
    // 清除已有的定时器
    if (countdownTimer) clearInterval(countdownTimer);
    if (refreshTimer) clearTimeout(refreshTimer);

    countdownTimer = setInterval(() => {
        countdown--;
        updateCountdownDisplay();

        if (countdown <= 0) {
            fetchLeaderboard();
        }
    }, 1000);
}

// 手动刷新
function manualRefresh() {
    const btn = document.getElementById('refresh-btn');
    btn.disabled = true;
    btn.textContent = '刷新中...';

    fetchLeaderboard().finally(() => {
        btn.disabled = false;
        btn.textContent = '立即刷新';
    });
}

// 页面加载时初始化
document.addEventListener('DOMContentLoaded', () => {
    fetchLeaderboard();
    startCountdown();
});

// 页面可见性变化时处理
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        // 页面隐藏时停止倒计时
        if (countdownTimer) {
            clearInterval(countdownTimer);
            countdownTimer = null;
        }
    } else {
        // 页面显示时重新获取数据并开始倒计时
        fetchLeaderboard();
        startCountdown();
    }
});
