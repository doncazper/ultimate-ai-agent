# CRM v3 Reference Synthesis

Status: north-star render specification, documentation only.
Surface ID: `CRM-01` v3.
Current as of: 2026-07-11.

CRM v3 synthesizes five locally reviewed specialty CRM references into a
general-purpose founder relationship workspace. It does not select or imply a
healthcare, insurance, retail, legal, or real-estate product vertical. The
professional-services reference supplies the primary structure; the other
references contribute only reusable interaction patterns.

## Shared CRM Grammar

All five references use the same compact desktop-software model:

- stable navigation and specialty-aware route terminology;
- one fixed global search field in the top toolbar;
- a concise five- or six-measure KPI strip;
- smart views and pipeline shortcuts adjacent to the main relationship list;
- a dense, sortable table as the primary operating surface;
- one persistent right-side inspector for the selected record;
- tasks, scheduled commitments, communications, files, and activity in context;
- bounded lower analytics for pipeline, workload, lifecycle, or risk;
- restrained semantic color for stages, health, urgency, and attention.

## Selective Contribution

- Professional services supplies the client/engagement table, next milestone,
  relationship health, pipeline overview, task schedule, and inspector model.
- Financial services contributes organization/household depth, renewal-style
  commitment visibility, health signals, and a source-backed next action.
- Healthcare contributes follow-up urgency, scheduled commitment prominence,
  risk visibility, and explicit open-task context.
- E-commerce contributes lifecycle smart views, preferred-channel awareness,
  recent activity, and a clearly bounded next-best action.
- Real estate contributes people-first pipelines, calls and appointments as
  primary work, compact stage analytics, and fast next-step access.

## Locked v3 Composition

The standard UAA shell remains unchanged and includes Today, Communications,
Work Board, CRM, Calendar, News, Studio, Knowledge, Activity & Trust,
Customize, Settings, and Developer Tools.

The CRM workspace uses:

1. A single non-wrapping route toolbar with title/subtitle on the left, fixed
   search in the standard center-right slot, smart-view and filter controls,
   and `Review 3 decisions` at the far right.
2. Route tabs for People, Organizations, Opportunities, Pipeline, Follow-ups,
   and Reports.
3. One compact KPI strip for active relationships, follow-ups due, open
   opportunities, pipeline value, relationships at risk, and commitments this
   week.
4. A smart-view rail for Needs attention, Follow-ups due, Waiting on others,
   Active opportunities, At risk, and Recently contacted.
5. A dense relationship table with person/organization, relationship type,
   stage, last contact, next commitment, opportunity/value, health/attention,
   and next action.
6. A persistent inspector with overview, related people and organization,
   safe contact channels, opportunity and pipeline context, commitments, open
   tasks, recent activity, and links to Communications, Calendar, Work Board,
   Knowledge, and receipts.
7. Bounded lower analytics for pipeline stage and relationship health/workload.
8. A persistent route-aware UAA composer capable of explaining sources and
   confidence while drafting or proposing work rather than executing it.

## Calling Truth Contract

`Call`, `Message`, `Add follow-up`, and overflow are first-class record actions.
The Call control opens an availability-backed method chooser for system default
or iPhone, FaceTime Audio, WhatsApp, Telegram, and Google Voice. Every method is
marked `Available`, `Not connected`, `Planned`, or `Blocked`; unavailable
providers are never rendered as connected.

The chooser exposes only safe destination text such as `Mobile ending ••42`.
Launching a dialer is an external action and enters an exact review or approval
step where required. Opening a dialer never marks a call or follow-up complete.
Recording is Off by default. Call outcomes require adapter evidence or explicit
operator confirmation before they become relationship truth.

## UAA Integration

The route composer may ask about the selected relationship or pipeline, draft a
follow-up, propose a call, propose a meeting, summarize recent activity,
identify neglected relationships, or recommend a next step. Recommendations
must expose sources and confidence. These are proposals and explanations; this
render grants no connector write, telephony, backend route, or runtime
authority.
