import json
import httpx
import openai
from openai import OpenAI
from typing import Dict, Any, List, Optional
from backend.app.config import settings
from backend.app.query_parser import parse_query_rules, IntentType

SYSTEM_PROMPT = """
You are an AI workforce intelligence search router. Your job is to analyze natural language queries about employees, extract search filters, determine search intent, and output a valid JSON response.
You do not answer queries directly. You orchestrate search tools.

Intents:
- STRUCTURED_SEARCH: Query only contains exact filters (designation, location, experience range, bu, sbg, cadre, band, certification, qualification).
  Example: "show civil engineers with 10+ years"
- SEMANTIC_SEARCH: Query relies on matching unstructured skills, project exposures, or experiences.
  Example: "who knows electrical systems", "people with Siemens experience"
- HYBRID_SEARCH: Query combines both structured filters and unstructured skills/exposures.
  Example: "civil engineers in Chennai with metro exposure"
- REFINEMENT: User is adding, changing, or clarifying a previous query (e.g. adding a location filter, restricting to core skills).
  Example: "only Chennai", "only reviewed proficiency", "with PMP certification"

Output format must be a single valid JSON block with these keys:
{
  "intent": "STRUCTURED_SEARCH | SEMANTIC_SEARCH | HYBRID_SEARCH | REFINEMENT | UNKNOWN",
  "search_mode": "structured | semantic | hybrid",
  "filters": {
    "designation": string or array of strings or null,
    "designation_operator": "and" | "or" | null,
    "department": string or array of strings or null,
    "department_operator": "and" | "or" | null,
    "location": string or array of strings or null,  // corresponds to Cluster
    "location_operator": "and" | "or" | null,
    "band": string or array of strings or null,
    "band_operator": "and" | "or" | null,
    "cadre": string or array of strings or null,
    "cadre_operator": "and" | "or" | null,
    "bu": string or array of strings or null,
    "bu_operator": "and" | "or" | null,
    "sbg": string or array of strings or null,
    "sbg_operator": "and" | "or" | null,
    "experience_min": number or null,
    "experience_max": number or null,
    "internal_exp_min": number or null,
    "external_exp_min": number or null,
    "internal_org": string or null,
    "external_org": string or null,
    "certification": string or array of strings or null,
    "certification_operator": "and" | "or" | null,
    "certification_groups": array of arrays of strings or null,
    "qualification": string or array of strings or null,
    "qualification_operator": "and" | "or" | null,
    "qualification_groups": array of arrays of strings or null,
    "segment": string or array of strings or null,
    "segment_operator": "and" | "or" | null,
    "skill": string or array of strings or null,
    "skill_operator": "and" | "or" | null,
    "sub_skill": string or array of strings or null,
    "sub_skill_operator": "and" | "or" | null,
    "external_designation": string or array of strings or null,
    "external_designation_operator": "and" | "or" | null,
    "reviewed_proficiency": string or null, // e.g. "Expert", "Proficient", or "reviewed only"
    "is_core_skill": boolean or null,
    "skills_text": string or null // the semantic portion of the query
  },
  "clarification_message": string or null
}

For any attribute that can take an array of strings, if multiple values are queried (e.g. "PMP and RICS", "Bangalore or Hyderabad"), extract them as a JSON array of strings, and determine the logical operator ("and" or "or") based on the query structure. Default to "and" for certification and skill, and "or" for others.
If the query is ambiguous, set "clarification_message" to ask the user for details, but still try to make the best search decision.

IMPORTANT — Designation vs Skill/Sub-Skill rules:
- "designation" is for CURRENT JOB ROLES/TITLES (e.g. "Project Manager", "Civil Engineer", "Safety Engineer").
  - If a user asks "who are all project managers" or "show me the project managers in <location>", this is a role/designation check. Set "designation" to "Project Manager" and do NOT set "skill" or "sub_skill" to "Project Management".
  - Map disciplines in designations to their standard abbreviated parentheses form:
    - "mechanical" -> "(Mech)" (e.g. "Construction Manager in Mechanical" -> "Construction Manager (Mech)", "Construction Manager Mechanical" -> "Construction Manager (Mech)")
    - "electrical" -> "(Elec)" (e.g. "Construction Manager in Electrical" -> "Construction Manager (Elec)", "Construction Manager Electrical" -> "Construction Manager (Elec)")
    - "civil" -> "(Civil)" (e.g. "Construction Manager in Civil" -> "Construction Manager (Civil)", "Construction Manager Civil" -> "Construction Manager (Civil)")
- "skill" and "sub_skill" are for skills listed on the skill sheet.
  - If a user asks "people who know project management", "people who know about managing projects", or "people with project management skills", this is a skill check. Set "skill" to "Project Management" and do NOT set "designation" to "Project Manager".

IMPORTANT — Designation vs Department rules:
- "department" is for the specific department or discipline (e.g. "CIVIL", "MECH", "ELEC", "QA/QC", "QUALITY", "PLANNING", "EHS", "CONTRACTS", "FACADE", "FORMWORKS", "MEP", "P&M", "STORES", "SURVEY").
- Use "department" when the user specifies a department explicitly (e.g. "in the civil department", "in mechanical department", "in ELEC").
  - If a user asks for "engineers in the civil department", set "designation" to "Engineer" and "department" to "CIVIL".
  - If a user asks for "civil engineers", you can set "designation" to "Civil Engineer" (which works via role matching).
  - If a user asks generally for "quality department" or "quality", set "department" to "QUALITY" (which is configured to return both QUALITY and QA/QC department employees).
  - If a user asks specifically for "QA/QC" department or "QA/QC", set "department" to "QA/QC" (which returns only QA/QC department employees, excluding general quality roles).

IMPORTANT — Designation vs External Designation (Past/Prior Experience):
- Use "designation" for current designation (e.g. "who are civil engineers", "show civil engineers in Delhi").
- Use "external_designation" when the query specifically asks about past/prior experience or former roles (e.g. "who were civil engineers", "people who worked as site engineers previously", "past experience as construction manager").

IMPORTANT — Skill vs Sub-Skill classification:
- "skill" is for general skill categories (e.g. "Project Management", "Civil Engineering", "Electrical Engineering", "Digital & IT", "Mechanical Engineering").
- "sub_skill" is for specific sub-skills (e.g. "Primavera P6", "Risk Management", "Contract Administration", "PMP", "Billing & Invoicing", "Project Scheduling", "Agile", "MS Project", "Cost Estimation").
- When a sub-skill is asked for specifically, populate "sub_skill" (e.g. "Agile") and leave "skill" as null. When a general skill is asked for, populate "skill" (e.g. "Project Management").

IMPORTANT — Qualification vs Certification disambiguation:
- "certification" is for PROFESSIONAL CERTIFICATIONS only: PMP, RICS, LEED, NEBOSH, IGBC, IPMA, ASNT, ASME, BIM, Primavera, AWS, etc.
- "qualification" is for ACADEMIC / EDUCATIONAL QUALIFICATIONS only: MBA, B.Tech, M.Tech, B.E., B.Arch, Diploma, Ph.D, Master's degree, Bachelor's degree, A.I.S.S.C.E, A.I.S.S.E, etc.
- NEVER put MBA, B.Tech, Diploma, degree names, or education board qualifications (like AISSCE, AISSE) into the "certification" field.
- NEVER put PMP, RICS, NEBOSH, or professional certifications into the "qualification" field.

IMPORTANT — Grouped AND/OR qualification and certification logic:
- Use "qualification_groups" (not "qualification") when the query has compound logic: (A OR B) AND (C OR D).
- Use "certification_groups" (not "certification") when certs need compound logic.
- Format: an array of arrays. Each inner array = alternatives OR'd together. Outer array = groups AND'd together.
- ALL alternatives within a slash-separated group MUST be included. Do NOT drop any.

How to parse slash-separated groups step by step:
  1. Split query on "and" (or "&") to identify separate requirement groups.
  2. Within each group, split on "/" to identify alternatives (these are OR'd).
  3. Include EVERY alternative from step 2 in the inner array.

Examples:
  Query: "B.Tech/B.E and M.Tech/M.E"
  Step 1: groups = ["B.Tech/B.E", "M.Tech/M.E"]
  Step 2: group1_alternatives = ["B.Tech", "B.E"], group2_alternatives = ["M.Tech", "M.E"]
  Result: qualification_groups: [["B.Tech", "B.E"], ["M.Tech", "M.E"]]
  ✗ WRONG: [["B.E"], ["M.Tech", "M.E"]]  ← do NOT drop B.Tech!

  Query: "PMP/IPMA certified and NEBOSH/LEED"
  Result: certification_groups: [["PMP", "IPMA"], ["NEBOSH", "LEED"]]

- When using _groups, set the corresponding flat field ("qualification" or "certification") to null.
"""

