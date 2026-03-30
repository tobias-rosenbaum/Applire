# Emma: Returning Power User
## Context Snapshot
Attribute 	Value
Profile completeness 	80–100%
Trust level 	High — has generated multiple CVs
Current situation 	Applying to 2–3 senior roles simultaneously
Time pressure 	Moderate — wants speed, not urgency
Emotional baseline 	Confident in system, impatient with friction
Primary JTBD 	"One-click tailoring — paste JD, get PDF"
LTV potential 	Highest across all personas
## Trigger

Emma receives a recruiter outreach or spots a job posting:

"Director of QA, GxP Compliance — Frankfurt"

"Head of Validation, MedTech — Basel"

She already has her Master Profile. She wants one tailored CV per JD, fast. She's not exploring — she's executing.
Happy Path Flow

Emma opens Apliqa (bookmark or direct URL), the dashboard loads with a personalized greeting and profile completeness badge. She clicks "New Application" or "Tailor CV", the system prompts for JD input (URL or paste), and she pastes a JD URL. The system scrapes and analyzes the JD, returns a summary, then auto-triggers a gap analysis against her Master Profile.

The system presents a match score (e.g., 87%) and gap summary. She reviews the gaps — they're minor — and clicks "Proceed to CV". The system generates a tailored CV and loads a preview in a browser iframe. She reviews it, clicks "Download PDF", the PDF downloads, the version is logged to her dashboard, and the dashboard updates to show "3 active applications."

flowchart TD
    A[Open Apliqa] --> B[Dashboard Loads]
    B --> C[Click: New Application]
    C --> D[JD Input Modal]
    D --> E{Input Type}
    E -->|URL| F[Scrape JD]
    E -->|Text| G[Analyze JD]
    F --> G
    G --> H[Gap Analysis]
    H --> I[Present Match Score + Gaps]
    I --> J{User Decision}
    J -->|Proceed| K[Generate CV]
    J -->|Interview| L[Quick Chat]
    L --> K
    K --> M[CV Preview iframe]
    M --> N[Download PDF]
    N --> O[Dashboard Updated]

## Branching Scenarios
### Branch A: Minor Gaps Found (Match Score 70–90%)

Step System Response Emma's Options Default Behavior
Gap presentation "Your profile matches 87%. 2 minor gaps found. Quick interview recommended (3 min)." Accept interview → 2–3 questions, profile enriched Interview optional, not blocking
Skip → "Proceed with current profile" CV generated with existing data

UX Principle: Don't block Emma. Make the interview optional but tempting. Show time estimate upfront.

### Branch B: Critical Gaps Found (Match Score <70%)

Step System Response Emma's Options Default Behavior
Gap presentation "Critical gaps detected. This role requires [X, Y, Z]. Interview recommended (5–7 min)." Accept interview → targeted questions, profile significantly enriched Interview strongly recommended
Skip → "Proceed with current profile" CV generated with warning: "May be weaker for this JD"

UX Principle: Warn, don't block. Emma may know something the system doesn't. Trust her judgment.

### Branch C: Scraping Failure (LinkedIn/XING)

Step System Response Emma's Action Outcome
URL scrape fails "Couldn't fetch this URL. Please paste the JD text instead." Pastes text manually Proceeds normally

UX Principle: Graceful degradation. Never dead-end. Provide clear recovery path.

### Branch D: Profile Outdated (>6 months since update)

Step System Response Emma's Action Outcome
Step System Response Emma's Action Outcome
Profile check "Your profile hasn't been updated in 8 months. Quick check: any new projects, certifications, or roles?" Confirms "All current" or adds updates Profile refreshed, trust maintained

UX Principle: Proactive profile maintenance. Emma's LTV depends on profile quality. This is a feature, not a nag.

### Branch E: Session Interrupted (Browser Closed Mid-Flow)

Step System Response Emma's Action Outcome
Emma returns Dashboard shows "Incomplete: [Job Title]" with "Resume" button Clicks "Resume" Session restored from GET /api/session/{id}

