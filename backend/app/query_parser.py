import re
from typing import Dict, Any, Optional, List
from enum import Enum

class IntentType(str, Enum):
    STRUCTURED_SEARCH = "STRUCTURED_SEARCH"
    SEMANTIC_SEARCH   = "SEMANTIC_SEARCH"
    HYBRID_SEARCH     = "HYBRID_SEARCH"
    REFINEMENT        = "REFINEMENT"
    UNKNOWN           = "UNKNOWN"

# Try loading spaCy, fallback to regex-only if SM model is not present
try:
    import spacy
    nlp = spacy.load("en_core_web_sm")
    SPACY_AVAILABLE = True
except Exception:
    SPACY_AVAILABLE = False
    nlp = None

# --- Keyword Sets (based on synthetic dataset categories) ---
DESIGNATIONS = [
    "site engineer", "project manager", "civil engineer", "electrical engineer",
    "mechanical engineer", "construction manager", "senior manager", "planning engineer",
    "graduate engineer trainee", "assistant manager", "deputy general manager",
    "general manager", "structural engineer", "qa/qc engineer", "safety engineer",
    "estimation engineer", "billing engineer", "quantity surveyor", "surveyor",
    "foreman", "cad engineer", "ehs officer", "geotechnical engineer", "commercial manager"
]

CLUSTERS = [
    "mumbai", "chennai", "bangalore", "delhi", "kolkata", "oman", "qatar", "saudi",
    "mauritius", "uae", "noida", "lucknow", "ahmedabad", "hyderabad", "pune"
]

CERTIFICATIONS = [
    "pmp", "ipma", "leed", "igbc", "primavera", "aws", "asme", "chartered engineer",
    "nebosh", "asnt", "bim", "rics"
]

QUALIFICATIONS = [
    "b.tech", "m.tech", "b.e.", "mba", "diploma", "ph.d", "b.arch", "degree", "master", "doctorate"
]

SEGMENTS = [
    "metro", "tunneling", "tbm", "natm", "water", "wastewater", "irrigation", "desalination",
    "building", "residential", "high-rise", "hospital", "airport", "data center", "factory",
    "road", "runway", "highway", "expressway", "heavy civil", "nuclear", "port", "harbour",
    "hydel", "bridge", "flyover", "power", "substation", "transmission", "cabling"
]

ORGANIZATIONS = [
    "siemens", "shapoorji", "jmc", "petron", "afcons", "tata", "gammon", "ncc",
    "dilip buildcon", "simplex", "soma"
]

PROFICIENCIES = ["basic", "functional", "proficient", "expert", "role model"]

REFINEMENT_TRIGGERS = [
    r"\bonly\b", r"\balso\b", r"\bfilter\b", r"\brefine\b", r"\badd\b", r"\bwith\b"
]

