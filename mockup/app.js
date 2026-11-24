// WM Workbench - Complete System Navigation & State Management
// All 14 screens with full interactions

const AppState = {
    currentScreen: 'my-day',
    mode: 'LIVE',
    selectedClient: null,
    workflowStage: 'rank.clients',
    correlationId: '8f21a4b2',
    consentGiven: false,
    briefApproved: false,
    reviewApproved: false,
    
    clients: [
        {
            id: 'wong',
            initials: 'KW',
            name: 'Kenneth Wong',
            aum: 'HKD 45.2M',
            priority: 1,
            previousRank: 4,
            reason: 'OPPORTUNITY — Rebalancing',
            reasonType: 'opportunity',
            signal: 'Portfolio drifted 6% from target allocation',
            conversations: [
                { date: '15 Oct 2024', topic: 'Discussed quarterly rebalancing preferences — prefers gradual adjustments' },
                { date: '22 Sep 2024', topic: 'Expressed interest in Hong Kong tech sector exposure' },
                { date: '10 Aug 2024', topic: 'Risk tolerance review — confirmed moderate growth strategy' }
            ],
            anticipatedNeeds: [
                'Rebalancing discussion triggered by 6% portfolio drift',
                'Tech sector opportunities (mentioned interest 22 Sep)',
                'Q1 2026 performance review preparation'
            ],
            brief: {
                portfolio: 'AUM HKD 45.2M. Equities 68% (target 62%), Fixed Income 26% (target 30%), Cash 6% (target 8%)',
                changes: 'HSBC Holdings +2.3% increased position to 7.2% (was 5.8%). Drift: 6 percentage points.',
                interactions: 'Last meeting 15 Oct 2024. Open action: Review rebalancing options.',
                news: 'HSBC Holdings reports strong Q3 earnings, upgrades guidance',
                agenda: 'Discuss rebalancing options aligned to stated preferences\nReview Hong Kong tech sector opportunities'
            }
        },
        {
            id: 'rahman',
            initials: 'AR',
            name: 'Ahmad Rahman',
            aum: 'SGD 32.8M',
            priority: 2,
            previousRank: 2,
            reason: 'SCHEDULED — Annual Review',
            reasonType: 'scheduled',
            signal: 'Annual review meeting today 13:00 — Faith-based investing focus',
            conversations: [
                { date: '15 Sep 2024', topic: 'Annual review scheduled — requested zakat calculation' },
                { date: '03 Aug 2024', topic: 'Discussed sustainable sukuk opportunities' }
            ],
            anticipatedNeeds: [
                'Annual zakat calculation with documentation',
                'Shariah compliance verification',
                'Sustainable sukuk opportunities'
            ]
        },
        {
            id: 'tan',
            initials: 'TF',
            name: 'Tan Family Office',
            aum: 'SGD 120.5M · 7 entities',
            priority: 3,
            previousRank: 3,
            reason: 'MULTI-GENERATIONAL — Quarterly Review',
            reasonType: 'family',
            signal: 'Family review meeting 15:30 — 4 family members attending',
            conversations: [
                { date: '08 Aug 2024', topic: 'Succession planning discussion with patriarch and son' },
                { date: '15 May 2024', topic: 'Requested consolidated reporting across all entities' }
            ],
            anticipatedNeeds: [
                'Consolidated view across 7 entities',
                'Individual performance breakdowns',
                'Succession planning update'
            ]
        }
    ]
};

// Navigation between screens
function navigateTo(screenId, clientId = null) {
    console.log('Navigating to:', screenId, clientId);
    
    // Hide all screens
    document.querySelectorAll('.screen').forEach(screen => {
        screen.classList.remove('active');
    });
    
    // Update state
    AppState.currentScreen = screenId;
    if (clientId) {
        AppState.selectedClient = AppState.clients.find(c => c.id === clientId);
    }
    
    // Show target screen
    const targetScreen = document.getElementById(screenId);
    if (targetScreen) {
        targetScreen.classList.add('active');
        
        // Load screen-specific data
        if (screenId === 'client-brief' && AppState.selectedClient) {
            loadClientBrief();
        } else if (screenId === 'meeting-review' && AppState.selectedClient) {
            loadMeetingReview();
        }
        
        // Update workflow stage
        updateWorkflowStage(screenId);
    }
    
    // Scroll to top
    window.scrollTo(0, 0);
}

