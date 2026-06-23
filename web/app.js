// mihomo-proxy-pool Web GUI

const API = '/api';

// ── Helpers ──

function $(sel) { return document.querySelector(sel); }
function $$(sel) { return document.querySelectorAll(sel); }

function fmtDelay(ms) {
    if (!ms || ms <= 0) return '--';
    return ms < 1000 ? `${ms} ms` : `${(ms / 1000).toFixed(1)} s`;
}

function delayClass(ms) {
    if (!ms || ms <= 0) return '';
    if (ms < 200) return 'good';
    if (ms < 500) return 'medium';
    return 'slow';
}

function delayWidth(ms, max) {
    if (!ms || ms <= 0) return 0;
    return Math.min((ms / max) * 100, 100);
}

function timeAgo(iso) {
    const d = new Date(iso);
    const now = new Date();
    const sec = Math.floor((now - d) / 1000);
    if (sec < 5) return '刚刚';
    if (sec < 60) return `${sec}s 前`;
    if (sec < 3600) return `${Math.floor(sec / 60)}m 前`;
    return `${Math.floor(sec / 3600)}h 前`;
}

function flagEmoji(name) {
    const map = {
        '日本': '🇯🇵', '新加坡': '🇸🇬', '香港': '🇭🇰', '台湾': '🇹🇼',
        '美国': '🇺🇸', '加拿大': '🇨🇦', '德国': '🇩🇪', '英国': '🇬🇧',
        '印度': '🇮🇳', '韩国': '🇰🇷', '法国': '🇫🇷', '荷兰': '🇳🇱',
        '俄罗斯': '🇷🇺', '澳大利亚': '🇦🇺', '巴西': '🇧🇷',
    };
    for (const [key, flag] of Object.entries(map)) {
        if (name.includes(key)) return flag;
    }
    return '🌐';
}

// ── API calls ──

async function fetchJSON(url, opts = {}) {
    const res = await fetch(url, opts);
    if (!res.ok) throw new Error(`${res.status}`);
    return res.json();
}

async function loadStatus() {
    try {
        const data = await fetchJSON(`${API}/status`);
        updateStatusUI(data);

        const health = await fetchJSON(`${API}/health`);
        updateConnBadge(health.mihomo);
    } catch (e) {
        $('#conn-status').className = 'badge badge-dead';
        $('#conn-status').textContent = '● 未连接';
    }
}

async function loadNodes() {
    try {
        const data = await fetchJSON(`${API}/nodes`);
        updateNodesUI(data);
    } catch (e) { /* ignore */ }
}

async function loadHistory() {
    try {
        const data = await fetchJSON(`${API}/history`);
        updateHistoryUI(data);
    } catch (e) { /* ignore */ }
}

async function loadSettings() {
    try {
        const data = await fetchJSON(`${API}/settings`);
        updateSettingsUI(data);
    } catch (e) { /* ignore */ }
}

async function rotateNode() {
    try {
        const btn = $('.current-node-body .btn-primary');
        btn.textContent = '⏳ 切换中...';
        btn.disabled = true;
        const data = await fetchJSON(`${API}/rotate`, { method: 'POST' });
        if (data.ok) {
            await Promise.all([loadStatus(), loadNodes(), loadHistory()]);
        }
    } catch (e) {
        alert('轮转失败: ' + e.message);
    } finally {
        const btn = $('.current-node-body .btn-primary');
        btn.textContent = '🔄 换一个';
        btn.disabled = false;
    }
}

async function switchNode(name) {
    try {
        await fetchJSON(`${API}/switch?name=${encodeURIComponent(name)}`, { method: 'POST' });
        await Promise.all([loadStatus(), loadNodes(), loadHistory()]);
    } catch (e) {
        alert('切换失败: ' + e.message);
    }
}

async function updateStrategy() {
    const val = $('#strategy-select').value;
    await fetchJSON(`${API}/settings`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ strategy: val }),
    });
}

async function toggleAuto() {
    try {
        const data = await fetchJSON(`${API}/auto-rotate`, { method: 'POST' });
        updateAutoToggle(data.auto_running);
        loadStatus();
    } catch (e) {
        alert('操作失败: ' + e.message);
    }
}

async function updateInterval() {
    const val = parseInt($('#interval-input').value) || 300;
    await fetchJSON(`${API}/settings`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ auto_interval: val }),
    });
}

async function updateFilter() {
    const pattern = $('#filter-input').value.trim();
    const mode = $('#filter-mode').value;
    await fetchJSON(`${API}/settings`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filter_pattern: pattern, filter_mode: mode }),
    });
    loadStatus();
    loadNodes();
}