def update_keyword_lists(profiles: List[Dict[str, Any]]):
    """
    Dynamically rebuilds keyword lists for the rule-based parser based on the loaded dataset.
    """
    global DESIGNATIONS, CLUSTERS, CERTIFICATIONS, QUALIFICATIONS, SEGMENTS, ORGANIZATIONS
    
    desigs = {
        "site engineer", "project manager", "civil engineer", "electrical engineer",
        "mechanical engineer", "construction manager", "senior manager", "planning engineer",
        "graduate engineer trainee", "assistant manager", "deputy general manager",
        "general manager", "structural engineer", "qa/qc engineer", "safety engineer",
        "estimation engineer", "billing engineer", "quantity surveyor", "surveyor",
        "foreman", "cad engineer", "ehs officer", "geotechnical engineer", "commercial manager"
    }
    clusters = {
        "mumbai", "chennai", "bangalore", "delhi", "kolkata", "oman", "qatar", "saudi",
        "mauritius", "uae", "noida", "lucknow", "ahmedabad", "hyderabad", "pune"
    }
    certs = {
        "pmp", "ipma", "leed", "igbc", "primavera", "aws", "asme", "chartered engineer",
        "nebosh", "asnt", "bim", "rics"
    }
    quals = {
        "b.tech", "m.tech", "b.e.", "mba", "diploma", "ph.d", "b.arch", "degree", "master", "doctorate"
    }
    segs = {
        "metro", "tunneling", "tbm", "natm", "water", "wastewater", "irrigation", "desalination",
        "building", "residential", "high-rise", "hospital", "airport", "data center", "factory",
        "road", "runway", "highway", "expressway", "heavy civil", "nuclear", "port", "harbour",
        "hydel", "bridge", "flyover", "power", "substation", "transmission", "cabling"
    }
    orgs = {
        "siemens", "shapoorji", "jmc", "petron", "afcons", "tata", "gammon", "ncc",
        "dilip buildcon", "simplex", "soma"
    }
    
    for p in profiles:
        if p.get("designation"):
            desigs.add(p["designation"].strip().lower())
        if p.get("cluster"):
            clusters.add(p["cluster"].strip().lower())
            
        for cert in p.get("certifications", []):
            if cert:
                val = cert.strip().lower().strip(":,;.")
                val = re.sub(r"\b(certifications|certification|cert)\b\s*$", "", val).strip().strip(":,;.- ")
                if val:
                    certs.add(val)
                    norm_val = re.sub(r"[\s\-\.]", "", val)
                    if norm_val and norm_val != val:
                        certs.add(norm_val)
                    if "mrics" in val:
                        certs.add("rics")
                    # Extract parentheses/bracket abbreviations, e.g. "project management professional (pmp)" -> "pmp"
                    for abbr in re.findall(r"[\(\[]([^\)\]]+)[\)\]]", val):
                        abbr_clean = abbr.strip().strip(":,;.")
                        if abbr_clean:
                            certs.add(abbr_clean)
                            norm_abbr = re.sub(r"[\s\-\.]", "", abbr_clean)
                            if norm_abbr and norm_abbr != abbr_clean:
                                certs.add(norm_abbr)
                
        for q in p.get("qualifications", []):
            desc = q.get("Description")
            if desc:
                val = desc.strip().lower().strip(":,;.")
                val = re.sub(r"\b(qualifications|qualification|degree)\b\s*$", "", val).strip().strip(":,;.- ")
                if val:
                    quals.add(val)
                    norm_val = re.sub(r"[\s\-\.]", "", val)
                    if norm_val and norm_val != val:
                        quals.add(norm_val)
                    words = val.split()
                    if words:
                        w_clean = words[0].strip(".,()[]{}")
                        if w_clean:
                            quals.add(w_clean)
                            norm_w = re.sub(r"[\s\-\.]", "", w_clean)
                            if norm_w and norm_w != w_clean:
                                quals.add(norm_w)
                    # Extract parentheses/bracket abbreviations, e.g. "master of business administration (mba)" -> "mba"
                    for abbr in re.findall(r"[\(\[]([^\)\]]+)[\)\]]", val):
                        abbr_clean = abbr.strip().strip(":,;.")
                        if abbr_clean:
                            quals.add(abbr_clean)
                            norm_abbr = re.sub(r"[\s\-\.]", "", abbr_clean)
                            if norm_abbr and norm_abbr != abbr_clean:
                                quals.add(norm_abbr)
                    
        for s in p.get("segment_exposure", []):
            seg = s.get("Segment")
            if seg:
                segs.add(seg.strip().lower())
                
        for exp in p.get("external_experience", []):
            org = exp.get("Org")
            if org:
                orgs.add(org.strip().lower())
                
    if desigs:
        DESIGNATIONS = list(desigs)
    if clusters:
        CLUSTERS = list(clusters)
    if certs:
        CERTIFICATIONS = list(certs)
    if quals:
        QUALIFICATIONS = list(quals)
    if segs:
        SEGMENTS = list(segs)
    if orgs:
        ORGANIZATIONS = list(orgs)

