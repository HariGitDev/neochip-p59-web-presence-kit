/* Tenant content — NeoChip Solutions.
 *
 * SCOPE NOTE (2026-08-23, R2): restructured after Hari corrected the benchmark to
 * ampel.com (American Pioneer Electronics). AMPEL positions as a full supply-chain
 * partner — product catalog, line card, inventory management, value-added services,
 * lifecycle support, market intelligence — not a narrow RFQ shop. This file follows
 * that breadth.
 *
 * GUARDRAIL: nothing here may claim authorized lines, certifications, a warehouse or
 * physical location, phone number, customer counts, revenue, supplier relationships,
 * guaranteed inventory, or in-house test capability. AMPEL claims several of these
 * (NJ warehouse, 500+ manufacturers, AS5553/AS6081, in-house IC testing) — NeoChip
 * cannot mirror those claims. Where the structure needs one, use a TBD token so it is
 * visible on the page and cannot ship silently. See REQUIREMENTS.md §4.
 */

const content = {
  id: 'neochip',
  brand: {
    name: 'NeoChip Solutions',
    short: 'NeoChip',
    tagline: 'Electronic components and supply chain solutions',
    logo: null, // D-3 open
  },

  /* Nav now carries dropdowns — AMPEL's "Our Services and Solutions" is a section, not a page. */
  nav: [
    { label: 'About', href: '#about' },
    {
      label: 'Products', href: '#products',
      children: [
        { label: 'Component categories', href: '#products' },
        { label: 'Lines we quote', href: '#lines' },
      ],
    },
    {
      label: 'Services & Solutions', href: '#services',
      children: [
        { label: 'Sourcing & shortage', href: '#services' },
        { label: 'Obsolescence & EOL', href: '#services' },
        { label: 'Inventory management', href: '#services' },
        { label: 'Excess inventory', href: '#services' },
        { label: 'BOM & cross-reference', href: '#services' },
        { label: 'Value-added services', href: '#value-added' },
        { label: 'Logistics & fulfilment', href: '#value-added' },
      ],
    },
    { label: 'Quality', href: '#quality' },
    { label: 'Industries', href: '#industries' },
    { label: 'Insights', href: '#insights' },
    { label: 'Contact', href: '#contact' },
  ],
  cta: { label: 'Submit RFQ', href: '#rfq' },

  hero: {
    eyebrow: 'Components · supply chain · lifecycle support',
    title: 'More than a parts supplier. A supply chain you can plan around.',
    lede:
      'NeoChip Solutions supports electronics manufacturers across the full component lifecycle — sourcing and shortage cover, obsolescence and last-time-buy, BOM and cross-reference work, inventory programmes, excess recovery, and the documentation and logistics that hold it together.',
    primary: { label: 'Send a part number or BOM', href: '#rfq' },
    secondary: { label: 'See what we do', href: '#services' },
  },

  // Renders nothing while empty. Real figures only — OQ-4.
  proof: [],

  /* ---- Core services: the AMPEL "Services and Solutions" breadth ---- */
  services: [
    { num: '01', title: 'Component sourcing', body: 'Open-market and independent-channel sourcing for parts the authorized channel cannot supply on your timeline.' },
    { num: '02', title: 'Shortage & allocation cover', body: 'Line-down and allocation situations, worked against your build dates rather than a quote queue.' },
    { num: '03', title: 'Obsolescence & EOL', body: 'Last-time-buy planning, legacy component sourcing, and end-of-life risk on parts still designed into live products.' },
    { num: '04', title: 'BOM management', body: 'Whole-BOM quoting, line-by-line risk flags, and consolidated sourcing instead of part-by-part chasing.' },
    { num: '05', title: 'Cross-reference & substitutes', body: 'Form-fit-function alternates identified and documented when the original part is gone, allocated, or priced out.' },
    { num: '06', title: 'Inventory programmes', body: 'Buffer stock, scheduled releases, and consignment-style arrangements planned around your production schedule.' },
    { num: '07', title: 'Excess inventory recovery', body: 'Recovery options for surplus and obsolete stock sitting on your books.' },
    { num: '08', title: 'Supply chain optimisation', body: 'Consolidating fragmented supply, reducing supplier count, and taking cost and lead time out of the lines that hurt.' },
  ],

  /* ---- Value-added: the operational layer AMPEL leads with ---- */
  valueAdded: {
    eyebrow: 'Value-added services',
    title: 'The work that happens after the purchase order',
    lede: 'Sourcing is the visible half. This is the half that decides whether the parts are usable when they land.',
    items: [
      { title: 'Kitting & consolidation', body: 'Multiple lines consolidated into a single scheduled delivery against your build.' },
      { title: 'Documentation control', body: 'Traceability paperwork assembled and reconciled before the shipment leaves.' },
      { title: 'Packaging & handling', body: 'Moisture-sensitivity and ESD handling requirements specified and checked against the offer.' },
      { title: 'Worldwide fulfilment', body: 'Routing, consolidation, and delivery scheduling coordinated across origins.' },
      { title: 'Market intelligence', body: 'Pricing and availability context on the lines you buy, so procurement decisions are informed rather than reactive.' },
      { title: 'Lifecycle support', body: 'Ongoing visibility on EOL and PCN risk across the parts you depend on.' },
    ],
  },

  risk: {
    eyebrow: 'Why this matters',
    title: 'A bad part does not fail on the bench. It fails in the field.',
    body:
      'The cost of a counterfeit or mis-marked component is never the price of the component. It is the rework, the schedule, the customer, and the investigation. Independent sourcing only earns its place if the verification is real — so that is where we spend the effort.',
  },

  quality: {
    eyebrow: 'Quality & counterfeit avoidance',
    title: 'How we verify what we source',
    lede: 'A documented process, applied the same way every time.',
    steps: [
      { num: '01', title: 'Supplier vetting', body: 'Source is qualified before a quote is issued. Unknown or unverifiable sources are declined rather than passed along with a caveat.' },
      { num: '02', title: 'Documentation review', body: 'Traceability paperwork is reviewed against the offer — part number, date code, quantity, packaging, and origin — before purchase.' },
      { num: '03', title: 'Inspection on receipt', body: 'Incoming goods are checked against the purchase documentation and the customer requirement before release.' },
      { num: '04', title: 'Escalation', body: 'Anything that does not reconcile stops. We tell you it stopped, and why, before you plan around it.' },
    ],
    badges: [],   // OQ-3 — AMPEL shows AS5553/AS6081/MSL/JEDEC. We show nothing until earned.
  },

  /* ---- Products: AMPEL's catalog is far broader than semiconductors ---- */
  products: [
    'Integrated circuits & semiconductors',
    'Microcontrollers & processors',
    'Memory',
    'Discrete semiconductors',
    'Passive components',
    'Connectors & terminals',
    'Electromechanical',
    'Relays',
    'Power electronics',
    'Optoelectronics',
    'Sensors',
    'RF & microwave',
    'Thermal management',
    'Wire, cable & harness',
    'IoT modules',
    'Test & measurement',
  ],

  /* Line card — structurally present, deliberately empty. See guardrails. */
  lines: {
    eyebrow: 'Lines',
    title: 'Lines we quote',
    lede: 'We quote across the open and independent channel. A published manufacturer line card goes here once those relationships are verified — not before.',
    items: [],
  },

  industries: [
    'Industrial & automation', 'Medical devices', 'Telecommunications', 'Automotive',
    'Consumer electronics', 'Contract manufacturing / EMS', 'Aerospace & defence', 'Energy & power',
  ],

  process: [
    { num: '01', title: 'You send a part number or a BOM', body: 'Part number, quantity, target date. A whole BOM is better — we will flag the risky lines.' },
    { num: '02', title: 'We source and verify', body: 'We work the supply base, check what comes back against the documentation, and price the alternates where they exist.' },
    { num: '03', title: 'You get a real answer', body: 'Price, lead time, source condition, substitutes, and what we could not find — stated plainly.' },
    { num: '04', title: 'We keep the line supplied', body: 'Scheduled releases, buffer stock, and EOL warnings on the parts you depend on.' },
  ],

  faq: [
    { q: 'Are you an authorized distributor?', a: 'No. NeoChip Solutions is an independent distributor. We source through the open market and the independent supply base, which is why the verification process described above exists.' },
    { q: 'Do you only do spot buys, or ongoing supply?', a: 'Both. Spot buys and line-down cover are the urgent work; inventory programmes and scheduled releases are the steady work. The second is where we are more useful.' },
    { q: 'What do you need to quote?', a: 'A manufacturer part number and a quantity is enough to start. Target price, required date code, packaging, and delivery date help us filter faster. A BOM is welcome.' },
    { q: 'Can you find alternates if the part is obsolete?', a: 'Yes — cross-reference and form-fit-function substitute identification is part of the service, documented so your engineering team can approve or reject it.' },
    { q: 'What happens if you cannot find a part?', a: 'We tell you, and we tell you early. A late "no" is worse than an early one.' },
  ],

  /* Insights / news — AMPEL runs a blog. Structure present, no fabricated posts. */
  insights: { eyebrow: 'Insights', title: 'Market notes', items: [] },

  /* Testimonials — AMPEL leads with these. Empty until real ones exist. */
  testimonials: [],

  contact: {
    email: 'Ads@deepti.net',
    phone: null,
    address: null,
  },

  footerLegal: ['Privacy Policy', 'Terms & Conditions'],
}

export default content
