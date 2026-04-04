from apliqa.services.cv_gap_mapper import map_gaps_to_sections


def test_gap_maps_to_section_with_most_keyword_overlap():
    sections = {
        "introduction": "experienced python developer with django",
        "position::abc": "built rest apis using python flask",
        "skills": "java sql git",
    }
    gaps = ["python", "django"]
    result = map_gaps_to_sections(gaps, sections)
    # "python" appears in both introduction and position::abc; "django" only in introduction
    # introduction has 2 matches, position::abc has 1
    assert result["introduction"] == ["python", "django"]
    assert result.get("position::abc") == ["python"]
    assert "skills" not in result or result["skills"] == []


def test_unmatched_gap_goes_to_general():
    sections = {"introduction": "java developer", "skills": "java"}
    gaps = ["kubernetes"]
    result = map_gaps_to_sections(gaps, sections)
    assert result.get("__general__") == ["kubernetes"]


def test_empty_gaps_returns_empty():
    sections = {"introduction": "some text"}
    result = map_gaps_to_sections([], sections)
    assert result == {}