def route_query_llm(
    query: str, 
    history: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Route the query using Gemini as primary, OpenAI as secondary.
    If both fail or are missing, falls back to the local rule-based parser.
    """
    # 1. Try Gemini
    if settings.GEMINI_API_KEY:
        try:
            return _route_query_gemini(query, history)
        except Exception as e:
            warning = f"Gemini Router Error: {str(e)}."
            # Fall back to OpenAI if key is present
            if settings.OPENAI_API_KEY:
                try:
                    return _route_query_openai(query, history)
                except Exception as oe:
                    return _fallback_to_rules(query, f"{warning} OpenAI fallback failed: {str(oe)}.")
            else:
                return _fallback_to_rules(query, f"{warning} Using local parser.")

    # 2. Try OpenAI
    if settings.OPENAI_API_KEY:
        try:
            return _route_query_openai(query, history)
        except Exception as e:
            return _fallback_to_rules(query, f"OpenAI Router Error: {str(e)}. Using local parser.")

    # 3. Local Rule-Based Fallback
    return _fallback_to_rules(query, "No LLM API keys configured. Using local parser.")


def _route_query_gemini(
    query: str, 
    history: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """Route query using Gemini 2.5 Flash / 2.0 Flash via direct HTTP API call."""
    api_key = settings.GEMINI_API_KEY
    
    contents = []
    if history:
        # Append last 4 messages of history for context
        for h in history[-4:]:
            user_msg = h.get("message", "")
            contents.append({
                "role": "user",
                "parts": [{"text": user_msg}]
            })
            if h.get("llm_response"):
                contents.append({
                    "role": "model",
                    "parts": [{"text": json.dumps(h["llm_response"])}]
                })
                
    # Append current user message
    contents.append({
        "role": "user",
        "parts": [{"text": query}]
    })
    
    payload = {
        "systemInstruction": {
            "parts": [{"text": SYSTEM_PROMPT}]
        },
        "contents": contents,
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.0
        }
    }
    
    headers = {"Content-Type": "application/json"}
    
    models = ["gemini-2.5-flash", "gemini-2.0-flash"]
    last_err = None
    
    with httpx.Client(timeout=15.0) as client:
        for model in models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            try:
                response = client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(text)
            except Exception as e:
                last_err = e
                continue
                
        raise last_err


def _route_query_openai(
    query: str, 
    history: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """Route query using OpenAI GPT-4o-mini."""
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    
    # Build prompt messages including history
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    if history:
        for h in history[-4:]:
            messages.append({"role": "user", "content": h.get("message", "")})
            if h.get("llm_response"):
                messages.append({"role": "assistant", "content": json.dumps(h["llm_response"])})
                
    messages.append({"role": "user", "content": query})
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.0,
        response_format={"type": "json_object"}
    )
    
    content = response.choices[0].message.content
    return json.loads(content)


def _fallback_to_rules(query: str, warning_msg: str) -> Dict[str, Any]:
    """Fallback helper using query_parser.py rules."""
    parsed = parse_query_rules(query)
    
    intent = parsed["intent"]
    
    # Map intent to search mode
    if intent == IntentType.STRUCTURED_SEARCH:
        search_mode = "structured"
    elif intent == IntentType.SEMANTIC_SEARCH:
        search_mode = "semantic"
    elif intent == IntentType.HYBRID_SEARCH:
        search_mode = "hybrid"
    else:
        search_mode = "semantic"
        
    filters = {
        "designation": parsed["designation"],
        "designation_operator": parsed.get("designation_operator", "or"),
        "department": parsed.get("department"),
        "department_operator": parsed.get("department_operator", "or"),
        "location": parsed["location"],
        "location_operator": parsed.get("location_operator", "or"),
        "band": parsed.get("band"),
        "band_operator": parsed.get("band_operator", "or"),
        "cadre": parsed.get("cadre"),
        "cadre_operator": parsed.get("cadre_operator", "or"),
        "bu": parsed.get("bu"),
        "bu_operator": parsed.get("bu_operator", "or"),
        "sbg": parsed.get("sbg"),
        "sbg_operator": parsed.get("sbg_operator", "or"),
        "experience_min": parsed["experience_min"],
        "experience_max": parsed["experience_max"],
        "internal_exp_min": None,
        "external_exp_min": None,
        "internal_org": None,
        "external_org": parsed["organization"],
        "certification": parsed["certification"],
        "certification_operator": parsed.get("certification_operator", "and"),
        "certification_groups": parsed.get("certification_groups"),
        "qualification": parsed["qualification"],
        "qualification_operator": parsed.get("qualification_operator", "or"),
        "qualification_groups": parsed.get("qualification_groups"),
        "segment": parsed["segment"],
        "segment_operator": parsed.get("segment_operator", "or"),
        "skill": parsed["skill"],
        "skill_operator": parsed.get("skill_operator", "and"),
        "sub_skill": parsed.get("sub_skill"),
        "sub_skill_operator": parsed.get("sub_skill_operator", "or"),
        "external_designation": parsed.get("external_designation"),
        "external_designation_operator": parsed.get("external_designation_operator", "or"),
        "reviewed_proficiency": parsed["reviewed_proficiency"],
        "is_core_skill": parsed["is_core_skill"],
        "skills_text": query
    }
    
    return {
        "intent": intent.value,
        "search_mode": search_mode,
        "filters": filters,
        "clarification_message": f"{warning_msg} Running local search."
    }
