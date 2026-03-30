
# Priya: The International Relocator (Regulated Industries)

## Context Snapshot

|Attribute|Value|
|---|---|
|Profile completeness|0% — first-time user|
|Trust level|Low-to-moderate — unfamiliar with DACH norms, uncertain what "good" looks like|
|Current situation|Secured offer or actively applying to pharma/biotech roles in Germany, Austria, or Switzerland|
|Time pressure|High — often tied to visa timelines, relocation deadlines, or active interview processes|
|Emotional baseline|Anxious about cultural missteps, confident in expertise but unsure how to present it|
|Primary JTBD|"Tell me what a German pharma employer expects — and reformat my experience accordingly"|
|LTV potential|Moderate-high (€40–80) — 3–5 CVs per search, likely one-time intense usage with potential return for future moves|

## Trigger

Priya has been working as a Regulatory Affairs Specialist at a biotech company in Hyderabad for 9 years. She's been offered an interview for a **Senior Regulatory Affairs Manager** role at a mid-sized pharma company in Frankfurt. The recruiter asked for her CV "in German market format."

She Googles:

- _"How to write a German CV for pharma jobs"_
- _"Should I include a photo on my German CV?"_
- _"How to present Indian degree in Germany"_

She finds conflicting advice everywhere. One blog says include a photo, another says don't. One says 2 pages max, another says 3–4 is fine for senior roles. None of them understand pharma-specific conventions.

She finds Apliqa via SEO (_"Bewerbung in regulierten Branchen"_) or a relocation forum recommendation.

She realizes:

