/**
 * Information architecture — single source of truth for the two-level nav.
 *
 * Grouping follows the RM's actual workflow: start the day → understand the
 * client → engage → prepare and execute advice → analyse the portfolio →
 * administer the platform. Each backend capability has exactly one home here.
 */
export interface NavItem {
  href: string;
  label: string;
  description: string;
}

export interface NavGroup {
  id: string;
  label: string;
  short: string;
  description: string;
  items: NavItem[];
}

export const NAV_GROUPS: NavGroup[] = [
  {
    id: 'day',
    label: 'My Day',
    short: 'Day',
    description: 'Start the book',
    items: [
      { href: '/dashboard', label: 'Morning digest', description: 'Priorities, pipeline and what to prepare' },
    ],
  },
  {
    id: 'book',
    label: 'Client 360',
    short: 'Book',
    description: 'People, households and memory',
    items: [
      { href: '/clients', label: 'Client book', description: 'Who you serve' },
      { href: '/relationships', label: 'Households', description: 'Family graph and household context' },
      { href: '/memory', label: 'Client memory', description: 'Facts the RM has accepted' },
    ],
  },
  {
    id: 'journey',
    label: 'Wealth Journey',
    short: 'Journey',
    description: 'Engage, discover, recommend, act, service',
    items: [
      { href: '/journey', label: 'Engage', description: 'Prioritised leads and the AI meeting brief' },
      { href: '/journey/pipeline', label: 'Pipeline', description: 'Opportunity board' },
      { href: '/journey/discover', label: 'Discover', description: 'Profile, goals and the knowledge graph' },
      { href: '/journey/recommend', label: 'Recommend', description: 'Planner, shortlist, pitch and policy' },
      { href: '/journey/act', label: 'Act', description: 'Cart, signature and sandbox hand-off' },
      { href: '/journey/approvals', label: 'Approvals', description: 'A different person checks the cart' },
      { href: '/journey/service', label: 'Service', description: 'Drift, nudges and rebalancing' },
    ],
  },
  {
    id: 'studio',
    label: 'AI Meeting Studio',
    short: 'Studio',
    description: 'Summarise a meeting and accept profile changes',
    items: [
      { href: '/meetings', label: 'Meeting studio', description: 'Transcript, summary, diffs and follow-up' },
    ],
  },
  {
    id: 'market',
    label: 'Market and CIO',
    short: 'Market',
    description: 'Holdings, peers and the house view',
    items: [
      { href: '/portfolio', label: 'Portfolio', description: 'Holdings and asset-class breakdown' },
      { href: '/portfolio/future-planner', label: 'Future planner', description: 'Deterministic projection with an AI narrative' },
      { href: '/portfolio/currency', label: 'Currency', description: 'Currency exposure' },
      { href: '/portfolio/investors-like-me', label: 'Investors like me', description: 'Peer allocation' },
      { href: '/market', label: 'Market data', description: 'Quotes, news and signals' },
    ],
  },
  {
    id: 'inspector',
    label: 'Platform and API inspector',
    short: 'Admin',
    description: 'Existing operator screens, kept available',
    items: [
      { href: '/priorities', label: 'Priority book', description: 'Pin, snooze and dismiss' },
      { href: '/calendar', label: 'Calendar', description: 'Meetings and resolutions' },
      { href: '/capture', label: 'Capture API', description: 'Consent and capture session calls' },
      { href: '/messages', label: 'Messages', description: 'Draft messages' },
      { href: '/workflows', label: 'Workflows', description: 'Workflow instances' },
      { href: '/briefs', label: 'Brief archive', description: 'Stored client briefs' },
      { href: '/advice', label: 'Product API', description: 'Suitability lookups' },
      { href: '/shariah', label: 'Shariah API', description: 'Screening lookups' },
      { href: '/actions', label: 'Actions API', description: 'Authorise and execute' },
      { href: '/admin', label: 'Decision gates', description: 'Capability switches' },
      { href: '/admin/audit', label: 'Audit trail', description: 'Change log' },
      { href: '/admin/telemetry', label: 'Telemetry', description: 'Activity volumes' },
      { href: '/admin/artifacts', label: 'Artifacts', description: 'Document history' },
      { href: '/admin/skills', label: 'Skill registry', description: 'Workflow skills' },
      { href: '/admin/session', label: 'Session', description: 'Sign-in and access' },
      { href: '/admin/catalogue', label: 'Developer reference', description: 'Operator lookup' },
      { href: '/ui-kit', label: 'UI kit', description: 'Component gallery' },
    ],
  },
];

export const ALL_NAV_ITEMS = NAV_GROUPS.flatMap((g) =>
  g.items.map((i) => ({ ...i, groupId: g.id, groupLabel: g.label })),
);

// /brief/{clientId} is a generated detail of the Client Briefs workspace. It
// has no literal nav entry (it needs a client id), so map it explicitly rather
// than letting it fall back to the first group and a "Detail" breadcrumb.
const BRIEF_DETAIL: NavItem = {
  href: '/briefs',
  label: 'Meeting Brief',
  description: 'Prepared pack for a specific client meeting',
};

/** Find the group that owns a pathname; used for the rail + breadcrumb. */
export function groupForPath(pathname: string): NavGroup {
  if (pathname.startsWith('/brief/')) {
    return NAV_GROUPS.find((g) => g.id === 'inspector')!;
  }
  const exact = ALL_NAV_ITEMS.filter((i) => pathname === i.href).sort(
    (a, b) => b.href.length - a.href.length,
  )[0];
  if (exact) return NAV_GROUPS.find((g) => g.id === exact.groupId)!;
  const prefix = ALL_NAV_ITEMS.filter((i) => pathname.startsWith(i.href + '/')).sort(
    (a, b) => b.href.length - a.href.length,
  )[0];
  if (prefix) return NAV_GROUPS.find((g) => g.id === prefix.groupId)!;
  return NAV_GROUPS[0];
}

export function itemForPath(pathname: string): NavItem | undefined {
  if (pathname.startsWith('/brief/')) return BRIEF_DETAIL;
  return ALL_NAV_ITEMS.filter((i) => pathname === i.href || pathname.startsWith(i.href + '/')).sort(
    (a, b) => b.href.length - a.href.length,
  )[0];
}
