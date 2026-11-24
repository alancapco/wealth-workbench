// Capco WM Workbench MVP - Interactive Mockup
// Application logic for clickable hi-fi prototype

// State management
const appState = {
    currentView: 'myDayHome',
    currentClient: null,
    mode: 'live',
    workflows: {},
    drawerOpen: null
};

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    console.log('Capco WM Workbench initialized');
    updateClock();
    setInterval(updateClock, 1000);

    // Simulate market event after 2 seconds
    setTimeout(() => {
        showMarketEvent();
    }, 2000);
});

// Clock update
function updateClock() {
    const now = new Date();
    const timeStr = now.toLocaleTimeString('en-SG', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false,
        timeZone: 'Asia/Singapore'
    });

    const modeDetail = document.querySelector('.mode-detail');
    if (modeDetail) {
        modeDetail.textContent = `Market data • SGT ${timeStr}`;
    }
}

// Show market event banner
function showMarketEvent() {
    const banner = document.getElementById('marketEventBanner');
    if (banner) {
        banner.style.animation = 'slideInRight 0.5s ease-out';
    }
}

// Open market event drawer
function openMarketDrawer() {
    const drawer = document.getElementById('marketDrawer');
    if (drawer) {
        drawer.classList.remove('hidden');
        appState.drawerOpen = 'marketDrawer';
    }
}

// Close drawer
function closeDrawer(drawerId) {
    const drawer = document.getElementById(drawerId);
    if (drawer) {
        drawer.classList.add('hidden');
        appState.drawerOpen = null;
    }
}

// Open source drawer (CMP-02)
function openSourceDrawer(sourceId) {
    // Create and show source drawer with evidence
    const sourceData = {
        'ranking-v1': {
            title: 'Ranking Engine v1.2',
            timestamp: '10:14:20 SGT',
            details: [
                { label: 'Algorithm', value: 'Risk-Opportunity-Retention Weighted' },
                { label: 'Version', value: '1.2.0' },
                { label: 'Rule Pack', value: 'Standard Banking v3' },
                { label: 'Confidence', value: '98.5%' },
                { label: 'Source', value: 'Copilot Core Orchestration' }
            ]
        }
    };

    const data = sourceData[sourceId];
    if (data) {
        alert(`Source Details:\n\n${data.title}\n${data.timestamp}\n\n${data.details.map(d => `${d.label}: ${d.value}`).join('\n')}`);
    }
}

// Open client workspace (SCR-03)
function openClientWorkspace(clientId) {
    const clients = {
        'wong': {
            name: 'Kenneth Wong',
            aum: 'HKD 45.2M',
            avatar: 'WK',
            gradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            brief: generateBrief('wong')
        },
        'rahman': {
            name: 'Ahmad Rahman',
            aum: 'SGD 32.8M',
            avatar: 'AR',
            gradient: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
            brief: generateBrief('rahman')
        }
    };

    const client = clients[clientId];
    if (!client) return;

    appState.currentClient = clientId;

    // Hide My Day, show Client Workspace
    document.getElementById('myDayHome').classList.add('hidden');
    const workspace = document.getElementById('clientWorkspace');
    workspace.classList.remove('hidden');

    // Render client brief
    workspace.innerHTML = generateClientWorkspaceHTML(client);

    // Reinitialize Lucide icons
    lucide.createIcons();
}