def get_query_tokens(text: str) -> List[str]:
    """
    Splits text by whitespace, strips punctuation, and produces a list of clean tokens.
    Includes dot/hyphen-removed variations for matching flexibility.
    """
    words = text.lower().split()
    tokens = []
    for w in words:
        stripped = w.strip(".,()[]{}\"';:?!*&")
        if stripped:
            tokens.append(stripped)
            norm = re.sub(r"[\-\.]", "", stripped)
            if norm != stripped and norm:
                tokens.append(norm)
    return tokens

def get_stem_variations(tok: str) -> set[str]:
    """
    Returns a set of grammatical variations of a token (e.g. singularizing plurals).
    """
    vars_ = {tok}
    if len(tok) > 3:
        if tok.endswith("ies"):
            vars_.add(tok[:-3] + "y")
        elif tok.endswith("es") and not tok.endswith("ss"):
            vars_.add(tok[:-2])
            vars_.add(tok[:-1])
        elif tok.endswith("s") and not tok.endswith("ss"):
            vars_.add(tok[:-1])
    return vars_

def match_and_consume_keyword(keyword: str, query_tokens: List[str]) -> tuple[bool, List[str]]:
    """
    Checks if all words in the keyword match query tokens, supporting singular/plural and normalizations.
    If so, returns (True, updated_query_tokens_with_matched_tokens_removed).
    Otherwise returns (False, query_tokens).
    """
    word_parts = keyword.lower().split()
    cleaned_parts = []
    for wp in word_parts:
        stripped = wp.strip(".,()[]{}\"';:?!*&")
        if stripped:
            cleaned_parts.append(stripped)
            
    if not cleaned_parts:
        return False, query_tokens
        
    temp_tokens = list(query_tokens)
    for part in cleaned_parts:
        part_norm = re.sub(r"[\-\.]", "", part)
        part_variations = {part, part_norm} if part_norm else {part}
        
        part_all_vars = set()
        for pv in part_variations:
            part_all_vars.update(get_stem_variations(pv))
            
        matched_tok = None
        for tok in temp_tokens:
            tok_norm = re.sub(r"[\-\.]", "", tok)
            tok_variations = {tok, tok_norm} if tok_norm else {tok}
            
            tok_all_vars = set()
            for tv in tok_variations:
                tok_all_vars.update(get_stem_variations(tv))
                
            if part_all_vars.intersection(tok_all_vars):
                matched_tok = tok
                break
                
        if matched_tok is not None:
            temp_tokens.remove(matched_tok)
        else:
            return False, query_tokens
            
    return True, temp_tokens


def detect_operator(query: str, matches: List[str], default_op: str = "or") -> str:
    """
    Detects if the relationship between matches in the query is 'and' or 'or'.
    """
    if len(matches) <= 1:
        return default_op
        
    query_lower = query.lower()
    positions = []
    for m in matches:
        match_pat = re.compile(rf"\b{re.escape(m.lower())}\b")
        search = match_pat.search(query_lower)
        if search:
            positions.append((search.start(), search.end(), m))
            
    if len(positions) < 2:
        return default_op
        
    positions.sort()
    
    has_or = False
    has_and = False
    for i in range(len(positions) - 1):
        end_current = positions[i][1]
        start_next = positions[i+1][0]
        between_text = query_lower[end_current:start_next]
        if re.search(r"\bor\b", between_text):
            has_or = True
        if re.search(r"\band\b|\b&\b", between_text):
            has_and = True
            
    if has_or and not has_and:
        return "or"
    if has_and and not has_or:
        return "and"
        
    if "or" in query_lower:
        return "or"
    if "and" in query_lower or "both" in query_lower:
        return "and"
        
    return default_op


