"""
Merge logic for combining new profile data with existing.

Design rules:
- NEVER silently overwrite conflicting data.
- All conflicts are flagged in MergeResult.conflicts for user resolution.
- Non-conflicting additions and improvements are applied automatically.
"""
from dataclasses import dataclass, field

from apliqa.schemas.profile import (
    Conflict,
    MasterProfileData,
    Skill,
    WorkEntry,
)


@dataclass
class MergeResult:
    merged_profile: MasterProfileData
    added: list[str] = field(default_factory=list)   # descriptions of auto-added items
    conflicts: list[Conflict] = field(default_factory=list)


def _dates_overlap(
    a_start: str | None,
    a_end: str | None,
    b_start: str | None,
    b_end: str | None,
) -> bool:
    """
    Best-effort overlap check on partial date strings like '2020-01' or '2020'.
    Returns True when dates cannot be determined (safe default — flags as potential overlap).
    """
    if not a_start or not b_start:
        return True
    # Normalise to 'YYYY-MM' for comparison
    a_s = (a_start + "-01")[:7]
    a_e = (a_end + "-12")[:7] if a_end else "9999-12"
    b_s = (b_start + "-01")[:7]
    b_e = (b_end + "-12")[:7] if b_end else "9999-12"
    return a_s <= b_e and b_s <= a_e


def _merge_work_experience(
    existing: list[WorkEntry],
    incoming: list[WorkEntry],
    source: str,
) -> tuple[list[WorkEntry], list[str], list[Conflict]]:
    """
    Rules:
    1. Same company + overlapping dates → same role
       → merge unique responsibilities/achievements/technologies; flag title contradictions
    2. Same company + non-overlapping dates → different role → add as new entry
    3. Different company → add as new entry
    """
    result = list(existing)
    added: list[str] = []
    conflicts: list[Conflict] = []

    for inc in incoming:
        matched = False
        for idx, ex in enumerate(result):
            if ex.company.strip().lower() != inc.company.strip().lower():
                continue
            if not _dates_overlap(ex.start_date, ex.end_date, inc.start_date, inc.end_date):
                continue
            # Same company + overlapping dates → same role
            matched = True
            merged = ex.model_copy(deep=True)

            # Flag differing job title
            if ex.role.strip().lower() != inc.role.strip().lower():
                conflicts.append(
                    Conflict(
                        section="work_experience",
                        field="role",
                        existing_value=ex.role,
                        incoming_value=inc.role,
                        source=source,
                        suggested_resolution=f"Review both titles for '{ex.company}'",
                    )
                )

            # Merge lists — deduplicate by lower-cased value
            def _merge_list(a: list[str], b: list[str]) -> list[str]:
                seen = {v.lower() for v in a}
                result_list = list(a)
                for v in b:
                    if v.lower() not in seen:
                        result_list.append(v)
                        seen.add(v.lower())
                return result_list

            merged = merged.model_copy(
                update={
                    "responsibilities": _merge_list(ex.responsibilities, inc.responsibilities),
                    "achievements": _merge_list(ex.achievements, inc.achievements),
                    "technologies": _merge_list(ex.technologies, inc.technologies),
                }
            )
            result[idx] = merged
            break

        if not matched:
            result.append(inc)
            added.append(f"work_experience: {inc.role} at {inc.company}")

    return result, added, conflicts


def _merge_skills(
    existing: list[Skill],
    incoming: list[Skill],
    source: str,
) -> tuple[list[Skill], list[str], list[Conflict]]:
    """
    Rules:
    1. Same skill name → keep higher proficiency + higher years_experience
    2. New skill → add
    3. Source always reflects origin
    """
    _PROF_RANK = {"basic": 0, "intermediate": 1, "advanced": 2, "expert": 3}
    result = list(existing)
    added: list[str] = []
    conflicts: list[Conflict] = []

    for inc in incoming:
        match = next(
            (s for s in result if s.name.strip().lower() == inc.name.strip().lower()),
            None,
        )
        if match is None:
            result.append(inc)
            added.append(f"skill: {inc.name}")
        else:
            idx = result.index(match)
            # Keep higher proficiency
            best_prof = (
                match.proficiency
                if _PROF_RANK[match.proficiency] >= _PROF_RANK[inc.proficiency]
                else inc.proficiency
            )
            # Keep higher years_experience
            best_years: int | None = match.years_experience
            if inc.years_experience is not None:
                if best_years is None or inc.years_experience > best_years:
                    best_years = inc.years_experience

            result[idx] = match.model_copy(
                update={
                    "proficiency": best_prof,
                    "years_experience": best_years,
                    "source": source,
                }
            )

    return result, added, conflicts