// Update workflow breadcrumb
function updateWorkflowStage(screenId) {
    const stageMap = {
        'my-day': 'rank.clients',
        'client-brief': 'brief.generate',
        'consent-banner': 'meeting.capture',
        'meeting-review': 'review.approve',
        'outreach': 'outreach.draft'
    };
    
    AppState.workflowStage = stageMap[screenId] || AppState.workflowStage;
    
    // Update UI
    const stages = document.querySelectorAll('.workflow-stage');
    stages.forEach(stage => {
        stage.classList.remove('active');
        if (stage.dataset.stage === AppState.workflowStage) {
            stage.classList.add('active');
        }
    });
}

// Load client brief screen
function loadClientBrief() {
    const client = AppState.selectedClient;
    if (!client || !client.brief) return;
    
    document.getElementById('brief-client-name').textContent = client.name;
    document.getElementById('brief-client-aum').textContent = client.aum;
    document.getElementById('brief-portfolio').textContent = client.brief.portfolio;
    document.getElementById('brief-changes').textContent = client.brief.changes;
    document.getElementById('brief-interactions').textContent = client.brief.interactions;
    document.getElementById('brief-news').textContent = client.brief.news;
    document.getElementById('brief-agenda').value = client.brief.agenda;
}

// Load meeting review screen
function loadMeetingReview() {
    const client = AppState.selectedClient;
    if (!client) return;
    
    document.getElementById('review-client-name').textContent = client.name;
}

// Approve brief (Gate 1)
function approveBrief() {
    AppState.briefApproved = true;
    showToast('Brief approved successfully', 'success');
    
    setTimeout(() => {
        navigateTo('consent-banner', AppState.selectedClient.id);
    }, 1000);
}

// Consent actions (Gate 2)
function acceptConsent() {
    AppState.consentGiven = true;
    showToast('Consent accepted - Recording started', 'success');
    
    setTimeout(() => {
        navigateTo('meeting-review', AppState.selectedClient.id);
    }, 1500);
}

function declineConsent() {
    AppState.consentGiven = false;
    showToast('Consent declined - Manual notes only', 'warning');
    
    setTimeout(() => {
        navigateTo('meeting-review', AppState.selectedClient.id);
    }, 1500);
}

// Approve meeting outcomes (Gate 3 - The Decisive Approval)
function approveReview() {
    AppState.reviewApproved = true;
    showToast('All meeting outcomes approved - CRM updates queued', 'success');
    
    // Simulate workflow completion
    setTimeout(() => {
        showToast('Loop closed - Priority list updated', 'success');
    }, 2000);
    
    setTimeout(() => {
        navigateTo('my-day');
    }, 3500);
}

// Show overlay drawer
function showDrawer(drawerId) {
    const drawer = document.getElementById(drawerId);
    if (drawer) {
        drawer.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
}

// Close overlay drawer
function closeDrawer(drawerId) {
    const drawer = document.getElementById(drawerId);
    if (drawer) {
        drawer.classList.remove('active');
        document.body.style.overflow = '';
    }
}

// Toast notifications
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    
    document.body.appendChild(toast);
    
    setTimeout(() => toast.classList.add('show'), 100);
    
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Initialize on load
document.addEventListener('DOMContentLoaded', () => {
    console.log('WM Workbench System Initialized');
    
    // Update clock
    setInterval(updateClock, 1000);
    updateClock();
    
    // Set initial screen
    navigateTo('my-day');
});

// Update SGT clock
function updateClock() {
    const now = new Date();
    const sgtTime = new Date(now.toLocaleString('en-US', { timeZone: 'Asia/Singapore' }));
    const timeString = sgtTime.toLocaleTimeString('en-SG', { 
        hour: '2-digit', 
        minute: '2-digit', 
        second: '2-digit'
    });
    
    const clockElements = document.querySelectorAll('.clock-time');
    clockElements.forEach(el => el.textContent = timeString + ' SGT');
}

// Export for global access
window.AppState = AppState;
window.navigateTo = navigateTo;
window.showDrawer = showDrawer;
window.closeDrawer = closeDrawer;
window.approveBrief = approveBrief;
window.acceptConsent = acceptConsent;
window.declineConsent = declineConsent;
window.approveReview = approveReview;