def parse_query_rules(query: str) -> Dict[str, Any]:
    """
    Rule-based parser using spaCy, regex, and keyword lists to extract structured components.
    """
    q_clean = query.lower().strip()
    query_tokens = get_query_tokens(q_clean)
    
    result = {
        "original_query": query,
        "intent": IntentType.UNKNOWN,
        "designation": None,
        "designation_operator": "or",
        "location": None,
        "location_operator": "or",
        "band": None,
        "band_operator": "or",
        "cadre": None,
        "cadre_operator": "or",
        "bu": None,
        "bu_operator": "or",
        "sbg": None,
        "sbg_operator": "or",
        "experience_min": None,
        "experience_max": None,
        "certification": None,
        "certification_operator": "and",
        "qualification": None,
        "qualification_operator": "or",
        "segment": None,
        "segment_operator": "or",
        "skill": None,
        "skill_operator": "and",
        "organization": None,
        "reviewed_proficiency": None,
        "is_core_skill": False,
        "skills_text": query # Fallback full query for semantic search
    }
    
    # 1. Experience extraction (Regex)
    range_match = re.search(r"(\d+)\s*(?:-|to)\s*(\d+)\s*years?", q_clean)
    if range_match:
        result["experience_min"] = float(range_match.group(1))
        result["experience_max"] = float(range_match.group(2))
        matched, updated = match_and_consume_keyword(range_match.group(0), query_tokens)
        if matched:
            query_tokens = updated
    else:
        min_match = re.search(r"(?:more than|at least|over|minimum)?\s*(\d+)\s*(?:\+|years?)", q_clean)
        if min_match:
            result["experience_min"] = float(min_match.group(1))
            matched, updated = match_and_consume_keyword(min_match.group(0), query_tokens)
            if matched:
                query_tokens = updated
            
    # 2. Designation extraction (Keyword matching)
    designation_matches = []
    for desig in sorted(DESIGNATIONS, key=lambda d: (len(get_query_tokens(d)), len(d)), reverse=True):
        matched, updated = match_and_consume_keyword(desig, query_tokens)
        if matched:
            designation_matches.append(desig.title())
            query_tokens = updated
    if designation_matches:
        result["designation"] = designation_matches[0] if len(designation_matches) == 1 else designation_matches
        result["designation_operator"] = detect_operator(q_clean, designation_matches, "or")
            
    # 3. Location/Cluster extraction
    location_matches = []
    for loc in sorted(CLUSTERS, key=lambda l: (len(get_query_tokens(l)), len(l)), reverse=True):
        matched, updated = match_and_consume_keyword(loc, query_tokens)
        if matched:
            location_matches.append(loc.title())
            query_tokens = updated
            
    # Use spaCy GPE/LOC if spaCy is available
    if SPACY_AVAILABLE and nlp:
        doc = nlp(query)
        for ent in doc.ents:
            if ent.label_ in ["GPE", "LOC"]:
                matched, updated = match_and_consume_keyword(ent.text, query_tokens)
                if matched:
                    loc_title = ent.text.title()
                    if loc_title not in location_matches:
                        location_matches.append(loc_title)
                    query_tokens = updated

    if location_matches:
        result["location"] = location_matches[0] if len(location_matches) == 1 else location_matches
        result["location_operator"] = detect_operator(q_clean, location_matches, "or")

    # 4. Certification extraction
    certification_matches = []
    for cert in sorted(CERTIFICATIONS, key=lambda c: (len(get_query_tokens(c)), len(c)), reverse=True):
        matched, updated = match_and_consume_keyword(cert, query_tokens)
        if matched:
            certification_matches.append(cert.upper())
            query_tokens = updated
    if certification_matches:
        result["certification"] = certification_matches[0] if len(certification_matches) == 1 else certification_matches
        result["certification_operator"] = detect_operator(q_clean, certification_matches, "and")
            
    # 5. Qualification extraction
    qualification_matches = []
    for qual in sorted(QUALIFICATIONS, key=lambda q: (len(get_query_tokens(q)), len(q)), reverse=True):
        matched, updated = match_and_consume_keyword(qual, query_tokens)
        if matched:
            qualification_matches.append(qual.title())
            query_tokens = updated
    if qualification_matches:
        generic_quals = {"degree", "master", "doctorate", "Degree", "Master", "Doctorate"}
        if len(qualification_matches) > 1:
            non_generic = [q for q in qualification_matches if q not in generic_quals]
            if non_generic:
                qualification_matches = non_generic
        result["qualification"] = qualification_matches[0] if len(qualification_matches) == 1 else qualification_matches
        result["qualification_operator"] = detect_operator(q_clean, qualification_matches, "or")
            
    # 6. Segment extraction
    segment_matches = []
    for seg in sorted(SEGMENTS, key=lambda s: (len(get_query_tokens(s)), len(s)), reverse=True):
        matched, updated = match_and_consume_keyword(seg, query_tokens)
        if matched:
            segment_matches.append(seg.title())
            query_tokens = updated
    if segment_matches:
        result["segment"] = segment_matches[0] if len(segment_matches) == 1 else segment_matches
        result["segment_operator"] = detect_operator(q_clean, segment_matches, "or")
            
    # 7. Organization extraction
    organization_matches = []
    for org in sorted(ORGANIZATIONS, key=lambda o: (len(get_query_tokens(o)), len(o)), reverse=True):
        matched, updated = match_and_consume_keyword(org, query_tokens)
        if matched:
            organization_matches.append(org.title())
            query_tokens = updated
    if organization_matches:
        result["organization"] = organization_matches[0] if len(organization_matches) == 1 else organization_matches
            
    # 8. Proficiency filters
    for prof in sorted(PROFICIENCIES, key=lambda p: (len(get_query_tokens(p)), len(p)), reverse=True):
        matched, updated = match_and_consume_keyword(prof, query_tokens)
        if matched:
            result["reviewed_proficiency"] = prof.title()
            query_tokens = updated
            break
            
    matched_rev, updated = match_and_consume_keyword("reviewed", query_tokens)
    if matched_rev:
        result["reviewed_proficiency"] = "reviewed"
        query_tokens = updated
        
    matched_core, updated = match_and_consume_keyword("core skill", query_tokens)
    if matched_core:
        result["is_core_skill"] = True
        query_tokens = updated
    else:
        matched_core_single, updated = match_and_consume_keyword("core", query_tokens)
        if matched_core_single:
            result["is_core_skill"] = True
            query_tokens = updated
        
    # 8.5 Band, Cadre, BU, and SBG extraction
    # Band extraction
    band_match = re.search(r"\b([a-zA-Z])\s*-?\s*band\b|\bband\s+([a-zA-Z])\b", q_clean)
    if band_match:
        band_letter = band_match.group(1) or band_match.group(2)
        result["band"] = f"{band_letter.upper()} - Band"
        matched, updated = match_and_consume_keyword(band_match.group(0), query_tokens)
        if matched:
            query_tokens = updated
    else:
        tier_match = re.search(r"\btier\s*-?\s*(\d)\b", q_clean)
        if tier_match:
            result["band"] = f"Tier {tier_match.group(1)}"
            matched, updated = match_and_consume_keyword(tier_match.group(0), query_tokens)
            if matched:
                query_tokens = updated

    # Cadre extraction
    cadre_match = re.search(r"\bcadre\s+([a-zA-Z0-9\-]+)\b|\b([a-zA-Z0-9\-]+)\s+cadre\b", q_clean)
    if cadre_match:
        result["cadre"] = (cadre_match.group(1) or cadre_match.group(2)).upper()
        matched, updated = match_and_consume_keyword(cadre_match.group(0), query_tokens)
        if matched:
            query_tokens = updated
    else:
        cadre_pat = re.search(r"\b((?:tc|[smo])\d(?:\s*[- ]?\s*[a-zA-Z0-9]+)?)\b", q_clean)
        if cadre_pat:
            result["cadre"] = cadre_pat.group(1).upper()
            matched, updated = match_and_consume_keyword(cadre_pat.group(0), query_tokens)
            if matched:
                query_tokens = updated

    # SBG extraction
    sbg_match = re.search(r"\b([a-zA-Z0-9\&]+)\s+sbg\b", q_clean)
    if sbg_match:
        result["sbg"] = f"{sbg_match.group(1).upper()} SBG"
        matched, updated = match_and_consume_keyword(sbg_match.group(0), query_tokens)
        if matched:
            query_tokens = updated
    else:
        sbgs = ["b&f sbg", "hci sbg", "ti sbg", "wet sbg", "pt&d sbg", "mmh sbg"]
        for s in sbgs:
            matched, updated = match_and_consume_keyword(s, query_tokens)
            if matched:
                result["sbg"] = s.upper()
                query_tokens = updated
                break

    # BU extraction
    bus = {
        "buildings & factories": "Buildings & Factories",
        "buildings and factories": "Buildings & Factories",
        "b&f": "Buildings & Factories",
        "heavy civil": "Heavy Civil Infrastructure",
        "transportation": "Transportation Infrastructure",
        "water & effluent": "Water & Effluent Treatment",
        "water and effluent": "Water & Effluent Treatment",
        "wet": "Water & Effluent Treatment",
        "power transmission": "Power Transmission & Distribution",
        "pt&d": "Power Transmission & Distribution",
    }
    for key, val in bus.items():
        matched, updated = match_and_consume_keyword(key, query_tokens)
        if matched:
            result["bu"] = val
            query_tokens = updated
            break
        
    # Reconstruct remaining query for skill extraction
    remaining_query = " ".join(query_tokens)
    skill_match = re.search(r"\b(?:knows|skilled in|skills?\s+in|skills?\s+of|skills?|expert in)\s+([a-zA-Z\s\+\#]+)\b", remaining_query)
    if skill_match:
        skill_captured = skill_match.group(1).strip()
        connectors = [
            r"\bhas\b", r"\bhaving\b", r"\bwith\b", 
            r"\bwho\b", r"\bonly\b", r"\bfor\b", r"\bproficient\b", 
            r"\bproficiency\b", r"\breviewed\b"
        ]
        for conn in connectors:
            parts = re.split(conn, skill_captured, maxsplit=1)
            if len(parts) > 1 and parts[0].strip():
                skill_captured = parts[0].strip()
            
        if skill_captured.startswith("in "):
            skill_captured = skill_captured[3:].strip()
            
        # Parse multiple skills
        skill_parts = re.split(r"\b(?:and|or|&)\b|,", skill_captured)
        skills = [s.strip().title() for s in skill_parts if s.strip()]
        if skills:
            result["skill"] = skills[0] if len(skills) == 1 else skills
            result["skill_operator"] = detect_operator(skill_captured, skills, "and")
        
    # 10. Intent determination
    is_refinement = any(re.match(rf"^{trigger}", q_clean) for trigger in REFINEMENT_TRIGGERS)
    
    has_structured = any([
        result["designation"],
        result["location"],
        result["band"],
        result["cadre"],
        result["bu"],
        result["sbg"],
        result["experience_min"] is not None,
        result["certification"],
        result["qualification"],
        result["organization"]
    ])
    
    has_semantic = any([
        result["skill"],
        result["segment"],
        "expert" in q_clean, "knows" in q_clean, "skills" in q_clean, "exposure" in q_clean
    ])
    
    if is_refinement:
        result["intent"] = IntentType.REFINEMENT
    elif has_structured and has_semantic:
        result["intent"] = IntentType.HYBRID_SEARCH
    elif has_structured:
        result["intent"] = IntentType.STRUCTURED_SEARCH
    elif has_semantic:
        result["intent"] = IntentType.SEMANTIC_SEARCH
    else:
        result["intent"] = IntentType.SEMANTIC_SEARCH
        
    return result
