# Jason - Headhunter
## Context Snapshot

|Attribute|Value|
|---|---|
|Profile completeness|N/A — manages candidate profiles, not his own|
|Trust level|Very skeptical — has tried "AI recruitment tools" that failed|
|Current situation|5-15 open mandates, 3-5 new CVs arriving daily|
|Time pressure|HIGH — every hour formatting is lost revenue|
|Emotional baseline|Frustrated by "reformatting tax," needs speed + quality|
|Primary JTBD|"Turn this CV into a branded Kandidatenprofil in 2 minutes"|
|LTV potential|VERY HIGH (€3,000-€12,000/year) — B2B team plan + API credits|

## Trigger

Jason receives a candidate CV via email:

> Subject: **Application - QA Manager Position** Attachment: `Marcus_Hoffmann_CV.pdf`

He also has a client mandate:

> **Roche Basel** - Director of Validation, €140k-€170k, GMP/GAMP 5 required

Jason's current workflow:

1. Open candidate CV (usually generic format, 2-3 pages)
    
2. Open his agency's Word template (`Kandidatenprofil_Template.docx`)
    
3. Copy-paste candidate details, reformatting manually
    
4. Highlight relevant GxP experience (based on his own judgment)
    
5. Add agency branding (logo, footer, confidentiality notice)
    
6. Save as PDF, upload to Starhunter CRM
    
7. Email to client
    

**Time cost:** 30-60 minutes per profile **Daily volume:** 3-5 profiles = **2.5-5 hours of formatting work**

He Googles: _"AI Kandidatenprofil generator for recruiters Germany"_ → finds Apliqa B2B.

## Happy Path Flow

Jason lands on Apliqa B2B page (targeted LinkedIn ad or Google search), clicks "Book Demo" or "Start Free Trial", creates a B2B account (company name, VAT ID optional, team size). The system prompts: "Create your agency profile - upload your Kandidatenprofil template and branding assets."

Jason uploads:

- Agency logo (PNG)
    
- Kandidatenprofil template (DOCX with placeholder fields)
    
- Brand colors (hex codes auto-detected from logo)
    

The system confirms: "Agency profile ready. Upload a candidate CV to get started."

Jason drags `Marcus_Hoffmann_CV.pdf` into the upload zone. The system parses the CV and creates a candidate Master Profile in Jason's workspace. It presents a preview: "Candidate profile created: Marcus Hoffmann, QA Manager, 15 years pharma experience."

Jason then clicks "Tailor for Mandate" and selects the Roche Basel JD from his active mandates list (or pastes a new JD). The system analyzes the JD against Marcus's profile and presents: "Match Score: 82%. Strong fit for Director of Validation. Key strengths: GAMP 5, MES validation, FDA audit experience."

The system generates a branded Kandidatenprofil using Jason's template, auto-filling candidate details and prioritizing GMP/GAMP experience. Jason reviews the preview in browser (his agency's branding, professional layout, 2 pages). He notices the system highlighted Marcus's "blood bank 21 CFR Part 11 work" — something he'd missed in the original CV.

Jason makes one minor edit (adjusts a job title for clarity), then clicks "Download PDF." The Kandidatenprofil downloads with filename: `Kandidatenprofil_Marcus_Hoffmann_Director_Validation_Roche.pdf`. The system logs: "Submitted to: Roche Basel - Director of Validation" and prompts: "Track in pipeline?"

Jason clicks "Yes" — the submission is logged to his dashboard with status "Submitted - Awaiting Response."

**Total time:** 5 minutes (vs. 45 minutes manually).

