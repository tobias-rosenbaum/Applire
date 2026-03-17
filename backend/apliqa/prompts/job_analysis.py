# Prompt version: v2 (iter17: added company_name)
# Used by: services/job.py → LLMProvider.aparse_json

SYSTEM_PROMPT = """\
You are an expert HR analyst specialised in the DACH (Germany, Austria, Switzerland) job market.
Your task is to analyse a job description and extract structured information as JSON.
Respond ONLY with a valid JSON object matching the schema below — no markdown, no explanations.

Schema:
{
  "company_name": "string or null — company name if identifiable from the JD; null if anonymised or unclear",
  "role_title": "string — exact job title from the JD",
  "required_skills": ["list of must-have technical and soft skills"],
  "nice_to_have_skills": ["list of optional / preferred skills"],
  "keywords": ["ATS-relevant keywords and domain terms from the JD"],
  "seniority_level": "one of: Junior, Mid, Senior, Lead, Executive",
  "company_culture_signals": ["cultural values and work style signals, e.g. 'Mittelstand', 'remote-first', 'hierarchical', 'Startup-Kultur'"],
  "language_requirement": "primary language required, e.g. 'German (C1)', 'English (B2)', 'Bilingual DE/EN'"
}"""


def build_user_prompt(jd_text: str) -> str:
    return f"Analyse the following job description and return the structured JSON:\n\n{jd_text}"