UX Principle: State persistence. Emma never loses work. Backend-stateful design (ADR 004) enables this.

## Emotional Journey

[Confident] → [Focused] → [Curious] → [Informed] → [Satisfied] → [Done]
↑ ↓
└──────────── [Delighted] if proactive update ───────┘
Beat 	Trigger 	Emma's Feeling
Recognition 	"Welcome back, Emma" + profile badge 	Known, valued
Speed 	JD analysis in <30s 	Respected, efficient
Transparency 	Match score + gap summary visible 	In control, informed
Agency 	Can skip interview 	Trusted, autonomous
Closure 	Dashboard shows all applications 	Organized, complete
Delight 	Proactive profile check 	Cared for, supported

## Exit Conditions
Exit Type 	Trigger 	System State 	Next Action
Happy exit 	PDF downloaded, logged to dashboard 	CV record created, flow step = "complete" 	Return to dashboard or close tab
Deferred exit 	Browser closed mid-flow 	Session preserved in flow_sessions + interview_sessions 	Resume via "Incomplete" card on dashboard
Abandon exit 	Emma leaves without downloading 	Draft CV saved (90-day TTL), flow step = "cv_generation" 	Appears in dashboard as "Incomplete"

## Touchpoint Inventory
Screen/Component 	Purpose 	Emma Interaction 	Technical Reference
Dashboard 	Landing, overview, active applications 	View, click "New Application" 	GET /api/flow (list user's flows)
JD Input Modal 	URL or text entry 	Paste URL/text, submit 	POST /api/job/analyze
Gap Summary Card 	Match score + gap list 	Review, choose action 	POST /api/job/{id}/gaps → GapAnalysis
Interview Chat UI 	2–7 questions, conversational 	Answer free-text, submit 	POST /api/session/{id}/message
CV Preview (iframe) 	WYSIWYG HTML preview 	Scroll, review, click "Download" 	GET /api/cv/{id}/html
PDF Download 	Final artifact 	Download, done 	GET /api/cv/{id}/pdf
Application History 	Version tracking 	View past CVs, compare deltas 	GET /api/cv (list user's CVs)
Incomplete Card 	Resume interrupted flows 	Click "Resume" 	GET /api/flow/{id}/state

## Design Principles
Principle 	Rationale 	Implementation
One-click is the goal 	Every extra click is friction 	Paste JD → get PDF should be possible in 3 clicks
Transparency without overwhelm 	Emma wants info, not a report 	Match score + gap count visible; details on demand
Trust her judgment 	She can skip the interview 	Interview is always optional; system advises, doesn't command
Proactive, not pushy 	Profile maintenance is a feature 	"Your profile is 8 months old" is helpful, not annoying
Memory is a feature 	Never re-enter data 	Master Profile persists; every session enriches
Speed is respect 	Emma's time has high opportunity cost 	JD analysis <30s, CV generation <10s
State survives interruption 	Life happens 	Backend-stateful design; resume from any point
## Open Questions
# 	Question 	Impact 	Status
1 	Dashboard layout: Does Emma see a "quick action" panel (New Application) or a full pipeline view first? 	First screen design 	Open
2 	Gap presentation: Card-based (visual) vs. list-based (dense)? How much detail before "Proceed"? 	Gap Summary Card design 	Open
3 	Interview modality: Full-screen chat vs. slide-out panel vs. inline accordion? 	Interview Chat UI design 	Open
4 	CV preview layout: Side-by-side with gap summary, or sequential (gaps dismissed → preview)? 	Screen flow, cognitive load 	Open
5 	Version comparison: How does Emma compare CV v1 vs. v2 for the same JD? Delta view? 	Application History feature 	Open
6 	Mobile support: Is Emma's journey fully supported on mobile, or desktop-first? 	Responsive design scope 	Open
7 	Notification preference: Does Emma want email/push when CV is ready, or is in-app sufficient? 	Notification system design 	Open
