"""Unit tests for gap clustering schema and service."""
from applire.schemas.gap_cluster import GapClusterSchema


def test_gap_cluster_schema_validates():
    raw = {
        "id": "cluster-agentic",
        "label": "Agentic AI Systems",
        "category": "C",
        "gaps": ["Agentic Systems", "AI Systems"],
        "jd_skills": ["LLM-based Agent Design"],
        "jd_context": "Die Stelle sucht jemanden, der autonome KI-Agenten designt.",
    }
    cluster = GapClusterSchema.model_validate(raw)
    assert cluster.id == "cluster-agentic"
    assert cluster.category == "C"
    assert len(cluster.gaps) == 2