1. Her current CV is a **5-page Indian format** with personal details (father's name, marital status, date of birth) that are inappropriate for DACH
2. She has **strong GxP experience** (ANVISA, WHO-GMP, ICH guidelines) but doesn't know how to map it to European regulatory frameworks
3. She has **no idea** what reverse-chronological Lebenslauf conventions look like for regulated industries
4. Manually researching and reformatting could take **days** — and she still might get it wrong

## Happy Path Flow

```mermaid
mermaidFileEditViewflowchart TD
    A[Land on Homepage] --> B[Create Account]
    B --> C[Onboarding: Upload CV Prompt]
    C --> D[Upload 1-2 CVs]
    D --> E[Smart Auto-Merge + Cultural Pre-Scan]
    E --> F[Master Profile Created ✓]
    F --> G{Ready to Tailor?}
    G -->|Yes - Have JD| H[Paste JD URL/Text]
    G -->|Not Yet| I[Dashboard + Cultural Readiness Score]
    H --> J[JD Analysis + Gap Detection + Cultural Gap Detection]
    J --> K[Prepare Unified Interview]
    K --> L[Interview: 8-12 Questions<br/>Gaps + Cultural Adaptation + Conflicts]
    L --> M[Profile Enriched + Culturally Adapted]
    M --> N[CV Preview — DACH Format]
    N --> O[Download PDF]
    O --> P[Dashboard: Application Logged]

    style E fill:#10b981,color:#fff
    style F fill:#10b981,color:#fff
    style L fill:#8b5cf6,color:#fff
    style M fill:#10b981,color:#fff

    classDef userAction fill:#f59e0b,color:#000
    class D,H,L,O userAction
```

## Step-by-Step Journey

#### **Step 1: Landing & Signup**

Priya lands on Apliqa via Google search or relocation forum link. The landing page speaks to her pain directly:

> _"Moving to Germany for a pharma role? Your CV needs more than a translation — it needs a cultural transformation."_

She clicks **"Get Started"**, creates account (email + password or SSO).

**Emotion:** Anxious → Hopeful — _"Finally, something that seems to understand my situation."_ **Time:** 2 minutes

#### **Step 2: CV Upload**

Onboarding screen appears:

> **"Let's build your Master Profile. Upload your existing CV(s) — we'll handle the rest."** _Upload 1–3 CVs or a LinkedIn PDF for the richest profile. We'll automatically merge and adapt them for the DACH market._

Priya uploads:

- `Priya_CV_2025.pdf` (5-page Indian format, includes personal details, references, declaration)
- `LinkedIn_Profile.pdf` (exported from LinkedIn, English, abbreviated)

**System displays:** Upload progress bars → "Parsing CVs..." → "Analyzing data..." → "Detecting source market conventions..."

**Emotion:** Hopeful → Curious **Time:** 3 minutes (upload + parsing)

#### **Step 3: Smart Auto-Merge + Cultural Pre-Scan (Backend)**

The system:

1. **Extracts all data** from uploaded documents (positions, projects, skills, certifications, education)
2. **Detects source market** based on CV structure, content patterns, and metadata:
    
    - Personal details section (father's name, marital status, DOB) → Indian market detected
    - Declaration at bottom ("I hereby declare...") → Indian convention confirmed
    - References listed upfront → Non-DACH pattern
    
3. **Flags cultural adaptation items** (stored in `master_profile.cultural_flags`):
    
    - PII to remove (father's name, marital status, declaration)
    - Photo recommendation (optional in DACH, but common in pharma — system will ask)
    - Format restructuring needed (functional → reverse-chronological)
    - Credential mapping needed (B.Tech from IIT → equivalent positioning for German HR)
    - Regulatory framework mapping (ANVISA/WHO-GMP → EU GMP/EMA equivalence)
    
4. **Auto-resolves non-controversial items** (e.g., removes declaration, strips father's name)
5. **Flags items requiring user input** (photo preference, credential presentation, regulatory mapping)

**Priya sees:**

> ✅ **Master Profile Created!**
> 
> - 4 positions extracted
> - 8 projects identified
> - 2 certifications added
> - 31 data points consolidated
> 
> 🌍 **Cultural Adaptation Detected** We identified your CV follows **Indian market conventions**. We'll adapt it for DACH pharma standards during the tailoring process — no manual research needed.
> 
> **Ready to tailor for a specific role?** [Yes — I have a job description] [Not yet — explore my profile]

**Emotion:** Impressed, Relieved — _"It actually detected that my CV is Indian format. I don't have to figure out what to change myself."_ **Time:** 30–45 seconds (feels instant)

**KEY DIFFERENCE FROM MARCUS:** The cultural pre-scan is Priya's unique value moment. Marcus gets "wow, it merged my 3 CVs." Priya gets "wow, it knows my CV is wrong for Germany and it's going to fix that."

#### **Step 4: Job Description Input**

Priya clicks **"Yes — I have a job description"** and is prompted:

> **What role are you applying for?** Paste the job URL or job description text:

Priya pastes the JD text from the recruiter's email (the company's career page is in German, but the JD itself is in English).

**System displays:** "Analyzing job description..." → "Mapping regulatory requirements..." → "Preparing your interview..."

**Emotion:** Engaged **Time:** 1 minute

#### **Step 5: Unified Interview (Gaps + Cultural Adaptation + Conflicts)**

**System presents:**

> **Let's tailor your CV for: Senior Regulatory Affairs Manager — Frankfurt**
> 
> We'll ask 10 questions to optimize your profile for this role and the DACH market. This will take about 8–10 minutes.
> 
> Your answers will: ✓ Adapt your experience for German pharma conventions ✓ Map your regulatory expertise to European frameworks ✓ Fill knowledge gaps specific to this role ✓ Position your international background as a strength
> 
> [Start Interview]

**Interview flow (example questions):**

##### **Question 1 (Cultural — Photo)**

> German pharma CVs typically include a **professional headshot**. This is optional but very common in regulated industries.
> 
> Would you like to include a photo? If yes, you can upload one after the interview. We'll ensure it meets DACH standards (professional, neutral background, business attire).

**Priya responds:** "Yes, I'd like to include one."

**System action:** Flags photo upload step after interview; stores preference.

##### **Question 2 (Cultural — Credential Mapping)**

> This role requires a **Master's degree in Life Sciences or equivalent**.
> 
> Your profile shows a **B.Tech in Biotechnology from IIT Madras** and an **M.Sc. in Pharmaceutical Sciences from NIPER**.
> 
> For German HR, we'll present these as:
> 
> - "M.Sc. Pharmaceutical Sciences — NIPER (equivalent to German Diplom)"
> - "B.Tech Biotechnology — IIT Madras (India's premier technical institute)"
> 
> Does this accurately represent your qualifications? Any additional context we should include (e.g., thesis topic, honors)?

**Priya responds:** "Yes, that's correct. My M.Sc. thesis was on ICH Q8 Quality by Design for oral solid dosage forms."

**System action:** Enriches education section with thesis topic; stores credential mapping.

##### **Question 3 (Gap — Regulatory Framework Mapping)**

> This role emphasizes **EU GMP and EMA regulatory submissions**.
> 
> Your experience includes **ANVISA (Brazil-facing exports), WHO-GMP, and ICH guidelines**. These are highly relevant but need to be positioned for a European audience.
> 
> Can you describe any direct interaction with **EU regulatory frameworks**? For example:
> 
> - EMA submissions or consultations
> - EU GMP audit preparation
> - CE marking or EU MDR experience
> - Mutual Recognition Agreements (MRA) work

**Priya responds:** "I led the preparation for an EU GMP audit at our Hyderabad facility in 2023. We also submitted two CTD dossiers to EMA via our EU partner. I'm familiar with MRA frameworks between India and EU."

**System action:** Adds EU-facing regulatory experience to profile; maps ANVISA experience as "international regulatory expertise including EU GMP compliance."

##### **Question 4 (Gap — Language)**

> The job description is in English, but the company is based in Frankfurt.
> 
> What is your **German language proficiency**? (e.g., A1, B1, B2, fluent) If you're currently learning, we can position this positively (e.g., "German B1, actively pursuing B2").

**Priya responds:** "I'm at B1 level, taking intensive courses. Aiming for B2 by September."

**System action:** Adds language section with strategic positioning: "German: B1 (B2 certification targeted Q3 2026), English: Fluent (working language), Hindi: Native, Tamil: Native."

##### **Question 5 (Cultural — Work Authorization)**

> For DACH applications, employers often want to understand **work authorization status** upfront.
> 
> What is your current visa/work permit situation?
> 
> - EU Blue Card (applied/approved)
> - Work permit via employer sponsorship
> - EU citizenship
> - Other

**Priya responds:** "The company is sponsoring my EU Blue Card. Application is in process."

**System action:** Adds to profile metadata; positions in CV as "Work authorization: EU Blue Card (employer-sponsored, in process)."

##### **Question 6 (Gap — Team Leadership)**

> This role requires **management of a 5-person regulatory affairs team**.
> 
> Your profile shows project leadership but doesn't explicitly mention **direct reports or team management**.
> 
> Have you managed direct reports? If so, how many, and in what capacity?

**Priya responds:** "I managed a team of 3 regulatory associates and 2 documentation specialists for the last 2 years. I also mentored 4 junior scientists."

**System action:** Enriches profile with team leadership data; positions for DACH expectations.

##### **Question 7 (Gap — Specific Regulatory Expertise)**

> The JD mentions **Variations (Type IA, IB, II) and renewal submissions**.
> 
> Can you describe your experience with post-approval regulatory activities in any market? We'll map it to the EU variation framework.

**Priya responds:** _(details added)_

##### **Question 8 (Cultural — Availability)**

> German applications sometimes include **availability date** or **notice period** (Kündigungsfrist).
> 
> When would you be available to start? Should we include this in your CV?

**Priya responds:** "Available from July 2026. Yes, please include it."

##### **Questions 9–10:** Additional gap questions based on JD requirements (e.g., GxP documentation systems, audit experience specifics)

**Progress shown throughout:** "Question 7 of 10 — Adapting your profile for the DACH pharma market"

**Emotion:** Educated, Empowered — _"I'm learning what German pharma employers actually care about WHILE building my CV. These questions are teaching me things no blog could."_

**Time:** 8–10 minutes

#### **Step 6: CV Generation**

After interview completion:

> ✅ **Interview Complete!** Generating your DACH-formatted CV... (15 seconds)

**System:**

- Updates Master Profile with all interview answers
- Applies DACH cultural rules:
    
    - Reverse-chronological format
    - Professional photo placeholder (if opted in)
    - Proper credential mapping
    - Language section with strategic positioning
    - Work authorization line
    - Removed: declaration, father's name, marital status, references section
    
- Runs tailoring engine using enriched profile + JD
- Maps regulatory frameworks (ANVISA → EU GMP equivalence language)
- Emphasizes EU-facing experience (EMA submissions, EU GMP audit)
- Generates DACH-formatted CV

**Priya sees CV preview in browser**

**Emotion:** Amazed → Confident — _"This looks completely different from my original CV. It looks... German. Professional. Like I belong in this market."_

**Time:** 1–2 minutes (review)

#### **Step 7: Download & Complete**

Priya clicks **"Download PDF"**

**System:**

- Generates PDF using WeasyPrint (ADR 006)
- Logs application in dashboard
- Shows confirmation:
    
    > **"CV saved! Your profile is now optimized for the DACH pharma market."** _Future applications will be even faster — your cultural adaptations are saved._
    

Priya downloads PDF, reviews, sends to recruiter.

**Emotion:** Relieved, Empowered — _"This took 25 minutes. I would have spent DAYS researching and still gotten it wrong. And now my profile is ready for the next application too."_

**Time:** 1 minute

**Total journey time: ~25 minutes**

---

## Branching Scenarios

#### **Branch A: Priya Has No JD Yet — Exploring the Market**

**Flow:**

1. After Master Profile creation, Priya clicks **"Not yet — explore my profile"**
2. Dashboard shows:
    
    - Profile completeness: 68%
    - **Cultural Readiness Score: 45%** ← _Priya-specific metric_
        
        > "Your profile has strong content but needs cultural adaptation for the DACH market. Tailor for a specific role to unlock full adaptation."
        
    - Suggested improvements:
        
        - "Add German language proficiency"
        - "Upload a professional photo"
        - "Clarify work authorization status"
        
    - "New Application" button for later
    
3. **Cultural flags remain unresolved** — stored in backend
4. When Priya returns with a JD, cultural adaptation surfaces in interview alongside gaps

**Design rationale:**

- The Cultural Readiness Score gives Priya a clear signal that her profile needs work — without overwhelming her
- Quick-win suggestions (language, photo, work auth) can be addressed without a JD
- Deep cultural adaptation (credential mapping, regulatory framework translation) waits for JD context

**Emotion:** Informed → Motivated to return with a JD

#### **Branch B: CV Language Mismatch — JD in German, CV in English**

**Flow:**

1. Priya pastes a JD that's entirely in German
2. System detects language mismatch:
    
    > "This job description is in **German**. Your profile is in **English**."
    > 
    > For this application, should we:
    > 
    > - **Generate CV in English** (common for international pharma roles, even in Germany)
    > - **Generate CV in German** (preferred for some employers — requires B2+ German)
    > 
    > _Recommendation: For regulatory affairs roles at international pharma companies in Frankfurt, an English CV is typically accepted. We'll include your German language skills prominently._
    
3. Priya selects English (or German if confident)
4. Interview proceeds with language-aware questions

**Design rationale:**

- Don't assume — ask, but provide a clear recommendation
- The system's recommendation demonstrates cultural intelligence (this IS the value prop)
- For V2: automatic German CV generation with professional translation layer

**Emotion:** Uncertain → Guided — _"I didn't even know I had to make this choice. The recommendation makes sense."_

#### **Branch C: Credential Recognition Uncertainty**

**Flow:**

1. During interview, Priya mentions a degree the system can't confidently map
2. System responds:
    
    > "We're not certain how German HR would evaluate your **Post Graduate Diploma in Regulatory Affairs from RAPS India**."
    > 
    > Options:
    > 
    > - Present as "Post Graduate Diploma in Regulatory Affairs (RAPS India)" with brief description
    > - If you have a **credential evaluation** from anabin or KMK, we can reference the German equivalence
    > - We'll include it either way — international certifications from recognized bodies are valued in pharma
    
3. Priya provides context; system stores mapping for future use

**Design rationale:**

- Honest about uncertainty — builds trust
- Provides actionable options
- Never drops data — includes credential regardless

**Emotion:** Worried → Reassured — _"At least it's honest about what it doesn't know, and it still includes my qualification."_

#### **Branch D: Priya Uploads a CV in a Non-Latin Script**

**Flow:**

1. Priya uploads a CV partially in Hindi or another non-Latin script
2. System detects non-Latin content:
    
    > "We detected content in a **non-Latin script** in your upload. Our parsing works best with English, German, or other Latin-script documents."
    > 
    > "Please upload an **English or German version** of your CV, or paste your career details manually."
    
3. Fallback: guided interview to build profile from scratch (same as Marcus Branch D)

**Design rationale:**

- Graceful handling of a realistic edge case for international users
- Clear recovery path
- No dead-end

**Emotion:** Frustrated → Relieved — _"Okay, I'll use my English version."_

#### **Branch E: Priya Abandons Mid-Interview**

**Resume flow:**

1. Priya returns to dashboard
2. Card shows: **"Incomplete: Senior Regulatory Affairs Manager"**
3. She clicks the card → sees:
    
    - **CV Preview** (generated with current data — already culturally adapted for resolved items)
    - **Remaining Gaps Panel**:
        
        > "Your CV is ready, but we identified **3 additional items** that could strengthen it for this role:"
        > 
        > - Work authorization status _(cultural)_
        > - Availability / start date _(cultural)_
        > - Specific experience with EU variation submissions _(gap)_
        > 
        > [Address remaining gaps] [Download CV as-is]
        
    
4. If she clicks **"Address remaining gaps"**:
    
    - New interview session opens with only the 3 remaining questions
    - Progress shows: "Question 1 of 3 — Finalizing your DACH adaptation"
    - After completion: CV regenerates with enriched data
    
5. If she clicks **"Download CV as-is"**:
    
    - PDF downloads immediately
    - Gaps remain stored in profile for future reference
    - She can return later to address them if desired
    

**Design rationale:**

- Immediate value: Priya gets a usable CV even if she didn't finish
- Transparency: She sees exactly what's missing and why it matters
- Agency: She chooses whether to invest more time or proceed with current state
- No dead-end: Gaps are preserved; she can address them later

**Emotion:** Relieved — _"I can see my CV right now. The gaps are optional. I'm not stuck."_

#### **Branch F: Priya is Relocating from the US (Minimal Cultural Delta)**

**Flow:**

1. System detects US-format CV (1-page resume, no photo, no personal details)
2. Cultural pre-scan flags:
    
    - Format: needs expansion (1 page → 2–3 pages for senior pharma roles in DACH)
    - Photo: recommend adding
    - Personal details: add date of birth (still common in DACH pharma, though declining)
    - Content: likely already strong on regulatory substance
    
3. Interview is shorter (6–8 questions) — less cultural adaptation needed, more gap-focused

**Design rationale:**

- Cultural adaptation intensity scales with the delta between source and target market
- US → DACH is a smaller jump than India → DACH
- System should be smart enough to calibrate

**Emotion:** Efficient — _"Quick and targeted. It knew I didn't need the full cultural overhaul."_

---

## Emotional Journey

```smalltalk
FileEditView[Anxious]      →  "Will I get this wrong? Every blog says something different."
    ↓
[Hopeful]      →  "This tool seems to understand pharma + DACH specifically."
    ↓
[Relieved]     →  "It detected my CV is Indian format. I don't have to figure this out alone."
    ↓
[Educated]     →  "The interview questions are teaching me what German pharma employers expect."
    ↓
[Empowered]    →  "I'm making informed decisions about how to present my experience."
    ↓
[Amazed]       →  "My CV looks completely different. Professional. Like I belong."
    ↓
[Confident]    →  "I can send this to the recruiter without second-guessing myself."
    ↓
[Advocacy]     →  Posts in relocation WhatsApp group: "Use this tool before applying in Germany."
```

**Critical achievement:** The emotional arc transforms **anxiety about cultural missteps** into **confidence through education**. Priya doesn't just get a CV — she learns what DACH pharma employers expect. That knowledge is the real product.

**Key difference from Marcus:** Marcus's arc is Skeptical → Impressed (efficiency). Priya's arc is Anxious → Empowered (knowledge). The emotional stakes are higher for Priya because she's navigating unfamiliar territory.

---

## Cultural Adaptation Patterns

### **Pattern 1: PII Removal (Automatic)**

|Source Market Item|DACH Action|Confidence|Auto-Resolve?|
|---|---|---|---|
|Father's name|Remove|99%|✅ Yes|
|Marital status|Remove|95%|✅ Yes|
|Declaration ("I hereby declare...")|Remove|99%|✅ Yes|
|References section|Remove (available on request)|90%|✅ Yes|
|Date of birth|Keep (still common in DACH pharma)|80%|✅ Yes|
|Nationality|Keep (relevant for work authorization context)|85%|✅ Yes|
|Religion|Remove|99%|✅ Yes|

### **Pattern 2: Structural Transformation**

|Source Convention|DACH Pharma Convention|Transformation|
|---|---|---|
|Functional/skills-based format|Reverse-chronological|Restructure positions by date (newest first)|
|1-page resume (US)|2–3 pages for senior roles|Expand with project details, certifications|
|5-page CV (India)|2–3 pages, focused|Condense; prioritize relevance to target role|
|Objective statement|Professional summary (optional)|Rewrite as 2–3 sentence positioning statement|
|References listed|"References available on request" or omit|Remove; add line if space permits|

### **Pattern 3: Regulatory Framework Mapping**

|Source Framework|DACH/EU Equivalent|Mapping Language|
|---|---|---|
|ANVISA (Brazil)|EU GMP, EMA|"International regulatory experience including ANVISA (Brazilian equivalent to EMA)"|
|FDA 21 CFR|EU GMP Annex 11|"Electronic records compliance (21 CFR Part 11 / EU GMP Annex 11)"|
|WHO-GMP|EU GMP|"WHO-GMP compliance (aligned with EU GMP standards)"|
|CDSCO (India)|EMA|"CDSCO regulatory submissions (comparable to EMA CTD format)"|
|TGA (Australia)|EMA (MRA)|"TGA submissions under EU-Australia MRA framework"|
|ICH guidelines|ICH guidelines|Direct equivalence — no mapping needed|

### **Pattern 4: Credential Mapping**

|Source Credential|DACH Presentation|Notes|
|---|---|---|
|B.Tech (IIT, India)|"B.Tech [Field] — [University] (India's premier technical institute)"|Add context for recognition|
|M.Sc. (NIPER, India)|"M.Sc. [Field] — NIPER (equivalent to German Diplom)"|Map to German equivalence|
|PharmD (US)|"Doctor of Pharmacy (PharmD) — [University]"|Well-recognized in DACH pharma|
|Bacharelado (Brazil)|"Bachelor's degree [Field] — [University], Brazil"|Simplify for German HR|
|anabin-evaluated degree|Include anabin reference|Strongest possible positioning|

---

## Exit Conditions

|Exit Type|Trigger|System State|Next Action|
|---|---|---|---|
|Happy exit|PDF downloaded, logged to dashboard|CV record created, cultural adaptations saved, flow step = "complete"|Return to dashboard or close tab|
|Deferred exit|Browser closed mid-flow|Session preserved in flow_sessions + interview_sessions + cultural_context|Resume via "Incomplete" card on dashboard|
|Abandon exit|Priya leaves without downloading|Draft CV saved (90-day TTL), cultural adaptations preserved, flow step = "cv_generation"|Appears in dashboard as "Incomplete"|
|Exploration exit|Priya clicks "Not yet" after profile creation|Master Profile created, cultural flags stored, no JD analyzed|Dashboard shows Cultural Readiness Score + suggestions|

---

## Touchpoint Inventory

|Screen/Component|Purpose|Priya Interaction|Technical Reference|
|---|---|---|---|
|**Landing Page**|Value prop — cultural adaptation messaging|Read, click "Get Started"|Static marketing site (SEO: "German CV pharma")|
|**Signup/Login**|Account creation|Email/password or SSO|POST /api/auth/register|
|**Onboarding Prompt**|CV upload instructions|Upload 1–3 CVs|POST /api/cv/upload (ADR 014)|
|**Upload Screen**|Drag-drop or file picker|Select files, confirm upload|Multipart form, progress bar|
|**Parsing Progress**|Real-time feedback + cultural detection|Wait, watch progress|WebSocket or polling /api/cv/{id}/status|
|**Cultural Pre-Scan (Backend)**|Source market detection, flag items|None — happens automatically|Backend cultural detection logic|
|**Profile Created Screen**|Success confirmation + cultural note|Review summary, click "Tailor for role"|GET /api/profile/summary|
|**JD Input Modal**|URL or text entry|Paste JD URL/text, submit|POST /api/job/analyze|
|**Interview Intro**|Set expectations (cultural + gaps)|Read estimate, click "Start"|GET /api/interview/{id}/intro|
|**Interview Chat UI**|8–12 questions, cultural + gaps|Answer free-text, submit each|POST /api/session/{id}/message|
|**Interview Progress**|Shows "Question X of Y — Adapting for DACH"|Track progress|Client-side state|
|**CV Preview (iframe)**|WYSIWYG HTML preview — DACH format|Scroll, review, click "Download"|GET /api/cv/{id}/html|
|**PDF Download**|Final artifact|Download, done|GET /api/cv/{id}/pdf|
|**Dashboard**|Profile status, Cultural Readiness Score, applications|Navigate, click "New Application"|GET /api/flow (list user flows)|
|**Resume Flow Card**|For abandoned interviews|Click "Resume" to continue|GET /api/flow/{id}/state|
|**Cultural Readiness Score**|Dashboard metric for Priya|View, click to see suggestions|GET /api/profile/cultural_readiness|
|**Photo Upload**|Post-interview step (if opted in)|Upload professional headshot|POST /api/profile/photo|

---

## Design Principles

|Principle|Rationale|Implementation|
|---|---|---|
|**Cultural detection is a feature**|Priya's "wow moment" is the system knowing her CV is wrong for DACH|Auto-detect source market; surface in Profile Created screen|
|**Education, not just execution**|Priya needs to understand WHY changes are made|Interview questions explain DACH norms contextually|
|**Source market calibration**|India → DACH needs more adaptation than US → DACH|Interview length and content scale with cultural delta|
|**Regulatory framework translation**|International experience is a strength, not a gap|Map ANVISA/WHO-GMP to EU equivalents; position as asset|
|**Credential mapping with honesty**|Don't overclaim equivalence; provide options|Ask in interview; offer anabin reference if available|
|**Language as a strategic choice**|English vs German CV is a real decision|Detect JD language; recommend; let Priya choose|
|**Work authorization visibility**|Critical for international candidates|Always ask; include prominently in CV|
|**Photo as optional but guided**|Cultural norm, not requirement|Ask preference; provide DACH photo standards|
|**Cultural Readiness Score**|Gives Priya a clear progress metric|Dashboard shows % adapted for DACH; suggestions for improvement|
|**State survives interruption**|Relocation is chaotic; Priya may be pulled away|Backend-stateful design (ADR 004); resume from any point|

---

## Open Questions

| #   | Question                                                                                                                                                    | Impact                    | Status         |
| --- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------- | -------------- |
| 1   | **Cultural Readiness Score calculation:** What factors weight the score? (PII removal, format, credentials, regulatory mapping, language, photo, work auth) | Dashboard metric design   | Open           |
| 2   | **Source market detection accuracy:** What happens if system misidentifies source market? Manual override?                                                  | Trust, error recovery     | Open           |
| 3   | **Regulatory framework mapping confidence:** When is mapping "safe" vs. "needs user input"?                                                                 | Interview question design | Open           |
| 4   | **Credential mapping database:** Do we need a pre-built mapping table for common credentials (IIT, NIPER, etc.)?                                            | Interview efficiency      | Open           |
| 5   | **German CV generation (V2):** Should we offer automatic translation? What quality threshold?                                                               | Feature scope, LLM costs  | Deferred to V2 |
| 6   | **Photo upload UX:** Inline during interview or post-interview step?                                                                                        | Flow design               | Open           |
| 7   | **Cultural adaptation templates:** Do we need market-specific templates (India→DACH, Brazil→DACH, US→DACH)?                                                 | CV generation logic       | Open           |
| 8   | **Multi-market targeting:** What if Priya is applying to both Germany and Switzerland?                                                                      | Profile flexibility       | Open           |

---

## Success Metrics

| Metric                                 | Target                                     | Measurement                                                                                   |
| -------------------------------------- | ------------------------------------------ | --------------------------------------------------------------------------------------------- |
| **Time to first CV**                   | <30 minutes (including cultural interview) | Track from signup to PDF download                                                             |
| **Cultural interview completion rate** | >80%                                       | % of users who finish interview once started                                                  |
| **Cultural adaptation satisfaction**   | >4.0/5.0                                   | Post-download survey: "How well does this CV fit DACH pharma expectations?"                   |
| **Source market detection accuracy**   | >90%                                       | Manual audit of detected vs. actual source market                                             |
| **Credential mapping accuracy**        | >85% user satisfaction                     | Survey: "Did we present your qualifications correctly for German HR?"                         |
| **Return rate**                        | >40% within 60 days                        | % of users who generate 2+ CVs (lower than Marcus/Emma — Priya may be one-time intense usage) |
| **Referral rate**                      | >15% mention to others                     | Post-download survey: "Would you recommend this to others relocating to DACH?"                |

---

**Key Takeaway:** Priya's journey is fundamentally about **education and empowerment**, not just efficiency. She arrives anxious about cultural missteps; she leaves confident that she understands DACH pharma expectations. The interview is her learning experience — every question teaches her something about her target market. That's the product.