def merge_profiles(
    existing: MasterProfileData,
    incoming: MasterProfileData,
    source: str,
) -> MergeResult:
    """
    Merge *incoming* profile data into *existing*.
    Returns a MergeResult with the merged profile and any flagged conflicts.
    """
    all_added: list[str] = []
    all_conflicts: list[Conflict] = []

    # Work experience
    merged_work, work_added, work_conflicts = _merge_work_experience(
        existing.work_experience, incoming.work_experience, source
    )
    all_added.extend(work_added)
    all_conflicts.extend(work_conflicts)

    # Skills
    merged_skills, skills_added, skills_conflicts = _merge_skills(
        existing.skills, incoming.skills, source
    )
    all_added.extend(skills_added)
    all_conflicts.extend(skills_conflicts)

    # Education — append non-duplicate entries (match on institution + degree)
    merged_edu = list(existing.education)
    for inc_e in incoming.education:
        duplicate = any(
            e.institution.strip().lower() == inc_e.institution.strip().lower()
            and e.degree.strip().lower() == inc_e.degree.strip().lower()
            for e in merged_edu
        )
        if not duplicate:
            merged_edu.append(inc_e)
            all_added.append(f"education: {inc_e.degree} at {inc_e.institution}")

    # Languages — keep higher/new levels
    merged_langs = list(existing.languages)
    for inc_l in incoming.languages:
        match = next(
            (l for l in merged_langs if l.language.lower() == inc_l.language.lower()),
            None,
        )
        if match is None:
            merged_langs.append(inc_l)
            all_added.append(f"language: {inc_l.language}")
        # else keep existing level (user can patch manually)

    # Certifications — append non-duplicate (match on name)
    merged_certs = list(existing.certifications)
    for inc_c in incoming.certifications:
        if not any(c.name.lower() == inc_c.name.lower() for c in merged_certs):
            merged_certs.append(inc_c)
            all_added.append(f"certification: {inc_c.name}")

    # Personal info — flag conflicts on populated vs populated fields
    merged_pi = existing.personal_info.model_copy(deep=True)
    inc_pi = incoming.personal_info
    for attr in ("name", "email", "phone", "linkedin_url", "xing_url"):
        ex_val = getattr(merged_pi, attr)
        inc_val = getattr(inc_pi, attr)
        if inc_val and not ex_val:
            # Incoming fills a gap — accept automatically
            merged_pi = merged_pi.model_copy(update={attr: inc_val})
            all_added.append(f"personal_info.{attr}")
        elif inc_val and ex_val and inc_val.strip().lower() != ex_val.strip().lower():
            all_conflicts.append(
                Conflict(
                    section="personal_info",
                    field=attr,
                    existing_value=ex_val,
                    incoming_value=inc_val,
                    source=source,
                )
            )

    # Professional summary — fill missing language variants
    merged_ps = existing.professional_summary.model_copy(deep=True)
    if not merged_ps.de and incoming.professional_summary.de:
        merged_ps = merged_ps.model_copy(update={"de": incoming.professional_summary.de})
        all_added.append("professional_summary.de")
    if not merged_ps.en and incoming.professional_summary.en:
        merged_ps = merged_ps.model_copy(update={"en": incoming.professional_summary.en})
        all_added.append("professional_summary.en")

    # Publications and volunteer activities — append all (no dedup logic needed here)
    merged_pubs = list(existing.publications) + [
        p for p in incoming.publications
        if not any(ep.title.lower() == p.title.lower() for ep in existing.publications)
    ]
    merged_vol = list(existing.volunteer_activities) + [
        v for v in incoming.volunteer_activities
        if not any(
            ev.role.lower() == v.role.lower() and ev.organization.lower() == v.organization.lower()
            for ev in existing.volunteer_activities
        )
    ]

    merged_profile = existing.model_copy(
        deep=True,
        update={
            "personal_info": merged_pi,
            "professional_summary": merged_ps,
            "work_experience": merged_work,
            "education": merged_edu,
            "certifications": merged_certs,
            "skills": merged_skills,
            "languages": merged_langs,
            "publications": merged_pubs,
            "volunteer_activities": merged_vol,
        },
    )

    return MergeResult(
        merged_profile=merged_profile,
        added=all_added,
        conflicts=all_conflicts,
    )
