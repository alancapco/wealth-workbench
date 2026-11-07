/**
 * RM Workbench MVP - Component JavaScript
 * Handles interactive components and state management
 */

/* ============================================
   Demo State Management
   ============================================ */

class DemoState {
    constructor() {
        this.state = {
            mode: 'LIVE', // 'LIVE' | 'REPLAY'
            scenario: 'S1', // 'S1' | 'S2' | 'S3' | 'S4'
            currentScreen: 'SCR-02',
            workflowStage: 'rank.clients',
            correlationId: this.generateCorrelationId(),
            feedAge: 3, // seconds
            feedStatus: 'fresh', // 'fresh' | 'stale' | 'outage'
            blockedAttempts: 0,
            integrityStatus: 'verified',
            approvalGates: {
                gate1_brief: false,
                gate2_consent: false,
                gate3_review: false
            },
            theme: 'dark' // 'light' | 'dark'
        };
        
        this.listeners = [];
        this.init();
    }
    
    init() {
        // Initialize theme from localStorage or default to dark
        const savedTheme = localStorage.getItem('rm-workbench-theme') || 'dark';
        this.setState({ theme: savedTheme });
        this.applyTheme(savedTheme);
        
        // Update system time every second
        this.updateSystemTime();
        setInterval(() => this.updateSystemTime(), 1000);
        
        // Simulate feed age increase (for demo purposes)
        setInterval(() => {
            if (this.state.mode === 'LIVE') {
                this.setState({ 
                    feedAge: this.state.feedAge + 1 
                });
                this.updateFeedStatus();
            }
        }, 1000);
    }
    
    generateCorrelationId() {
        return Array.from({ length: 8 }, () => 
            Math.floor(Math.random() * 16).toString(16)
        ).join('');
    }
    
    setState(updates) {
        this.state = { ...this.state, ...updates };
        this.notifyListeners();
        this.persistState();
    }
    
    getState() {
        return { ...this.state };
    }
    
    subscribe(callback) {
        this.listeners.push(callback);
        return () => {
            this.listeners = this.listeners.filter(cb => cb !== callback);
        };
    }
    
    notifyListeners() {
        this.listeners.forEach(callback => callback(this.state));
    }
    
    persistState() {
        localStorage.setItem('rm-workbench-state', JSON.stringify(this.state));
    }
    
    updateSystemTime() {
        const now = new Date();
        const timeString = now.toLocaleTimeString('en-SG', { 
            hour12: false, 
            timeZone: 'Asia/Singapore',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
        
        const timeElements = document.querySelectorAll('#systemTime');
        timeElements.forEach(el => {
            el.textContent = `${timeString} SGT`;
        });
    }
    
    updateFeedStatus() {
        const age = this.state.feedAge;
        let status = 'fresh';
        
        if (age > 120) {
            status = 'outage';
        } else if (age > 30) {
            status = 'stale';
        }
        
        if (status !== this.state.feedStatus) {
            this.setState({ feedStatus: status });
            this.showFeedStatusBanner(status);
        }
    }
    
    showFeedStatusBanner(status) {
        if (status === 'stale') {
            showStatusBanner({
                type: 'warning',
                title: 'Feed Stale',
                message: `Last tick 09:58:14 · age ${this.state.feedAge}s · Market section may be affected`
            });
        } else if (status === 'outage') {
            showStatusBanner({
                type: 'error',
                title: 'Feed Outage',
                message: 'Market data unavailable · Last confirmed state preserved'
            });
        }
    }
    
    toggleTheme() {
        const newTheme = this.state.theme === 'light' ? 'dark' : 'light';
        this.setState({ theme: newTheme });
        this.applyTheme(newTheme);
        localStorage.setItem('rm-workbench-theme', newTheme);
    }
    
    applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
    }
    
    switchMode(mode, recordedTime = null) {
        const announcement = mode === 'REPLAY' 
            ? `Switching to REPLAY — recorded ${recordedTime || '09:58'}`
            : 'Switching to LIVE mode';
            
        showStatusBanner({
            type: 'info',
            title: 'Mode Switch',
            message: announcement,
            duration: 3000
        });
        
        setTimeout(() => {
            this.setState({ 
                mode,
                feedAge: mode === 'REPLAY' ? 0 : this.state.feedAge
            });
        }, 500);
    }
    
    approveGate(gateId) {
        this.setState({
            approvalGates: {
                ...this.state.approvalGates,
                [gateId]: true
            }
        });
        
        showStatusBanner({
            type: 'success',
            title: 'Approved',
            message: `Gate ${gateId} approved successfully`,
            duration: 2500
        });
    }
    
    incrementBlockedAttempts() {
        this.setState({
            blockedAttempts: this.state.blockedAttempts + 1
        });
        
        showStatusBanner({
            type: 'error',
            title: 'Action Blocked',
            message: 'Automated action prevented by human approval requirement',
            duration: 3000
        });
    }
}

// Global state instance
const demoState = new DemoState();

/* ============================================
   CMP-02: Source Drawer
   ============================================ */

class SourceDrawer {
    constructor() {
        this.isOpen = false;
        this.currentData = null;
        this.init();
    }
    
