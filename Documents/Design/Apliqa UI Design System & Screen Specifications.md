## Apliqa UI Design System & Screen Specifications

### Brand Foundation

**Color Palette:**

- Primary Blue: #1B4F72 (trust, professionalism)
- Teal Accent: #2A8F9D (action, energy, European tech)
- Secondary Gold: #C9A84C (warmth, refinement, regulatory confidence)
- Success Green: #2D9F6F (positive outcomes, strong matches)
- Warning Amber: #E5A832 (partial matches, needs improvement)
- Critical Red: #D94F4F (gaps, critical issues)
- Neutral Light: #F5F7FA (backgrounds, cards)
- Neutral Dark: #2C3E50 (text, headers)
- White: #FFFFFF (primary background)

**Typography:**

- Headlines: Geometric sans-serif (e.g., Inter, Poppins), bold, 24-32px
- Body: Clean sans-serif (e.g., Inter, Roboto), regular, 14-16px
- Labels: Sans-serif, medium, 12-14px
- Tagline: "Precise. Confident. Future-Ready."

**Visual Language:**

- Soft shadows (0 2px 8px rgba(0,0,0,0.08))
- Rounded corners (8px standard, 12px for larger elements)
- Flat illustration style with subtle gradients
- Icons: Geometric, 24-32px standard sizes
- Spacing: 8px grid system (multiples of 8)

---

## MARCUS: New User Happy Path (Revised — Combined Flow)

### Screen 1: Combined CV Upload + JD Input

**Purpose:** Single entry point — upload CVs AND paste JD in one step. Eliminate friction.

**Layout:**

```
┌─────────────────────────────────────────────────────┐
│ Apliqa                                              │
│ AI-Powered CV Transformation                        │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌─── Your CVs (60%) ───┐  ┌── Job Description ──┐ │
│  │                       │  │      (40%)          │ │
│  │  Upload 2-4 CVs for   │  │  Paste a JD so we   │ │
│  │  the richest profile   │  │  can tailor your    │ │
│  │                       │  │  profile immediately │ │
│  │  ┌─────────────────┐  │  │                     │ │
│  │  │                 │  │  │  [URL] | [Paste]    │ │
│  │  │  📄 Drag & drop │  │  │                     │ │
│  │  │  CVs here       │  │  │  ┌───────────────┐  │ │
│  │  │  or click       │  │  │  │ Paste JD text │  │ │
│  │  │                 │  │  │  │ here...       │  │ │
│  │  │  PDF, DOCX, DOC │  │  │  │               │  │ │
│  │  │                 │  │  │  └───────────────┘  │ │
│  │  └─────────────────┘  │  │                     │ │
│  │                       │  │  (Optional — add    │ │
│  └───────────────────────┘  │   this later)       │ │
│                              └─────────────────────┘ │
│                                                     │
│             [Analyze & Build Profile]               │
│          This usually takes about 30 seconds        │
│                                                     │
├─────────────────────────────────────────────────────┤
│ Precise. Confident. Future-Ready.                   │
└─────────────────────────────────────────────────────┘
```

**Key Elements:**

- Two-column layout within centered content area (max-width ~900px)
- LEFT (60%): "Your CVs" section