// Generate client brief (Five-section brief - SCR-03)
function generateBrief(clientId) {
    const briefs = {
        'wong': {
            sections: [
                {
                    title: 'Portfolio Overview',
                    status: 'fresh',
                    asOf: '10:14:18 SGT',
                    source: 'Portfolio Management System',
                    content: `Current AUM: HKD 45.2M (-2.3% MTD)\n\nAsset Allocation:\n• Equities: 58% (Target: 55%)\n• Fixed Income: 28% (Target: 30%)\n• Cash: 14% (Target: 15%)\n\n⚠️ HSBC Holdings position: 18% (Target: 12%) - 6% drift`,
                    confidence: 'high'
                },
                {
                    title: 'Market Context',
                    status: 'live',
                    asOf: '10:14:18 SGT',
                    source: 'Reuters Market Data',
                    content: `HSBC Holdings (0005.HK)\nPrice: HKD 62.45 (+2.3%)\nVolume: Above average\n\nHang Seng Index: +1.8%\nFinancials sector: Leading gains`,
                    confidence: 'high'
                },
                {
                    title: 'Risk Assessment',
                    status: 'fresh',
                    asOf: '10:14:19 SGT',
                    source: 'Risk Engine v2.1',
                    content: `Concentration Risk: ELEVATED\n• Single position exceeds target by 6%\n• Sector concentration (Financials): 25%\n\nRecommendation: Consider rebalancing\nPriority: Medium-High`,
                    confidence: 'high'
                },
                {
                    title: 'Client Preferences',
                    status: 'fresh',
                    asOf: '15 Oct 2024',
                    source: 'Client Memory (D5)',
                    content: `Investment Style: Moderate growth\nRisk Tolerance: Medium\nLiquidity Need: Low\n\nRecent Preferences:\n• Prefers Hong Kong equities\n• Wants quarterly rebalancing\n• Mentioned interest in tech sector (last meeting)`,
                    confidence: 'high'
                },
                {
                    title: 'Suggested Actions',
                    status: 'proposed',
                    asOf: '10:14:20 SGT',
                    source: 'Copilot Core',
                    content: `1. Discuss HSBC position rebalancing\n2. Review allocation to bring equities to 55%\n3. Consider tech sector opportunities (client expressed interest)\n4. Schedule follow-up for Q4 review`,
                    confidence: 'medium',
                    editable: true
                }
            ]
        },
        'rahman': {
            sections: [
                {
                    title: 'Portfolio Overview',
                    status: 'fresh',
                    asOf: '08:30:00 SGT',
                    source: 'Portfolio Management System',
                    content: `Current AUM: SGD 32.8M (+1.2% MTD)\n\nAsset Allocation:\n• Equities: 45% (Shariah-compliant)\n• Sukuk: 35%\n• Cash: 20%\n\nAll holdings screened to client's stated Islamic preferences.`,
                    confidence: 'high'
                },
                {
                    title: 'Faith-Based Investing',
                    status: 'fresh',
                    asOf: '08:30:15 SGT',
                    source: 'Shariah Screening Engine',
                    content: `⭐ All holdings meet Shariah compliance criteria\n\nScreening Standard: AAOIFI\nLast Review: 1 Nov 2024\nNext Review: 1 Feb 2025\n\n📋 This is an estimate for discussion, not a fatwa.`,
                    confidence: 'high'
                },
                {
                    title: 'Zakat Estimate',
                    status: 'fresh',
                    asOf: '08:30:20 SGT',
                    source: 'Zakat Calculator v1.0',
                    content: `Estimated Zakatable Assets: SGD 28.5M\nEstimated Zakat (2.5%): SGD 712,500\n\nHijri Year End: 15 Ramadan 1446\nGregorian Equivalent: ~15 March 2025\n\n📋 Estimate for discussion only. Client should consult scholar.`,
                    confidence: 'medium'
                },
                {
                    title: 'Client Preferences',
                    status: 'fresh',
                    asOf: '15 Sep 2024',
                    source: 'Client Memory (D5)',
                    content: `Faith-Based: Islamic investment principles\nRisk Tolerance: Conservative\nPhilanthropy: Active zakat payer\n\nRecent Notes:\n• Annual review scheduled today\n• Interested in sustainable sukuk\n• Family: Wife and 2 children`,
                    confidence: 'high'
                },
                {
                    title: 'Suggested Agenda',
                    status: 'proposed',
                    asOf: '08:30:25 SGT',
                    source: 'Copilot Core',
                    content: `1. Review annual performance\n2. Discuss zakat estimate and timing\n3. Present new sustainable sukuk opportunities\n4. Confirm Shariah screening preferences\n5. Update beneficiary information`,
                    confidence: 'medium',
                    editable: true
                }
            ]
        }
    };

    return briefs[clientId];
}

// Generate client workspace HTML
function generateClientWorkspaceHTML(client) {
    const sections = client.brief.sections.map((section, idx) => `
        <div class="brief-section" data-section="${idx}">
            <div class="section-header-row">
                <h3>${section.title}</h3>
                <div class="section-chips">
                    <span class="source-chip ${section.status}" onclick="openSourceDrawer('section-${idx}')">
                        <i data-lucide="${getStatusIcon(section.status)}"></i>
                        ${section.source} • ${section.asOf}
                    </span>
                    ${section.confidence ? `<span class="confidence-badge ${section.confidence}">${section.confidence.toUpperCase()}</span>` : ''}
                </div>
            </div>
            <div class="section-content ${section.editable ? 'editable' : ''}">
                ${formatContent(section.content)}
            </div>
            ${section.editable ? `
                <div class="section-actions">
                    <button class="btn-secondary" onclick="editSection(${idx})">
                        <i data-lucide="edit-2"></i>
                        Edit
                    </button>
                    <button class="btn-primary" onclick="approveSection(${idx})">
                        <i data-lucide="check"></i>
                        Approve
                    </button>
                </div>
            ` : ''}
        </div>
    `).join('');

    return `
        <div class="workspace-nav">
            <button class="nav-back" onclick="backToMyDay()">
                <i data-lucide="arrow-left"></i>
                Back to My Day
            </button>
            <div class="workspace-breadcrumb">
                <span>My Day</span>
                <i data-lucide="chevron-right"></i>
                <span>${client.name}</span>
            </div>
        </div>

        <div class="client-header">
            <div class="client-avatar-large" style="background: ${client.gradient}">
                <span>${client.avatar}</span>
            </div>
            <div class="client-header-info">
                <h1>${client.name}</h1>
                <p class="client-aum">${client.aum} AUM</p>
            </div>
            <button class="btn-primary" onclick="startMeeting()">
                <i data-lucide="video"></i>
                Start Meeting
            </button>
        </div>

        <div class="brief-container">
            <div class="brief-header">
                <h2>Pre-Meeting Brief</h2>
                <div class="source-chip" onclick="openSourceDrawer('brief-generation')">
                    <i data-lucide="cpu"></i>
                    Generated by Copilot Core • 10:14:20 SGT
                </div>
            </div>

            <div class="brief-sections">
                ${sections}
            </div>
        </div>
    `;
}