async function updateExclude() {
    const raw = $('#exclude-input').value;
    const keywords = raw.split(',').map(s => s.trim()).filter(Boolean);
    await fetchJSON(`${API}/settings`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ exclude_keywords: keywords }),
    });
    loadNodes();
}

// ── UI Updates ──

function updateConnBadge(ok) {
    const el = $('#conn-status');
    if (ok) {
        el.className = 'badge badge-alive';
        el.textContent = '● 已连接';
    } else {
        el.className = 'badge badge-dead';
        el.textContent = '● 未连接';
    }
}

function updateStatusUI(data) {
    $('#current-name').textContent = data.current || '--';
    $('#node-flag').textContent = flagEmoji(data.current || '');

    if (data.auto_running) {
        $('#auto-badge').style.display = '';
    } else {
        $('#auto-badge').style.display = 'none';
    }

    // show filter scope: "12/27 个节点"
    const total = data.total_nodes || data.pool_size;
    const pool = data.pool_size;
    if (data.filter_pattern) {
        $('#node-count').textContent = `${pool} / ${total} 个节点 (已过滤)`;
    } else {
        $('#node-count').textContent = `${pool} 个节点`;
    }
}

function updateNodesUI(data) {
    const current = data.current;
    const nodes = data.nodes || [];
    $('#node-count').textContent = `${nodes.length} 个节点`;

    if (nodes.length === 0) {
        $('#node-table-body').innerHTML = '<tr><td colspan="5" class="empty-msg">暂无节点 — 请检查订阅 URL 是否已配置</td></tr>';
        return;
    }

    const maxDelay = Math.max(...nodes.map(n => n.delay || 0), 1);

    const rows = nodes.map(n => {
        const isCurrent = n.name === current;
        const cls = isCurrent ? 'current-row' : '';
        const aliveBadge = n.alive
            ? '<span class="badge badge-alive">在线</span>'
            : '<span class="badge badge-dead">离线</span>';
        const barW = delayWidth(n.delay, maxDelay);
        const barCls = delayClass(n.delay);
        const actionBtn = isCurrent
            ? '<span class="badge badge-current">当前</span>'
            : `<button class="btn btn-xs" onclick="switchNode('${n.name.replace(/'/g, "\\'")}')">切换</button>`;

        return `<tr class="${cls}">
            <td><strong>${n.name}</strong></td>
            <td>${n.type}</td>
            <td>
                <span class="delay-bar ${barCls}" style="width:${barW}px"></span>
                ${fmtDelay(n.delay)}
            </td>
            <td>${aliveBadge}</td>
            <td>${actionBtn}</td>
        </tr>`;
    });

    // update current node detail
    const curNode = nodes.find(n => n.name === current);
    if (curNode) {
        $('#current-type').textContent = curNode.type;
        $('#current-delay').textContent = fmtDelay(curNode.delay);
        if (curNode.alive) {
            $('#current-alive').innerHTML = '<span class="badge badge-alive">在线</span>';
        } else {
            $('#current-alive').innerHTML = '<span class="badge badge-dead">离线</span>';
        }
    }

    $('#node-table-body').innerHTML = rows.join('');
}

function updateHistoryUI(data) {
    if (!data || data.length === 0) {
        $('#history-list').innerHTML = '<span class="empty-msg">暂无记录</span>';
        return;
    }
    const items = data.slice(0, 20).map(h => `
        <div class="timeline-item">
            <span class="timeline-dot"></span>
            <span class="timeline-name">${h.name}</span>
            <span class="timeline-time">${timeAgo(h.time)}</span>
        </div>
    `).join('');
    $('#history-list').innerHTML = items;
}

function updateSettingsUI(data) {
    $('#strategy-select').value = data.strategy || 'round-robin';
    $('#interval-input').value = data.auto_interval || 300;
    $('#exclude-input').value = (data.exclude_keywords || []).join(', ');
    $('#filter-input').value = data.filter_pattern || '';
    $('#filter-mode').value = data.filter_mode || 'fuzzy';
    updateAutoToggle(data.auto_running);
}

function updateAutoToggle(running) {
    const btn = $('#auto-toggle');
    if (running) {
        btn.textContent = '关闭';
        btn.className = 'btn btn-sm btn-danger';
    } else {
        btn.textContent = '开启';
        btn.className = 'btn btn-sm';
    }
}

// ── Init ──

async function init() {
    await loadSettings();
    await Promise.all([loadStatus(), loadNodes(), loadHistory()]);
}

// Poll every 15s
setInterval(() => {
    loadStatus();
    loadNodes();
}, 15000);

// Poll history every 30s
setInterval(loadHistory, 30000);

init();