- Headline: "Your CVs" (20px, bold, #2C3E50)
- Subheading: "Upload 2-4 CVs for the richest profile. We'll merge them automatically." (14px, regular, #555)
- Drag-drop zone: Full column width × 240px, border: 2px dashed #2A8F9D, background: #F5F7FA
- After files added: Zone shrinks, file chips appear (filename + X to remove)
- RIGHT (40%): "Job Description" section


- Headline: "Job Description" (20px, bold, #2C3E50)
- Subheading: "Paste a JD so we can tailor your profile immediately." (14px, regular, #555)
- Tab toggle: [URL] | [Paste Text] with teal underline on active
- URL tab: Input field with placeholder
- Paste tab: Textarea (full width × 180px)
- Note: "(Optional — you can add this later)" (12px, italic, light gray)
- CTA: "Analyze & Build Profile" (Teal #2A8F9D, 52px height, bold, 240px width, centered)
- Disabled until at least 1 CV uploaded
- Helper: "This usually takes about 30 seconds" (12px, gray)

**Interaction:**

- Drag zone: Hover lightens background, border becomes solid
- File chips: Click X to remove, zone text changes to "Add more files"
- Tab toggle: Smooth underline animation between URL/Paste
- CTA: Disabled (gray) until 1+ CV uploaded; enables with color transition

**Emotional Tone:** Welcoming, purposeful. Marcus sees he can do everything in one step.

---

### Screen 2: Processing State — Rich Progress Animation
### Screen 2: Processing State (Overlay) — Rich Progress Animation
**Purpose:** Transform waiting into watching intelligence work. Replace THREE waiting moments with ONE.

**Layout:**

```
┌─────────────────────────────────────────────────────┐
│ Apliqa                                              │
├─────────────────────────────────────────────────────┤
│                                                     │
│              [Animated illustration]                │
│                                                     │
│  ✓  Uploading CVs — 3 files received               │
│  ✓  Parsing CVs — 5 positions, 12 projects,        │
│                     3 certifications found           │
│  ✓  Analyzing JD — QA Manager, 21 CFR Part 11      │
│  →  Building Master Profile — Merging 3 sources...  │
│  ○  Matching against role                           │
│  ○  Detecting gaps                                  │
│                                                     │
│  ████████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░   │
│  Usually takes about 30 seconds                     │
│                                                     │
└─────────────────────────────────────────────────────┘
```

**Key Elements:**

- Centered content area (max-width ~600px), vertically centered
- Animated illustration at top (clean, teal/blue tones, document analysis theme)
- Step-by-step progress checklist (vertical list):


- Completed: Green checkmark (#2D9F6F) + label + detail text (faded #888)
- In progress: Teal spinner (#2A8F9D, animated) + label (bold #2C3E50) + detail
- Pending: Gray circle outline (#D0D0D0) + label (light gray #CCC)
- Detail text appears as steps complete (e.g., "5 positions, 12 projects found")
- Progress bar: Full width, 6px, background #E0E0E0, fill #2A8F9D
- Helper: "Usually takes about 30 seconds" (12px, gray)

**Interaction:**

- Steps complete sequentially with micro-animations
- Checkmark pops in (scale 0 → 1, 200ms)
- Detail text fades in (opacity 0 → 1, 300ms)
- Progress bar fills smoothly
- Spinner rotates continuously on active step

**Emotional Tone:** Active, transparent, building anticipation. Marcus watches intelligence work.

---

### Screen 3: Combined Result — Master Profile + Match Score + Gaps

**Purpose:** The PAYOFF. Shows everything at once: profile summary, match score, gaps, and clear next action.

**Layout:**

```
┌─────────────────────────────────────────────────────┐
│ Apliqa                                              │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ✓ Master Profile Created                          │
│                                                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐│
│  │ 5 Pos.   │ │ 12 Proj. │ │ 3 Certs  │ │ 47 Pts ││
│  │ Extracted │ │ Identified│ │ Added   │ │ Merged ││
│  └──────────┘ └──────────┘ └──────────┘ └────────┘│
│                                                     │
│  ─────────────────────────────────────────────────  │
│                                                     │
│  ╭──────╮  QA Manager, 21 CFR Part 11 — Munich     │
│  │ 82%  │  Your profile matches 82% of this role's  │
│  │Strong│  requirements.                            │
│  ╰──────╯                                           │
│                                                     │
│  2 minor gaps identified:                           │
│  ⚠ EU GMP Audit Experience                         │
│    You have: ANVISA audits (highly relevant)        │
│  ⚠ Team Leadership (5+ reports)                    │
│    You have: Project leadership (transferable)      │
│                                                     │
│  [Quick Interview (3 min)]  [Generate CV]  Explore  │
│   Close gaps & boost score                          │
│                                                     │
├─────────────────────────────────────────────────────┤
│ Precise. Confident. Future-Ready.                   │
└─────────────────────────────────────────────────────┘
```

**Key Elements:**

- Section 1 (Master Profile): Checkmark + headline + 4 stat cards in row


- Cards: 140px wide, white, shadow, teal accent bar top (3px)
- Stats: Number (24px, bold, teal), Label (12px, gray)
- Divider: 1px line (#E0E0E0), 24px margin
- Section 2 (Match Analysis):


- Score badge: 100px circle, green #2D9F6F, "82%" (36px bold white), "Strong Fit" (12px white)
- Role title: "QA Manager, 21 CFR Part 11 — Munich" (20px, bold, #2C3E50)
- Match text: (14px, regular, #555)
- Gaps: Amber dots (#E5A832) + gap title + "You have:" context
- CTAs:


- Primary: "Quick Interview (3 min)" (teal, 48px, bold, slight glow)
- Secondary: "Generate CV Now" (outline, teal, 48px)
- Tertiary: "Explore Profile" (text link, teal, 14px)
- Helper below primary: "Answer a few questions to close the gaps" (12px, italic, gray)

**Interaction:**

- Stat cards have subtle hover effect
- Gap items have hover background
- Primary CTA has slight pulse/glow to draw attention
- Score badge animates on load (number counts up from 0 to 82)

**Emotional Tone:** Triumphant. Marcus went from upload → 30 second wait → complete analysis. No wasted steps.

---

---

### Screen 3: Gap Summary & Match Score

**Purpose:** Transparency, informed decision-making, optional interview

**Layout:**

```
┌─────────────────────────────────────────────────────┐
│ Apliqa                                              │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌─────────────────────────────────────────────┐   │
│  │  ✓ Match Score: 82% — Strong Fit            │   │
│  │                                             │   │
│  │  Your profile matches 82% of this role's    │   │
│  │  requirements. 2 minor gaps found.          │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
│  Gaps Identified:                                   │
│                                                     │
│  ⚠ EU GMP Audit Experience                         │
│    You have: ANVISA audits (highly relevant)       │
│                                                     │
│  ⚠ Team Leadership (5+ reports)                    │
│    You have: Project leadership (transferable)     │
│                                                     │
│  These gaps are minor. You can:                     │
│                                                     │
│     [Quick Interview (3 min)]  [Proceed as-is]     │
│                                                     │
├─────────────────────────────────────────────────────┤
│ Precise. Confident. Future-Ready.                   │
└─────────────────────────────────────────────────────┘
```

**Key Elements:**

- Match score badge: Centered, large (120px × 120px), circular, green (#2D9F6F) background, white text


- "82%" (48px, bold, white)
- "Strong Fit" (14px, regular, white)
- Headline: "Match Score: 82% — Strong Fit" (28px, bold, #2C3E50)
- Subheading: "Your profile matches 82% of this role's requirements. 2 minor gaps found." (16px, regular, #555)
- Gap items: List format, each item has:


- Amber warning icon (#E5A832)
- Gap title (16px, bold, #2C3E50)
- Your strength (14px, regular, #888, italicized)
- CTA section: "These gaps are minor. You can:" (14px, regular, #555)
- Buttons:


- Primary: "Quick Interview (3 min)" (Teal #2A8F9D, 48px height)
- Secondary: "Proceed as-is" (Outline, #2A8F9D, 48px height)

**Interaction:**

- Gap items have hover effect (background lightens)
- Buttons have hover state (shadow, color darken)

**Emotional Tone:** Transparent, reassuring, empowering. Marcus feels in control.

---

## PRIYA: Cultural Adaptation Journey

### Screen 1: Master Profile Created + Cultural Detection

**Purpose:** Celebrate success AND signal cultural adaptation (unique value prop)

**Layout:**

```
┌─────────────────────────────────────────────────────┐
│ Apliqa                                              │
├─────────────────────────────────────────────────────┤
│                                                     │
│                    ✓ Master Profile Created         │
│                                                     │
│  Your profile is ready. Here's what we found:       │
│                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────┐  │
│  │ 4 Positions  │  │ 8 Projects   │  │ 2 Certs  │  │
│  │ Extracted    │  │ Identified   │  │ Added    │  │
│  └──────────────┘  └──────────────┘  └──────────┘  │
│                                                     │
│  31 data points consolidated                        │
│                                                     │
│  ┌─────────────────────────────────────────────┐   │
│  │ 🌍 Cultural Adaptation Detected             │   │
│  │                                             │   │
│  │ We identified your CV follows Indian       │   │
│  │ market conventions. We'll adapt it for     │   │
│  │ DACH pharma standards during tailoring.    │   │
│  │                                             │   │
│  │ No manual research needed. We've got this. │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
│  Ready to tailor for a specific role?               │
│                                                     │
│     [Tailor for Role]    [Explore Profile]          │
│                                                     │
├─────────────────────────────────────────────────────┤
│ Precise. Confident. Future-Ready.                   │
└─────────────────────────────────────────────────────┘
```

**Key Elements:**

- Checkmark icon: Large (64px), green (#2D9F6F), centered
- Headline: "Master Profile Created ✓" (32px, bold, #2C3E50)
- Data cards: Same as Marcus (3 cards, teal accent bar)
- Cultural detection alert box:


- Background: Light teal (#E8F4F8)
- Left border: 4px solid teal (#2A8F9D)
- Icon: Globe emoji (32px) or custom icon
- Headline: "🌍 Cultural Adaptation Detected" (18px, bold, #2C3E50)
- Body text: "We identified your CV follows Indian market conventions. We'll adapt it for DACH pharma standards during tailoring. No manual research needed. We've got this." (14px, regular, #555)
- Tone: Warm, reassuring, expert
- CTA buttons: Same as Marcus

**Interaction:**

- Alert box has subtle animation on load (fade-in, slight slide-up)
- Buttons have hover state

**Emotional Tone:** Relieved, validated, expert-guided. Priya feels understood.

---

### Screen 2: Cultural Readiness Score Dashboard

**Purpose:** Give Priya a clear metric, suggest quick wins, motivate action

**Layout:**

```
┌─────────────────────────────────────────────────────┐
│ Apliqa                                              │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Cultural Readiness Score                           │
│                                                     │
│           ╭─────────────────╮                       │
│           │                 │                       │
│           │      45%        │                       │
│           │                 │                       │
│           ╰─────────────────╯                       │
│                                                     │
│  Your profile has strong content but needs          │
│  cultural adaptation for the DACH market.           │
│                                                     │
│  Quick Wins:                                        │
│                                                     │
│  ┌──────────────────┐  ┌──────────────────┐        │
│  │ 🗣️ Add German    │  │ 📸 Upload Photo  │        │
│  │ Language         │  │                  │        │
│  │ Proficiency      │  │ Professional     │        │
│  │                  │  │ headshot         │        │
│  └──────────────────┘  └──────────────────┘        │
│                                                     │
│  ┌──────────────────┐                              │
│  │ 🛂 Clarify Work  │                              │
│  │ Authorization    │                              │
│  │                  │                              │
│  │ Status           │                              │
│  └──────────────────┘                              │
│                                                     │
│                 [New Application]                   │
│                                                     │
├─────────────────────────────────────────────────────┤
│ Precise. Confident. Future-Ready.                   │
└─────────────────────────────────────────────────────┘
```

**Key Elements:**

- Headline: "Cultural Readiness Score" (28px, bold, #2C3E50)
- Circular progress indicator:


- 200px diameter
- Outer ring: Light gray (#E0E0E0), 8px stroke
- Inner ring: Teal (#2A8F9D), 8px stroke, 45% filled
- Center text: "45%" (48px, bold, #2A8F9D)
- Subheading: "Your profile has strong content but needs cultural adaptation for the DACH market." (16px, regular, #555, centered)
- Section header: "Quick Wins:" (18px, bold, #2C3E50)
- Suggestion cards: 3 cards in grid (2 top, 1 bottom), each:


- 160px × 160px
- White background, subtle shadow
- Icon (32px, emoji or custom)
- Title (14px, bold, #2C3E50)
- Description (12px, regular, #888)
- Hover effect: Shadow increase, slight lift
- CTA button: "New Application" (Teal #2A8F9D, 48px height, centered)

**Interaction:**

- Circular progress animates on load (ring fills from 0% to 45%)
- Cards have hover effect (shadow, slight scale)
- Clicking a card could open a modal for quick action (e.g., language input)

**Emotional Tone:** Motivating, clear, actionable. Priya sees a path forward.

---

### Screen 3: Interview Question (Cultural Education)

**Purpose:** Teach Priya about DACH norms while collecting data

**Layout:**

```
┌─────────────────────────────────────────────────────┐
│ Apliqa                                              │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Question 1 of 10 — Adapting your profile for       │
│  DACH pharma                                        │
│                                                     │
│  ████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   │
│  10% complete                                       │
│                                                     │
│  ┌─────────────────────────────────────────────┐   │
│  │                                             │   │
│  │  German language proficiency is important  │   │
│  │  for this role. What is your current       │   │
│  │  level?                                    │   │
│  │                                             │   │
│  │  (e.g., 'B1, actively pursuing B2')        │   │
│  │                                             │   │
│  │  ┌─────────────────────────────────────┐   │   │
│  │  │ [Free-text input field]             │   │   │
│  │  └─────────────────────────────────────┘   │   │
│  │                                             │   │
│  │                    [Submit]                 │   │
│  │                                             │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
├─────────────────────────────────────────────────────┤
│ Precise. Confident. Future-Ready.                   │
└─────────────────────────────────────────────────────┘
```

**Key Elements:**

- Header: "Question 1 of 10 — Adapting your profile for DACH pharma" (16px, regular, #555)
- Progress bar: Full width, 8px height, background #E0E0E0, fill #2A8F9D, 10% filled
- Progress text: "10% complete" (12px, regular, #888)
- Question card:


- Background: White, subtle shadow
- Padding: 40px
- Question text: "German language proficiency is important for this role. What is your current level?" (18px, regular, #2C3E50)
- Context hint: "(e.g., 'B1, actively pursuing B2')" (14px, italic, #888)
- Input field:


- Full width, 120px height
- Border: 1px solid #D0D0D0
- Placeholder: "Type your answer..."
- Focus state: Border color #2A8F9D, subtle shadow
- CTA button: "Submit" (Teal #2A8F9D, 48px height, centered)

**Interaction:**

- Input field focus: Border color changes to teal, subtle shadow appears
- Button hover: Color darkens, shadow increases
- On submit: Field clears, progress bar animates to next question, new question fades in

**Emotional Tone:** Conversational, educational, supportive. Priya feels guided.

---

## EMMA: Power User Dashboard

### Screen 1: Dashboard with Active Applications

**Purpose:** Show status at a glance, enable quick action, minimize friction

**Layout:**

```
┌─────────────────────────────────────────────────────┐
│ Apliqa                                              │
│ Welcome back, Emma                                  │
│ Profile: 95% Complete                              │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Active Applications (3)                            │
│                                                     │
│  ┌─────────────────────────────────────────────┐   │
│  │ QA Manager — Frankfurt                      │   │
│  │ Applied: 2 days ago                         │   │
│  │ Status: ✓ In Progress                       │   │
│  │                                             │   │
│  │ [Resume] [View CV] [Resubmit]               │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
│  ┌─────────────────────────────────────────────┐   │
│  │ Director of Validation — Basel              │   │
│  │ Applied: 5 days ago                         │   │
│  │ Status: ✓ In Progress                       │   │
│  │                                             │   │
│  │ [Resume] [View CV] [Resubmit]               │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
│  ┌─────────────────────────────────────────────┐   │
│  │ Senior Regulatory Affairs — Munich          │   │
│  │ Applied: 1 week ago                         │   │
│  │ Status: ⚠ Incomplete                        │   │
│  │                                             │   │
│  │ [Resume] [View CV] [Resubmit]               │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
│                 [New Application]                   │
│                                                     │
│  ┌─────────────────────────────────────────────┐   │
│  │ My Profile    Settings    Help              │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
├─────────────────────────────────────────────────────┤
│ Precise. Confident. Future-Ready.                   │
└─────────────────────────────────────────────────────┘
```

**Key Elements:**

- Header greeting: "Welcome back, Emma" (24px, bold, #2C3E50)
- Profile badge: "Profile: 95% Complete" (12px, regular, white text on teal #2A8F9D background, rounded pill)
- Section header: "Active Applications (3)" (20px, bold, #2C3E50)
- Application cards: List format, each card:


- Background: White, subtle shadow, left border 4px teal (#2A8F9D)
- Role title: "QA Manager — Frankfurt" (16px, bold, #2C3E50)
- Metadata: "Applied: 2 days ago" (12px, regular, #888)
- Status badge: "✓ In Progress" (green #2D9F6F) or "⚠ Incomplete" (amber #E5A832)
- Action buttons: "Resume", "View CV", "Resubmit" (small, outline style, 32px height)
- CTA button: "New Application" (Teal #2A8F9D, 48px height, centered, bold)
- Footer navigation: "My Profile", "Settings", "Help" (links, 12px, regular, #2A8F9D)

**Interaction:**

- Cards have hover effect (shadow increase, slight lift)
- Buttons have hover state (color darken, shadow increase)
- "Resume" button on incomplete application is highlighted (slightly bolder)
- Clicking "New Application" navigates to JD input screen

**Emotional Tone:** Organized, efficient, respectful of Emma's time. She feels in control.

---

## JASON: B2B Recruiter Interface

### Screen 1: Batch Match Matrix

**Purpose:** Show all matches at once, enable strategic decision-making, batch action

**Layout:**

```
┌─────────────────────────────────────────────────────┐
│ Apliqa B2B                                          │
│ Match Analysis: 8 Candidates × 3 Mandates           │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌──────────────────────────────────────────────┐   │
│  │ ☐ Candidate Name    │ Roche    │ Novartis │ │   │
│  │                     │ Director │ QA Mgr   │ │   │
│  ├──────────────────────────────────────────────┤   │
│  │ ☐ Marcus Hoffmann   │ 82% ✓   │ 71% ⚠   │ │   │
│  │ ☐ Sarah Chen        │ 75% ⚠   │ 88% ✓   │ │   │
│  │ ☐ David Müller      │ 68% ⚠   │ 64% ⚠   │ │   │
│  │ ☐ Priya Sharma      │ 79% ✓   │ 72% ⚠   │ │   │
│  │ ☐ Elena Rodriguez   │ 71% ⚠   │ 85% ✓   │ │   │
│  │ ☐ Klaus Weber       │ 64% ⚠   │ 58% ✗   │ │   │
│  │ ☐ Yuki Tanaka       │ 76% ⚠   │ 69% ⚠   │ │   │
│  │ ☐ Anna Kowalski     │ 81% ✓   │ 73% ⚠   │ │   │
│  └──────────────────────────────────────────────┘   │
│                                                     │
│  Selected: 5 matches                                │
│                                                     │
│  [Generate Kandidatenprofile for 5 Selected]        │
│                                                     │
├─────────────────────────────────────────────────────┤
│ Precise. Confident. Future-Ready.                   │
└─────────────────────────────────────────────────────┘
```

**Key Elements:**

- Header: "Match Analysis: 8 Candidates × 3 Mandates" (24px, bold, #2C3E50)
- Table:


- Header row: Candidate name column (200px), then mandate columns (120px each)
- Candidate names: 14px, regular, #2C3E50
- Checkboxes: 20px, left-aligned
- Match score cells:


- Green (#2D9F6F) for >80%: "82% ✓"
- Amber (#E5A832) for 60-80%: "71% ⚠"
- Red (#D94F4F) for <60%: "58% ✗"
- Font: 14px, bold, white text on colored background
- Cell padding: 12px
- Row hover: Background lightens slightly
- Selection counter: "Selected: 5 matches" (14px, regular, #555)
- CTA button: "Generate Kandidatenprofile for 5 Selected" (Teal #2A8F9D, 48px height, bold)

**Interaction:**

- Checkboxes: Click to select/deselect rows
- Selection counter updates in real-time
- Button is disabled if no rows selected (grayed out)
- Rows have hover effect (background lightens)
- Clicking a cell (non-checkbox) could open a detail modal

**Emotional Tone:** Powerful, efficient, data-driven. Jason feels in control of his pipeline.

---

### Screen 2: Pipeline Dashboard (Kanban)

**Purpose:** Track submissions, visualize progress, manage pipeline

**Layout:**

```
┌─────────────────────────────────────────────────────┐
│ Apliqa B2B                                          │
│ Pipeline Status                                     │
├─────────────────────────────────────────────────────┤
│                                                     │
│ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ │
│ │ Submitted    │ │ In Review    │ │ Rejected     │ │
│ │ (8)          │ │ (12)         │ │ (2)          │ │
│ ├──────────────┤ ├──────────────┤ ├──────────────┤ │
│ │              │ │              │ │              │ │
│ │ Marcus H.    │ │ Sarah C.     │ │ David M.     │ │
│ │ Roche        │ │ Novartis     │ │ BioNTech     │ │
│ │ Director     │ │ QA Manager   │ │ CSV Lead     │ │
│ │ 2 days ago   │ │ 5 days ago   │ │ 1 week ago   │ │
│ │              │ │              │ │              │ │
│ │ Priya S.     │ │ Elena R.     │ │              │ │
│ │ Roche        │ │ Novartis     │ │              │ │
│ │ Director     │ │ QA Manager   │ │              │ │
│ │ 1 day ago    │ │ 3 days ago   │ │              │ │
│ │              │ │              │ │              │ │
│ │ [+ 6 more]   │ │ [+ 10 more]  │ │              │ │
│ │              │ │              │ │              │ │
│ └──────────────┘ └──────────────┘ └──────────────┘ │
│                                                     │
│ ┌──────────────┐                                    │
│ │ Hired        │                                    │
│ │ (3)          │                                    │
│ ├──────────────┤                                    │
│ │              │                                    │
│ │ Klaus W.     │                                    │
│ │ Roche        │                                    │
│ │ Director     │                                    │
│ │ Hired 3 days │                                    │
│ │ ago          │                                    │
│ │              │                                    │
│ │ [+ 2 more]   │                                    │
│ │              │                                    │
│ └──────────────┘                                    │
│                                                     │
│  Summary Stats:                                     │
│  Total Submissions: 25 | Success Rate: 12% | Avg   │
│  Time to Hire: 18 days                             │
│                                                     │
├─────────────────────────────────────────────────────┤
│ Precise. Confident. Future-Ready.                   │
└─────────────────────────────────────────────────────┘
```

**Key Elements:**

- Header: "Pipeline Status" (24px, bold, #2C3E50)
- Kanban columns: 4 columns (Submitted, In Review, Rejected, Hired)


- Column header: Status name + count in parentheses (16px, bold, #2C3E50)
- Column background: Light gray (#F5F7FA)
- Column width: ~200px
- Submission cards:


- Background: White, subtle shadow
- Candidate name: 14px, bold, #2C3E50
- Company: 12px, regular, #888
- Role: 12px, regular, #888
- Date: 12px, regular, #888
- Card color accent (top border 4px):


- Submitted: Teal (#2A8F9D)
- In Review: Amber (#E5A832)
- Rejected: Red (#D94F4F)
- Hired: Green (#2D9F6F)
- Hover effect: Shadow increase, slight lift
- "View more" link: "[+ 6 more]" (12px, regular, #2A8F9D, clickable)
- Summary stats: "Total Submissions: 25 | Success Rate: 12% | Avg Time to Hire: 18 days" (12px, regular, #555, centered)

**Interaction:**

- Cards are draggable (visual hint: cursor changes to grab on hover)
- Dragging a card to a new column updates status
- Clicking a card opens detail modal
- "[+ more]" link expands column to show all cards
- Columns can be scrolled horizontally if many cards

**Emotional Tone:** Organized, visual, empowering. Jason sees his entire pipeline at a glance.

---

## Design System: Shared Components

### Button Styles

**Primary Button (Teal)**

- Background: #2A8F9D
- Text: White, 14px, bold
- Height: 48px
- Border-radius: 8px
- Padding: 0 24px
- Hover: Background darkens to #1E7A8A, shadow increases
- Active: Background darkens further, slight inset shadow
- Disabled: Background lightens to #A8D4DC, text grays out

**Secondary Button (Outline)**

- Background: Transparent
- Border: 2px solid #2A8F9D
- Text: #2A8F9D, 14px, bold
- Height: 48px
- Border-radius: 8px
- Padding: 0 24px
- Hover: Background lightens to #E8F4F8, border color darkens
- Active: Border color darkens, text darkens

**Small Button (Icon + Text)**

- Background: Transparent or light gray (#F5F7FA)
- Text: #2A8F9D, 12px, regular
- Height: 32px
- Border-radius: 6px
- Padding: 0 12px
- Hover: Background darkens, text darkens

### Input Fields

**Text Input**

- Background: White
- Border: 1px solid #D0D0D0
- Border-radius: 6px
- Padding: 12px 16px
- Font: 14px, regular, #2C3E50
- Placeholder: 14px, regular, #AAA
- Focus: Border color #2A8F9D, box-shadow: 0 0 0 3px rgba(42, 143, 157, 0.1)
- Error: Border color #D94F4F, error message below in red

**Textarea**

- Same as text input, but 120px minimum height
- Resize: Vertical only

### Cards

**Standard Card**

- Background: White
- Border-radius: 8px
- Box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08)
- Padding: 24px
- Hover: Box-shadow increases to 0 4px 16px rgba(0, 0, 0, 0.12)

**Accent Card (with left border)**

- Same as standard card, plus:
- Left border: 4px solid #2A8F9D (or status color)

### Progress Indicators

**Progress Bar**

- Background: #E0E0E0
- Fill: #2A8F9D
- Height: 8px
- Border-radius: 4px
- Animation: Smooth fill on update

**Circular Progress**

- Outer ring: Light gray (#E0E0E0), 8px stroke
- Inner ring: #2A8F9D, 8px stroke, percentage filled
- Center text: Percentage or label
- Animation: Ring fills smoothly on load

**Step Counter**

- Format: "Question 1 of 10"
- Font: 14px, regular, #555
- Position: Above progress bar

### Status Badges

**Strong Match**

- Background: #2D9F6F (green)
- Text: White, 12px, bold
- Padding: 6px 12px
- Border-radius: 20px
- Icon: ✓

**Partial Match**

- Background: #E5A832 (amber)
- Text: White, 12px, bold
- Padding: 6px 12px
- Border-radius: 20px
- Icon: ⚠

**Gap Detected**

- Background: #D94F4F (red)
- Text: White, 12px, bold
- Padding: 6px 12px
- Border-radius: 20px
- Icon: ✗

**In Progress**

- Background: #2A8F9D (teal)
- Text: White, 12px, bold
- Padding: 6px 12px
- Border-radius: 20px
- Icon: ✓

**Incomplete**

- Background: #E5A832 (amber)
- Text: White, 12px, bold
- Padding: 6px 12px
- Border-radius: 20px
- Icon: ⚠

---

## Interaction Patterns

### Loading States

**File Upload Progress**

```
Uploading Marcus_CV.pdf...
████████░░ 80%
```

- Progress bar animates smoothly
- Text updates in real-time
- Cancel button available

**Parsing Progress**

```
Parsing CVs...
✓ Extracted 5 positions
✓ Identified 12 projects
→ Analyzing data...
```

- Checkmarks appear as each step completes
- Arrow indicates current step
- Spinner on current step

**Generation Progress**

```
Generating Kandidatenprofile...
████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
40% complete
```

- Progress bar animates
- Percentage updates
- Estimated time remaining (optional)

### Hover & Focus States

**Card Hover**

- Box-shadow increases
- Slight scale (1.02x)
- Cursor changes to pointer (if clickable)

**Button Hover**

- Background color darkens
- Box-shadow increases
- Cursor changes to pointer

**Input Focus**

- Border color changes to teal (#2A8F9D)
- Box-shadow: 0 0 0 3px rgba(42, 143, 157, 0.1)
- Cursor appears in field

### Animations

**Fade-in**

- Duration: 300ms
- Easing: ease-out
- Used for: Modals, alerts, new content

**Slide-up**

- Duration: 300ms
- Easing: ease-out
- Distance: 20px
- Used for: Cards on load, alerts

**Progress Fill**

- Duration: 1000ms (for full bar)
- Easing: ease-in-out
- Used for: Progress bars, circular progress

**Smooth Transition**

- Duration: 200ms
- Easing: ease-in-out
- Used for: Color changes, shadow changes, hover states

---

## Accessibility Considerations

- **Color contrast:** All text meets WCAG AA standards (4.5:1 for body text, 3:1 for large text)
- **Focus indicators:** All interactive elements have visible focus states
- **Keyboard navigation:** All buttons and inputs are keyboard-accessible
- **Screen reader support:** All images have alt text, form labels are associated with inputs
- **Motion:** Animations respect `prefers-reduced-motion` setting
- **Text sizing:** All text is readable at 200% zoom

---

## Responsive Design Notes

**Desktop (1200px+)**

- Full layout as specified above
- Sidebar navigation visible
- Multi-column layouts (e.g., match matrix)

**Tablet (768px - 1199px)**

- Single-column layouts
- Cards stack vertically
- Buttons full-width
- Navigation collapses to hamburger menu

**Mobile (< 768px)**

- Single-column layout
- Cards stack vertically
- Buttons full-width
- Navigation collapses to hamburger menu
- Match matrix becomes scrollable table
- Kanban becomes vertical scroll

---

## Next Steps

1. **Create Figma components** based on these specifications
2. **Build interactive prototypes** for user testing
3. **Validate with personas** (especially Marcus, Priya, Emma, Jason)
4. **Iterate based on feedback** before development handoff
5. **Document component library** for engineering team