// Helper functions
function getStatusIcon(status) {
    const icons = {
        'fresh': 'check-circle',
        'live': 'activity',
        'proposed': 'lightbulb',
        'stale': 'alert-triangle'
    };
    return icons[status] || 'info';
}

function formatContent(content) {
    return content.split('\n').map(line => {
        if (line.startsWith('•')) {
            return `<div class="bullet-item">${line}</div>`;
        } else if (line.startsWith('⚠️') || line.startsWith('⭐') || line.startsWith('📋')) {
            return `<div class="highlight-item">${line}</div>`;
        } else if (line.trim()) {
            return `<p>${line}</p>`;
        }
        return '';
    }).join('');
}

function backToMyDay() {
    document.getElementById('clientWorkspace').classList.add('hidden');
    document.getElementById('myDayHome').classList.remove('hidden');
    appState.currentClient = null;
}

function editSection(idx) {
    alert(`Edit Section ${idx + 1}\n\nThis would open an inline editor to modify the suggested actions.`);
}

function approveSection(idx) {
    alert(`Section ${idx + 1} Approved\n\nThis action would:\n1. Mark section as approved\n2. Create audit event (C-4)\n3. Enable unified review screen\n\nIn the full demo, this leads to SCR-06.`);
}

function startMeeting() {
    alert('Start Meeting\n\nThis would:\n1. Show consent banner (SCR-07)\n2. Request recording permission\n3. Enable meeting capture\n4. Show recording indicator\n\nIn the full demo, this leads to the meeting workflow.');
}

// Open family entity graph (SCR-09)
function openFamilyGraph(familyId) {
    alert('Family Entity Graph\n\nThis would display:\n• 7-entity family structure\n• Node-level entitlements\n• Consolidated view (SGD 120.5M)\n• Individual entity breakdowns\n• Meeting pack versions per attendee\n\nFeature: SCR-09 (Range moment)');
}

// Demo mode switching (would be on SCR-11 operator console)
function switchMode(newMode) {
    const modeChip = document.getElementById('modeChip');
    const indicator = modeChip.querySelector('.mode-indicator');

    if (newMode === 'replay') {
        indicator.textContent = 'REPLAY';
        indicator.classList.remove('live');
        indicator.classList.add('replay');
        appState.mode = 'replay';

        // Show announcement banner
        showStatusBanner('Switching to REPLAY — recorded 09:58', 2500);
    } else {
        indicator.textContent = 'LIVE';
        indicator.classList.remove('replay');
        indicator.classList.add('live');
        appState.mode = 'live';

        showStatusBanner('Switching to LIVE mode', 2500);
    }
}

function showStatusBanner(message, duration) {
    const banner = document.createElement('div');
    banner.className = 'status-banner';
    banner.textContent = message;
    banner.style.cssText = `
        position: fixed;
        top: 72px;
        left: 50%;
        transform: translateX(-50%);
        padding: 16px 32px;
        background: #FEF3C7;
        border: 2px solid #F59E0B;
        border-radius: 8px;
        font-weight: 600;
        z-index: 2000;
        animation: fadeIn 0.3s ease-out;
    `;

    document.body.appendChild(banner);

    setTimeout(() => {
        banner.remove();
    }, duration);
}

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
    // ESC to close drawer
    if (e.key === 'Escape' && appState.drawerOpen) {
        closeDrawer(appState.drawerOpen);
    }

    // B to go back to My Day
    if (e.key === 'b' && appState.currentClient) {
        backToMyDay();
    }
});