flowchart TD
    A[Land on B2B Page] --> B[Sign Up: B2B Account]
    B --> C[Agency Profile Setup]
    C --> D[Upload: Logo + Template + Branding]
    D --> E[Agency Profile Complete]
    E --> F[Dashboard: Active Mandates View]
    F --> G{Action}
    G -->|New Candidate| H[Upload Candidate CV]
    G -->|Batch Review| I[Upload Multiple CVs]
    H --> J[Parse CV → Master Profile]
    J --> K[Candidate Profile Preview]
    K --> L{Next Action}
    L -->|Tailor| M[Select Mandate/JD]
    L -->|Store Only| N[Save to Candidate Pool]
    M --> O[JD Analysis]
    O --> P[Match Score + Key Strengths]
    P --> Q[Generate Kandidatenprofil]
    Q --> R[Preview: Branded Template]
    R --> S{Review}
    S -->|Edit| T[Inline Edits]
    S -->|Approve| U[Download PDF]
    T --> U
    U --> V[Log Submission to Pipeline]
    V --> W[Dashboard Updated]
    
    I --> X[Batch Parse: 5-10 CVs]
    X --> Y[Match Against Active Mandates]
    Y --> Z[Ranked List: Best Fits]
    Z --> M
```

## Branching Scenarios

### **Branch A: Anonymized Submission (Blind Mandate)**

|Step|System Response|Jason's Action|Outcome|
|---|---|---|---|
|Kandidatenprofil gen|"Generate anonymized profile? (removes name, photo, contact details)"|Toggles "Anonymize" switch ON|System strips PII but preserves all experience data|
|Preview|Kandidatenprofil shows: "Candidate Profile: Anonymous - QA Manager, 15y exp"|Reviews, confirms anonymization|Professional anonymization (not just redacted text)|
|Download|Filename: `Kandidatenprofil_Anonymous_Director_Validation_Roche.pdf`|Downloads and submits|Client receives blind profile|

> **UX Principle:** One-click anonymization. Jason uses this for 30-40% of mandates — it must be frictionless.

### **Branch B: Batch Processing (8 CVs × 3 Mandates)**

|Step|System Response|Jason's Action|Outcome|
|---|---|---|---|
|Upload|"Upload multiple CVs" → Jason drags 8 PDFs|Batch upload|All 8 CVs parsed in parallel|
|Mandate selection|"Match against: Roche Basel (Director), Novartis (QA Manager), BioNTech (CSV Lead)"|Selects all 3 mandates|System runs 8 × 3 = 24 match analyses|
|Results matrix|Table showing: Candidate × Mandate with match scores (e.g., Marcus → Roche = 82%)|Reviews top matches|Identifies 5 strong fits (>75%)|
|Bulk generation|"Generate Kandidatenprofile for 5 selected matches?"|Clicks "Generate All"|5 Kandidatenprofile generated in <2 minutes|
|Review queue|Jason reviews each profile individually|Approves 4, edits 1, rejects 1|4 profiles downloaded and submitted|

> **UX Principle:** Batch is where Jason's ROI explodes. This feature alone justifies the B2B pricing.

**Branch C: Candidate Profile Already Exists (Returning Candidate)**

|Step|System Response|Jason's Action|Outcome|
|---|---|---|---|
|Upload CV|"Candidate detected: Marcus Hoffmann (last updated 3 months ago). Update profile or use existing?"|Chooses "Update profile"|System merges new CV with existing Master Profile|
|Merge preview|"2 changes detected: New certification (Lean Six Sigma), Updated job title"|Reviews, approves merge|Master Profile enriched|
|Generate|New Kandidatenprofil generated with updated data|Downloads|Always uses latest candidate data|

> **UX Principle:** Jason's candidate pool is his most valuable asset. Apliqa becomes his single source of truth.

### **Branch D: Low Match Score (<60%) - Jason Decides**

|Step|System Response|Jason's Options|Default Behavior|
|---|---|---|---|
|Match result|"Match Score: 54%. Weak fit for this mandate. Key gaps: No GAMP 5 experience listed"|View gaps, proceed anyway, or skip|Warning shown; Jason can override|
|Override|Jason knows Marcus has GAMP 5 (not in CV) — clicks "Proceed Anyway"|Kandidatenprofil generated with "Partial Match" note|System trusts Jason's judgment|
|Manual enrichment|Jason adds note: "Candidate has GAMP 5 (verbal confirmation)"|Note saved to Master Profile|Future matches will include this intelligence|

> **UX Principle:** Jason is the domain expert. System advises, but never blocks him. His overrides enrich the candidate profile.

### **Branch E: Kaile (AI Agent) Delegation**

|Step|System Response|Kaile's Action|Jason's Oversight|
|---|---|---|---|
|API call|Kaile receives: 3 candidate CVs + 1 JD via Apliqa API|Parses CVs, runs match analysis|None (fully automated)|
|Match results|Kaile identifies: Candidate B = 89% match (best fit)|Generates Kandidatenprofil for Candidate B only|None|
|Return to Jason|Kaile posts: "Top candidate identified: Kandidatenprofil ready for review"|—|Jason reviews, approves, submits|
|Pipeline update|Kaile logs submission to Jason's dashboard via API|—|Jason sees "Submitted by Kaile" in dashboard|

> **UX Principle:** Kaile handles routine work. Jason handles client relationships and final decisions.

### **Branch F: GDPR Consent Capture (First-Time Candidate)**

|Step|System Response|Jason's Action|Outcome|
|---|---|---|---|
|CV upload|"GDPR notice: Candidate consent required. Send consent email or upload signed consent form?"|Clicks "Send consent email"|Automated email sent to candidate|
|Consent email|Candidate receives: "Your recruiter (Jason's Agency) wants to process your CV. Accept?"|Candidate clicks "I consent"|Consent logged; Jason can proceed|
|Consent declined|Candidate clicks "I do not consent"|Jason notified: "Candidate declined consent"|CV processing blocked; Jason must obtain manual consent|

> **UX Principle:** GDPR compliance is built-in, not bolted on. Jason is the data controller; Apliqa is the processor.

## Emotional Journey

```css
FileEditView[Skeptical] → [Curious] → [Impressed] → [Validated] → [Relieved] → [Delighted] → [Dependent]
     ↑                                                                                  ↓
     └────────────────── [Advocate] - refers other recruiters ──────────────────────────┘