    init() {
        // Create drawer HTML if not exists
        if (!document.getElementById('sourceDrawer')) {
            this.createDrawer();
        }
        
        this.drawer = document.getElementById('sourceDrawer');
        this.backdrop = document.getElementById('sourceDrawerBackdrop');
        
        // Event listeners
        this.backdrop?.addEventListener('click', () => this.close());
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isOpen) {
                this.close();
            }
        });
    }
    
    createDrawer() {
        const drawerHTML = `
            <div id="sourceDrawerBackdrop" class="source-drawer__backdrop"></div>
            <div id="sourceDrawer" class="source-drawer">
                <div class="source-drawer__header">
                    <div>
                        <h3 class="source-drawer__title" id="drawerTitle">Source Details</h3>
                        <p class="source-drawer__subtitle" id="drawerSubtitle"></p>
                    </div>
                    <button class="source-drawer__close" aria-label="Close drawer" onclick="sourceDrawer.close()">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <line x1="18" y1="6" x2="6" y2="18"></line>
                            <line x1="6" y1="6" x2="18" y2="18"></line>
                        </svg>
                    </button>
                </div>
                <div class="source-drawer__body" id="drawerBody"></div>
                <div class="source-drawer__footer">
                    <button class="btn-outline" onclick="sourceDrawer.close()">Close</button>
                </div>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', drawerHTML);
    }
    
    open(data) {
        this.currentData = data;
        this.render(data);
        
        // Open drawer
        setTimeout(() => {
            this.drawer.classList.add('source-drawer--open');
            this.backdrop.classList.add('source-drawer__backdrop--visible');
            this.isOpen = true;
            
            // Focus trap
            this.drawer.querySelector('.source-drawer__close')?.focus();
        }, 10);
    }
    
    close() {
        this.drawer.classList.remove('source-drawer--open');
        this.backdrop.classList.remove('source-drawer__backdrop--visible');
        this.isOpen = false;
    }
    
    render(data) {
        const titleEl = document.getElementById('drawerTitle');
        const subtitleEl = document.getElementById('drawerSubtitle');
        const bodyEl = document.getElementById('drawerBody');
        
        titleEl.textContent = data.title || 'Source Details';
        subtitleEl.textContent = data.sourceKind || '';
        
        let bodyHTML = '<div class="source-drawer__section">';
        bodyHTML += '<h4 class="source-drawer__section-title">Provenance</h4>';
        
        if (data.fields) {
            data.fields.forEach(field => {
                bodyHTML += `
                    <div class="source-drawer__field">
                        <div class="source-drawer__field-label">${field.label}</div>
                        <div class="source-drawer__field-value">${field.value}</div>
                    </div>
                `;
            });
        }
        
        bodyHTML += '</div>';
        
        if (data.evidence) {
            bodyHTML += '<div class="source-drawer__section">';
            bodyHTML += '<h4 class="source-drawer__section-title">Evidence</h4>';
            bodyHTML += `<p style="font-size: 0.875rem; line-height: 1.6;">${data.evidence}</p>`;
            bodyHTML += '</div>';
        }
        
        bodyEl.innerHTML = bodyHTML;
    }
}

const sourceDrawer = new SourceDrawer();

/* ============================================
   CMP-16: Status Banner / Toast
   ============================================ */

function showStatusBanner(options) {
    const {
        type = 'info',
        title,
        message,
        duration = 2500
    } = options;
    
    // Create banner if not exists
    let banner = document.getElementById('statusBanner');
    if (!banner) {
        banner = document.createElement('div');
        banner.id = 'statusBanner';
        banner.className = 'status-banner';
        banner.setAttribute('role', 'status');
        banner.setAttribute('aria-live', 'polite');
        document.body.appendChild(banner);
    }
    
    const icons = {
        info: 'ℹ',
        success: '✓',
        warning: '⚠',
        error: '⊘',
        blocked: '⊘'
    };
    
    banner.className = `status-banner status-banner--${type}`;
    banner.innerHTML = `
        <div class="status-banner__content">
            <div class="status-banner__icon">${icons[type] || icons.info}</div>
            <div class="status-banner__body">
                <div class="status-banner__title">${title}</div>
                <div class="status-banner__message">${message}</div>
            </div>
            <button class="status-banner__close" onclick="this.parentElement.parentElement.classList.remove('status-banner--visible')" aria-label="Close notification">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="18" y1="6" x2="6" y2="18"></line>
                    <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
            </button>
        </div>
    `;
    
    // Show banner
    setTimeout(() => {
        banner.classList.add('status-banner--visible');
    }, 10);
    
    // Auto-hide after duration (unless error/blocked)
    if (type !== 'error' && type !== 'blocked' && duration > 0) {
        setTimeout(() => {
            banner.classList.remove('status-banner--visible');
        }, duration);
    }
}

/* ============================================
   Evidence Chip Click Handlers
   ============================================ */

function openEvidenceChip(chipData) {
    const drawerData = {
        title: chipData.title || 'Source Evidence',
        sourceKind: chipData.sourceKind,
        fields: [
            { label: 'Source Type', value: chipData.sourceKind || 'Unknown' },
            { label: 'As Of', value: chipData.asOf || 'N/A' },
            { label: 'Timestamp', value: chipData.timestamp || 'N/A' },
            { label: 'Confidence', value: chipData.confidence || 'N/A' },
            { label: 'Correlation ID', value: chipData.correlationId || demoState.getState().correlationId }
        ],
        evidence: chipData.evidence || 'Full provenance chain available for audit.'
    };
    
    sourceDrawer.open(drawerData);
}

/* ============================================
   Approval Bar Handlers
   ============================================ */

function handleApproval(gateId) {
    const state = demoState.getState();
    
    // Check if already approved
    if (state.approvalGates[gateId]) {
        showStatusBanner({
            type: 'info',
            title: 'Already Approved',
            message: `Gate ${gateId} was already approved`,
            duration: 2500
        });
        return;
    }
    
    // Show confirmation
    const btn = event.target;
    btn.disabled = true;
    btn.textContent = 'Approving...';
    
    // Simulate approval delay
    setTimeout(() => {
        demoState.approveGate(gateId);
        btn.classList.add('btn-approve--success');
        btn.textContent = 'Approved ✓';
        
        // Update timestamp
        const now = new Date();
        const timestamp = now.toLocaleTimeString('en-SG', {
            hour12: false,
            timeZone: 'Asia/Singapore'
        });
        
        const timestampEl = btn.closest('.approval-bar')?.querySelector('.approval-bar__timestamp');
        if (timestampEl) {
            timestampEl.textContent = `Approved at ${timestamp} SGT`;
        }
    }, 800);
}

/* ============================================
   Navigation Helpers
   ============================================ */

function navigateTo(screen) {
    demoState.setState({ currentScreen: screen });
    
    // In a real implementation, this would handle screen transitions
    console.log(`Navigating to ${screen}`);
    
    showStatusBanner({
        type: 'info',
        title: 'Navigation',
        message: `Navigating to ${screen}`,
        duration: 1500
    });
}

function openClientDetail(clientId) {
    navigateTo('SCR-03');
    demoState.setState({ 
        workflowStage: 'brief.generate',
        correlationId: demoState.generateCorrelationId()
    });
}

/* ============================================
   Theme Toggle
   ============================================ */

function toggleTheme() {
    demoState.toggleTheme();
}

/* ============================================
   Initialize on DOM Ready
   ============================================ */

document.addEventListener('DOMContentLoaded', () => {
    console.log('RM Workbench MVP initialized');
    console.log('Current state:', demoState.getState());
    
    // Subscribe to state changes
    demoState.subscribe((state) => {
        console.log('State updated:', state);
        updateUIFromState(state);
    });
    
    // Add theme toggle button to header if not exists
    addThemeToggle();
    
    // Initialize Lucide icons if available
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
});

function updateUIFromState(state) {
    // Update mode chips
    const modeChips = document.querySelectorAll('.mode-chip, [data-mode-chip]');
    modeChips.forEach(chip => {
        chip.className = chip.className.replace(/mode-chip--\w+/, '');
        chip.classList.add(`mode-chip--${state.mode.toLowerCase()}`);
        chip.textContent = state.mode === 'LIVE' 
            ? '● LIVE · Market Data · as-of 09:58:14 SGT'
            : '⏵ REPLAY — recorded 09:58';
    });
    
    // Update health bar
    const feedAgeEl = document.getElementById('feedAge');
    if (feedAgeEl) {
        feedAgeEl.textContent = `${state.feedAge}s`;
        
        // Update status
        const feedStatusEl = document.getElementById('feedStatus');
        if (feedStatusEl) {
            feedStatusEl.className = `state-badge state-badge--${state.feedStatus === 'fresh' ? 'ready' : state.feedStatus === 'stale' ? 'warning' : 'error'}`;
            feedStatusEl.textContent = state.feedStatus.toUpperCase();
        }
    }
    
    // Update blocked attempts counter
    const blockedCountEl = document.getElementById('blockedCount');
    if (blockedCountEl) {
        blockedCountEl.textContent = state.blockedAttempts;
    }
}

function addThemeToggle() {
    const headerRight = document.querySelector('.header-right');
    if (headerRight && !document.getElementById('themeToggle')) {
        const toggleHTML = `
            <button 
                id="themeToggle" 
                class="theme-toggle" 
                onclick="toggleTheme()" 
                aria-label="Toggle dark mode"
                title="Toggle theme">
            </button>
        `;
        headerRight.insertAdjacentHTML('afterbegin', toggleHTML);
    }
}

/* ============================================
   Utility Functions
   ============================================ */

function formatTimestamp(date = new Date()) {
    return date.toLocaleTimeString('en-SG', {
        hour12: false,
        timeZone: 'Asia/Singapore',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
}

function formatCurrency(amount, currency = 'HKD') {
    return new Intl.NumberFormat('en-HK', {
        style: 'currency',
        currency: currency,
        minimumFractionDigits: 1,
        maximumFractionDigits: 1
    }).format(amount);
}

// Export for use in other scripts
window.RMWorkbench = {
    demoState,
    sourceDrawer,
    showStatusBanner,
    openEvidenceChip,
    handleApproval,
    navigateTo,
    openClientDetail,
    toggleTheme
};