```

|Beat|Trigger|Jason's Feeling|
|---|---|---|
|Skepticism|"AI for recruiters" — has heard this before, all failed|Defensive, unconvinced|
|Curiosity|Agency branding upload — "Wait, this actually understands my workflow"|Intrigued, willing to test|
|First success|First Kandidatenprofil generated in 5 minutes — quality is good|Surprised, cautiously optimistic|
|Validation|System surfaces "blood bank = 21 CFR Part 11" — better than he caught|Impressed, trusts system intelligence|
|Relief|Batch processing 8 CVs × 3 mandates in <10 minutes — saved 4 hours|Liberated, can focus on client calls|
|Delight|Month 1: Generated 100+ Kandidatenprofile, closed 2 extra placements|Converted, increased revenue|
|Dependency|Month 3: Can't imagine going back to manual formatting|Loyal, high retention|
|Advocacy|Refers 3 other boutique agencies — "You need this tool"|Evangelist, drives B2B growth|

## Exit Conditions

|Exit Type|Trigger|System State|Next Action|
|---|---|---|---|
|**Happy exit**|Kandidatenprofil downloaded, submitted to client|Candidate profile saved, submission logged, pipeline updated|Return for next candidate or mandate|
|**Batch complete**|All profiles reviewed and submitted|Multiple candidates processed, dashboard shows submissions|Close session or continue with new batch|
|**Store only**|Candidate profile created but not submitted|Master Profile saved in Jason's pool, no submission logged|Profile available for future mandates|
|**Interrupted**|Browser closed mid-generation|Candidate profile saved, draft Kandidatenprofil in temp storage|Resume via dashboard "Incomplete" card|
|**Abandon**|Candidate consent declined|CV data deleted (GDPR compliance), no profile created|Jason must obtain manual consent to proceed|

## Touchpoint Inventory

|Screen/Component|Purpose|Jason's Interaction|Technical Reference|
|---|---|---|---|
|**B2B Landing Page**|Value prop for recruiters, demo booking|Read, click "Start Free Trial"|Static marketing site|
|**B2B Signup**|Company account creation|Enter company name, email, password|POST /api/b2b/auth/register|
|**Agency Profile Setup**|Upload branding assets|Upload logo, template, set brand colors|POST /api/b2b/agency/profile|
|**Dashboard: Mandates View**|Active client mandates list|View, add new mandate, select for matching|GET /api/b2b/mandates|
|**Candidate Upload**|Single or batch CV upload|Drag-drop CVs|POST /api/b2b/candidate/upload (multipart)|
|**Candidate Pool**|All stored candidate profiles|Search, filter, view details|GET /api/b2b/candidates|
|**Match Analysis**|Candidate vs. Mandate scoring|Review match scores, view gaps|POST /api/b2b/match|
|**Batch Match Matrix**|Table: Candidates × Mandates with scores|Sort, filter, select best matches|POST /api/b2b/match/batch|
|**Kandidatenprofil Generator**|Branded profile creation|Review, edit, approve|POST /api/b2b/kandidatenprofil/generate|
|**Anonymization Toggle**|Enable/disable PII removal|Toggle switch|Query param: ?anonymize=true|
|**Preview (iframe)**|Branded Kandidatenprofil preview|Scroll, review, click "Download"|GET /api/b2b/kandidatenprofil/{id}/html|
|**PDF Download**|Final submission artifact|Download, submit to client|GET /api/b2b/kandidatenprofil/{id}/pdf|
|**Pipeline Dashboard**|Submission tracking (status, dates, clients)|View, update status, add notes|GET /api/b2b/pipeline|
|**GDPR Consent UI**|Send consent email or upload signed form|Click "Send Email" or upload PDF|POST /api/b2b/consent/request|
|**Settings: API Keys**|Generate API keys for Kaile integration|Click "Generate Key", copy|POST /api/b2b/api-keys|
|**Billing: Credits Dashboard**|Usage tracking, credit balance, invoices|View usage, buy more credits|GET /api/b2b/billing|

## Design Principles

| Principle                            | Rationale                                                    | Implementation                                                     |
| ------------------------------------ | ------------------------------------------------------------ | ------------------------------------------------------------------ |
| **Speed is revenue**                 | Every minute saved = more client-facing time                 | Kandidatenprofil generation <5 min; batch processing optimized     |
| **Jason's judgment is sacred**       | He's the domain expert; system advises, never blocks         | Low match warnings (not blocks); override options always available |
| **Branding is non-negotiable**       | His agency's reputation depends on professional presentation | Full template customization; logo, colors, layout control          |
| **Batch is the killer feature**      | 8 CVs × 3 mandates = 24 manual comparisons → automated       | Matrix view, bulk generation, parallel processing                  |
| **GDPR is built-in, not bolted on**  | Jason is legally liable; compliance can't be an afterthought | Consent capture workflow, audit logs, deletion enforcement         |
| **Pipeline visibility is essential** | Jason juggles 15+ mandates; needs single source of truth     | Dashboard shows all submissions, statuses, and next actions        |
| **Kaile delegation is opt-in**       | Not all recruiters want AI autonomy                          | API access gated behind settings; Jason controls delegation scope  |
| **Intelligence compounds over time** | Every candidate enrichment improves future matches           | Master Profile learns from Jason's overrides and manual notes      |
|                                      |                                                              |                                                                    |

## Open Questions

|#|Question|Impact|Status|Owner|
|---|---|---|---|---|
|1|**Template flexibility:** Should Jason upload a DOCX template, or use a visual template builder?|Dev complexity, UX friction|Open|Carla|
|2|**Batch size limits:** Cap at 10 CVs per batch, or allow unlimited (with performance warnings)?|Backend load, UX expectations|Open|Carla|
|3|**Candidate pool organization:** Tags, folders, or just search/filter?|Information architecture|Open|Jason|
|4|**Pipeline integration:** Should Apliqa integrate with Starhunter/Hunter CRM, or remain standalone?|B2B stickiness, dev effort|Open|Stefan|
|5|**Consent expiry:** How long is candidate consent valid? 6 months? 12 months? Indefinite?|GDPR compliance, legal risk|Open|Stefan|
|6|**Multi-user roles:** Should Jason's team have different permission levels (admin, recruiter, intern)?|B2B team plan features, RLS scope|Open|Carla|
|7|**Version control:** If Jason generates 3 Kandidatenprofile for the same candidate, how to track them?|Dashboard complexity, audit trail|Open|Jason|
|8|**API rate limits:** How many API calls per month for Kaile? Per-call pricing or flat rate?|Monetization model, abuse prevention|Open|Stefan|