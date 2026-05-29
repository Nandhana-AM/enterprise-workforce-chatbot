import re
from typing import Dict, Any, Optional, List
from enum import Enum

def normalize_val(val: Any) -> str:
    if val is None:
        return ""
    return re.sub(r"[\s\-\.]", "", str(val)).lower()


def normalize_desig_abbreviations(text: str) -> str:
    text = text.lower()
    # Insert space around parentheses if missing, e.g. "manager(finishes)" -> "manager (finishes)"
    text = re.sub(r"([^\s])\(", r"\1 (", text)
    text = re.sub(r"\)([^\s])", r") \1", text)
    
    # Normalize spaces after dot/hyphen first
    text = re.sub(r"\.([a-zA-Z])", r". \1", text)
    text = re.sub(r"([a-zA-Z])\-([a-zA-Z])", r"\1 - \2", text)
    
    # Replace abbreviations with standard forms
    text = re.sub(r"\b(asst|assistant)\b\.?", "assistant", text)
    text = re.sub(r"\b(sr|senior)\b\.?", "senior", text)
    text = re.sub(r"\b(jr|junior)\b\.?", "junior", text)
    text = re.sub(r"\bdgm\b", "deputy general manager", text)
    text = re.sub(r"\bjgm\b", "joint general manager", text)
    text = re.sub(r"\bmgr\b", "manager", text)
    
    # Map mechanical -> mech, electrical -> elec
    text = re.sub(r"\bmechanical\b", "mech", text)
    text = re.sub(r"\belectrical\b", "elec", text)
    
    # Map prepositions connecting designation to discipline
    text = re.sub(r"\bin\s+mech\b", " (mech)", text)
    text = re.sub(r"\bin\s+elec\b", " (elec)", text)
    text = re.sub(r"\bin\s+civil\b", " (civil)", text)
    return text





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

# Pre-compiled regular expressions for improved parser performance
EXP_RANGE_RE = re.compile(r"(\d+)\s*(?:-|to)\s*(\d+)\s*years?")
EXP_MIN_RE = re.compile(r"(?:more than|at least|over|minimum)?\s*(\d+)\s*(?:\+|years?)")
PAST_MARKER_RE = re.compile(r"\b(?:were|was|previously|previous|prior|past|former|ex|earlier|worked\s+as)\b")
QUALIFICATION_CONTEXT_RE = re.compile(
    r"\b(qualification|qualifications|qualified|degree|education|studied|graduate|graduated|university|college|course)\b"
)
AND_SPLIT_RE = re.compile(r"\s+(?:and|&)\s+")
SLASH_SPLIT_RE = re.compile(r"\s*/\s*")
NORMALIZE_DASH_DOT_RE = re.compile(r"[\-\.]")
NORMALIZE_VAL_RE = re.compile(r"[\s\-\.]")
BAND_RE = re.compile(r"\b([a-zA-Z])\s*-?\s*band\b|\bband\s+([a-zA-Z])\b")
TIER_RE = re.compile(r"\btier\s*-?\s*(\d)\b")
CADRE_RE = re.compile(r"\bcadre\s+([a-zA-Z0-9\-]+)\b|\b([a-zA-Z0-9\-]+)\s+cadre\b")
CADRE_PAT_RE = re.compile(r"\b((?:tc|[smo])\d(?:\s*[- ]?\s*[a-zA-Z0-9]+)?)\b")
SBG_RE = re.compile(r"\b([a-zA-Z0-9\&]+)\s+sbg\b")
SKILL_MATCH_RE = re.compile(r"\b(?:knows|skilled in|skills?\s+in|skills?\s+of|skills?|expert in)\s+([a-zA-Z\s\+\#]+)\b")

PM_SKILL_PATTERNS = [
    re.compile(r"project\s+management"),
    re.compile(r"managing\s+projects"),
    re.compile(r"management\s+of\s+projects"),
    re.compile(r"pm\s+skills?"),
    re.compile(r"project\s+manager\s+skills?"),
]

CONNECTOR_RES = [
    re.compile(r"\bhas\b"), re.compile(r"\bhaving\b"), re.compile(r"\bwith\b"), 
    re.compile(r"\bwho\b"), re.compile(r"\bonly\b"), re.compile(r"\bfor\b"), 
    re.compile(r"\bproficient\b"), re.compile(r"\bproficiency\b"), re.compile(r"\breviewed\b")
]

SKILL_SPLIT_RE = re.compile(r"\b(?:and|or|&)\b|,")

SUFFIX_CERT_RE = re.compile(r"\b(certifications|certification|cert)\b\s*$", re.IGNORECASE)
SUFFIX_QUAL_RE = re.compile(r"\b(qualifications|qualification|degree)\b\s*$", re.IGNORECASE)
PAREN_ABBR_RE = re.compile(r"[\(\[]([^\)\]]+)[\)\]]")

OR_RE = re.compile(r"\bor\b")
AND_RE = re.compile(r"\band\b|\b&\b")

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

SKILL_STOP_WORDS = {
    "the", "a", "an", "in", "on", "at", "to", "for", "with", "by", "of", "and", "or", "but", "from",
    "is", "are", "was", "were", "be", "been", "have", "has", "had", "do", "does", "did",
    "this", "that", "these", "those", "they", "them", "their", "he", "him", "his", "she", "her",
    "it", "its", "we", "us", "our", "you", "your", "who", "whom", "whose", "which", "what",
    "department", "dept"
}

SKILLS = ["project management", "civil engineering", "electrical engineering", "digital & it", "mechanical engineering"]
SUB_SKILLS = []

def update_keyword_lists(profiles: List[Dict[str, Any]]):
    """
    Dynamically rebuilds keyword lists for the rule-based parser based on the loaded dataset.
    """
    global DESIGNATIONS, CLUSTERS, CERTIFICATIONS, QUALIFICATIONS, SEGMENTS, ORGANIZATIONS, SKILLS, SUB_SKILLS
    
    desigs = {
        normalize_desig_abbreviations(d) for d in {
            "site engineer", "project manager", "civil engineer", "electrical engineer",
            "mechanical engineer", "construction manager", "senior manager", "planning engineer",
            "graduate engineer trainee", "assistant manager", "deputy general manager",
            "general manager", "structural engineer", "qa/qc engineer", "safety engineer",
            "estimation engineer", "billing engineer", "quantity surveyor", "surveyor",
            "foreman", "cad engineer", "ehs officer", "geotechnical engineer", "commercial manager"
        }
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
    skills = {
        "project management", "civil engineering", "electrical engineering", "digital & it", "mechanical engineering"
    }
    sub_skills = set()
    
    for p in profiles:
        if p.get("designation"):
            desigs.add(normalize_desig_abbreviations(p["designation"].strip()))
        if p.get("cluster"):
            clusters.add(p["cluster"].strip().lower())
            
        for cert in p.get("certifications", []):
            if cert:
                val = cert.strip().lower().strip(":,;.")
                val = SUFFIX_CERT_RE.sub("", val).strip().strip(":,;.- ")
                if val:
                    certs.add(val)
                    norm_val = NORMALIZE_VAL_RE.sub("", val)
                    if norm_val and norm_val != val:
                        certs.add(norm_val)
                    if "mrics" in val:
                        certs.add("rics")
                    # Extract parentheses/bracket abbreviations, e.g. "project management professional (pmp)" -> "pmp"
                    for abbr in PAREN_ABBR_RE.findall(val):
                        abbr_clean = abbr.strip().strip(":,;.")
                        if abbr_clean:
                            certs.add(abbr_clean)
                            norm_abbr = NORMALIZE_VAL_RE.sub("", abbr_clean)
                            if norm_abbr and norm_abbr != abbr_clean:
                                certs.add(norm_abbr)
                
        for q in p.get("qualifications", []):
            desc = q.get("Description")
            if desc:
                val = desc.strip().lower().strip(":,;.")
                val = SUFFIX_QUAL_RE.sub("", val).strip().strip(":,;.- ")
                if val:
                    quals.add(val)
                    norm_val = NORMALIZE_VAL_RE.sub("", val)
                    if norm_val and norm_val != val:
                        quals.add(norm_val)
                    words = val.split()
                    if words:
                        w_clean = words[0].strip(".,()[]{}")
                        if w_clean:
                            quals.add(w_clean)
                            norm_w = NORMALIZE_VAL_RE.sub("", w_clean)
                            if norm_w and norm_w != w_clean:
                                quals.add(norm_w)
                    # Extract parentheses/bracket abbreviations, e.g. "master of business administration (mba)" -> "mba"
                    for abbr in PAREN_ABBR_RE.findall(val):
                        abbr_clean = abbr.strip().strip(":,;.")
                        if abbr_clean:
                            quals.add(abbr_clean)
                            norm_abbr = NORMALIZE_VAL_RE.sub("", abbr_clean)
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
                
        for s in p.get("skills", []):
            if s.get("Skill"):
                skills.add(s["Skill"].strip().lower())
            if s.get("Sub-Skill"):
                sub_skills.add(s["Sub-Skill"].strip().lower())
                
    # Deduplicate: any term present in both quals and certs should live only in quals
    # (degree/education terms must not be matched as certifications)
    shared = quals & certs
    certs -= shared

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
    if skills:
        SKILLS = list(skills)
    if sub_skills:
        SUB_SKILLS = list(sub_skills)

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
            norm = NORMALIZE_DASH_DOT_RE.sub("", stripped)
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
        part_norm = NORMALIZE_DASH_DOT_RE.sub("", part)
        part_variations = {part, part_norm} if part_norm else {part}
        
        part_all_vars = set()
        for pv in part_variations:
            part_all_vars.update(get_stem_variations(pv))
            
        matched_tok = None
        for tok in temp_tokens:
            tok_norm = NORMALIZE_DASH_DOT_RE.sub("", tok)
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
        if OR_RE.search(between_text):
            has_or = True
        if AND_RE.search(between_text):
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
    # Map common proficiency typos to standard forms
    q_clean = q_clean.replace("funtional", "functional")
    q_clean = q_clean.replace("poficient", "proficient")
    q_clean = q_clean.replace("proficent", "proficient")
    q_clean = q_clean.replace("profficient", "proficient")
    # Normalize designation abbreviations
    q_clean = normalize_desig_abbreviations(q_clean)
    query_tokens = get_query_tokens(q_clean)
    
    result = {
        "original_query": query,
        "intent": IntentType.UNKNOWN,
        "designation": None,
        "designation_operator": "or",
        "department": None,
        "department_operator": "or",
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
        "certification_groups": None,
        "qualification": None,
        "qualification_operator": "or",
        "qualification_groups": None,
        "segment": None,
        "segment_operator": "or",
        "skill": None,
        "skill_operator": "and",
        "sub_skill": None,
        "sub_skill_operator": "or",
        "external_designation": None,
        "external_designation_operator": "or",
        "organization": None,
        "reviewed_proficiency": None,
        "is_core_skill": False,
        "skills_text": query # Fallback full query for semantic search
    }
    
    # 1. Experience extraction (Regex)
    range_match = EXP_RANGE_RE.search(q_clean)
    if range_match:
        result["experience_min"] = float(range_match.group(1))
        result["experience_max"] = float(range_match.group(2))
        matched, updated = match_and_consume_keyword(range_match.group(0), query_tokens)
        if matched:
            query_tokens = updated
    else:
        min_match = EXP_MIN_RE.search(q_clean)
        if min_match:
            result["experience_min"] = float(min_match.group(1))
            matched, updated = match_and_consume_keyword(min_match.group(0), query_tokens)
            if matched:
                query_tokens = updated
            
    # 2. Designation extraction (Keyword matching)
    # Check if query is explicitly asking for project management / managing projects as a skill
    is_pm_skill_query = False
    if any(pat.search(q_clean) for pat in PM_SKILL_PATTERNS):
        is_pm_skill_query = True

    designation_matches = []
    external_designation_matches = []
    
    # Split query into present and past parts if there is a past marker
    parts = PAST_MARKER_RE.split(q_clean, maxsplit=1)
    
    if len(parts) > 1:
        present_part = parts[0]
        past_part = parts[1]
        
        # Tokenize both parts
        present_tokens = get_query_tokens(present_part)
        past_tokens = get_query_tokens(past_part)
        
        # Match present designations
        desig_list = DESIGNATIONS
        if is_pm_skill_query:
            desig_list = [d for d in DESIGNATIONS if d.lower() != "project manager"]
            
        for desig in sorted(desig_list, key=lambda d: (len(get_query_tokens(d)), len(d)), reverse=True):
            matched, updated = match_and_consume_keyword(desig, present_tokens)
            if matched:
                designation_matches.append(desig.title())
                present_tokens = updated
                
        # Match past designations
        for desig in sorted(desig_list, key=lambda d: (len(get_query_tokens(d)), len(d)), reverse=True):
            matched, updated = match_and_consume_keyword(desig, past_tokens)
            if matched:
                external_designation_matches.append(desig.title())
                past_tokens = updated
                
        # Reconstruct query_tokens by removing matched designations
        for dm in designation_matches:
            _, query_tokens = match_and_consume_keyword(dm, query_tokens)
        for edm in external_designation_matches:
            _, query_tokens = match_and_consume_keyword(edm, query_tokens)
    else:
        # Standard designation matching
        desig_list = DESIGNATIONS
        if is_pm_skill_query:
            desig_list = [d for d in DESIGNATIONS if d.lower() != "project manager"]
            
        for desig in sorted(desig_list, key=lambda d: (len(get_query_tokens(d)), len(d)), reverse=True):
            matched, updated = match_and_consume_keyword(desig, query_tokens)
            if matched:
                designation_matches.append(desig.title())
                query_tokens = updated

    if designation_matches:
        result["designation"] = designation_matches[0] if len(designation_matches) == 1 else designation_matches
        result["designation_operator"] = detect_operator(q_clean, designation_matches, "or")

    if external_designation_matches:
        result["external_designation"] = external_designation_matches[0] if len(external_designation_matches) == 1 else external_designation_matches
        result["external_designation_operator"] = detect_operator(q_clean, external_designation_matches, "or")
            
    # 2b. Department extraction
    dept_terms = {
        "contracts administration": "CONTRACTS ADMINISTRATION",
        "contracts": "CONTRACTS",
        "accounts": "ACCOUNTS",
        "billing": "BILLING",
        "business development": "BUSINESS DEVELOPMENT",
        "civil": "CIVIL",
        "ehs": "EHS",
        "electrical": "ELEC",
        "elec": "ELEC",
        "elv & ict": "ELV & ICT",
        "elv": "ELV & ICT",
        "ict": "ELV & ICT",
        "facade": "FACADE",
        "finishing": "FINISHES",
        "finishes": "FINISHES",
        "formwork": "FORMWORKS",
        "formworks": "FORMWORKS",
        "geotechnical": "GEOTECHNICAL",
        "hvac": "HVAC",
        "mechanical": "MECH",
        "mech": "MECH",
        "mep": "MEP",
        "o&m": "O&M",
        "p&m": "P&M",
        "planning": "PLANNING",
        "precast": "PRECAST",
        "procurement": "PROCUREMENT",
        "public health": "PUBLIC HEALTH",
        "quality assurance": "QA/QC",
        "quality control": "QA/QC",
        "quality": "QUALITY",
        "qa/qc": "QA/QC",
        "qa": "QA/QC",
        "qc": "QA/QC",
        "quantity survey": "QUANTITY SURVEY",
        "quantity surveying": "QUANTITY SURVEY",
        "steel structure": "STEEL STRUCTURE",
        "stores": "STORES",
        "survey": "SURVEY"
    }
    
    department_matches = []
    for term in sorted(dept_terms.keys(), key=lambda t: len(t), reverse=True):
        matched, updated = match_and_consume_keyword(term, query_tokens)
        if matched:
            dept_name = dept_terms[term]
            if dept_name not in department_matches:
                department_matches.append(dept_name)
            query_tokens = updated
            # Consume "department" and "dept" from query_tokens if they exist
            for d_word in ["department", "dept"]:
                while d_word in query_tokens:
                    query_tokens.remove(d_word)
            
    if department_matches:
        result["department"] = department_matches[0] if len(department_matches) == 1 else department_matches
        result["department_operator"] = detect_operator(q_clean, department_matches, "or")

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

    # Detect if query is explicitly asking about qualifications/education
    # (used only for intent scoring, not for blocking certs — deduplication handles that)
    qualification_context = bool(QUALIFICATION_CONTEXT_RE.search(q_clean))

    # 4. PRE-PASS: Detect slash-separated grouped patterns for qualification and certification.
    # e.g. "B.Tech/B.E and M.Tech/M.E" → qualification_groups: [["B.Tech","B.E"],["M.Tech","M.E"]]
    # Strategy: split query on " and " or " & ", then check each part for slash-separated keywords.
    def _find_slash_groups(keyword_list, query_str, is_qual=True):
        """
        Looks for slash-separated patterns in query parts (split by 'and'/'&').
        Returns (groups, consumed_tokens) if a multi-group pattern is found, else (None, []).
        """
        # Split raw query on ' and ', ' & ', ' AND '
        and_parts = AND_SPLIT_RE.split(query_str)
        if len(and_parts) < 2:
            return None, []

        all_groups = []
        all_consumed = []
        for part in and_parts:
            # Check for slash within this part using the keyword list
            slash_candidates = SLASH_SPLIT_RE.split(part.strip())
            group = []
            part_consumed = []
            for candidate in slash_candidates:
                candidate_clean = candidate.strip().strip(".,()[]{}'\";:").lower()
                # Try matching this candidate against the keyword list
                for kw in sorted(keyword_list, key=lambda k: (len(get_query_tokens(k)), len(k)), reverse=True):
                    kw_norm = NORMALIZE_VAL_RE.sub("", kw.lower())
                    cand_norm = NORMALIZE_VAL_RE.sub("", candidate_clean)
                    if kw_norm == cand_norm or kw.lower() == candidate_clean:
                        display = kw.upper() if not is_qual else kw.title()
                        group.append(display)
                        part_consumed.append(candidate_clean)
                        break
            if group:
                all_groups.append(group)
                all_consumed.extend(part_consumed)
        # Only use groups if we found at least 2 groups (otherwise it's a plain single filter)
        if len(all_groups) >= 2:
            return all_groups, all_consumed
        return None, []

    # Try qualification groups first
    qual_groups, qual_consumed = _find_slash_groups(QUALIFICATIONS, q_clean, is_qual=True)
    if qual_groups:
        result["qualification_groups"] = qual_groups
        result["qualification"] = None  # clear flat field to avoid double-filtering
        # Remove consumed tokens from query_tokens
        for consumed in qual_consumed:
            for tok in list(query_tokens):
                if NORMALIZE_VAL_RE.sub("", tok) == NORMALIZE_VAL_RE.sub("", consumed):
                    try:
                        query_tokens.remove(tok)
                    except ValueError:
                        pass
                    break

    # Try certification groups
    cert_groups, cert_consumed = _find_slash_groups(CERTIFICATIONS, q_clean, is_qual=False)
    if cert_groups:
        result["certification_groups"] = cert_groups
        result["certification"] = None  # clear flat field to avoid double-filtering
        for consumed in cert_consumed:
            for tok in list(query_tokens):
                if NORMALIZE_VAL_RE.sub("", tok) == NORMALIZE_VAL_RE.sub("", consumed):
                    try:
                        query_tokens.remove(tok)
                    except ValueError:
                        pass
                    break

    # 4. Certification extraction (only if no groups were detected)
    # Note: CERTIFICATIONS has already had any edu-degree overlap removed by deduplication in update_keyword_lists,
    # so terms like 'mba', 'b.tech', 'diploma' will NOT appear in CERTIFICATIONS.
    certification_matches = []
    if not result["certification_groups"]:
        for cert in sorted(CERTIFICATIONS, key=lambda c: (len(get_query_tokens(c)), len(c)), reverse=True):
            matched, updated = match_and_consume_keyword(cert, query_tokens)
            if matched:
                certification_matches.append(cert.upper())
                query_tokens = updated
        if certification_matches:
            result["certification"] = certification_matches[0] if len(certification_matches) == 1 else certification_matches
            result["certification_operator"] = detect_operator(q_clean, certification_matches, "and")

    # 5. Qualification extraction (only if no groups were detected)
    qualification_matches = []
    if not result["qualification_groups"]:
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
    band_match = BAND_RE.search(q_clean)
    if band_match:
        band_letter = band_match.group(1) or band_match.group(2)
        result["band"] = f"{band_letter.upper()} - Band"
        matched, updated = match_and_consume_keyword(band_match.group(0), query_tokens)
        if matched:
            query_tokens = updated
    else:
        tier_match = TIER_RE.search(q_clean)
        if tier_match:
            result["band"] = f"Tier {tier_match.group(1)}"
            matched, updated = match_and_consume_keyword(tier_match.group(0), query_tokens)
            if matched:
                query_tokens = updated

    # Cadre extraction
    cadre_match = CADRE_RE.search(q_clean)
    if cadre_match:
        result["cadre"] = (cadre_match.group(1) or cadre_match.group(2)).upper()
        matched, updated = match_and_consume_keyword(cadre_match.group(0), query_tokens)
        if matched:
            query_tokens = updated
    else:
        cadre_pat = CADRE_PAT_RE.search(q_clean)
        if cadre_pat:
            result["cadre"] = cadre_pat.group(1).upper()
            matched, updated = match_and_consume_keyword(cadre_pat.group(0), query_tokens)
            if matched:
                query_tokens = updated

    # SBG extraction
    sbg_match = SBG_RE.search(q_clean)
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
        
    skill_matches = []
    sub_skill_matches = []
    
    # 1. Process pm skill query specifically if flagged
    if is_pm_skill_query:
        if "Project Management" not in skill_matches:
            skill_matches.append("Project Management")
        # Consume tokens matching pm skill patterns from query_tokens
        for pat in PM_SKILL_PATTERNS:
            match_obj = pat.search(q_clean)
            if match_obj:
                matched_phrase = match_obj.group(0)
                _, query_tokens = match_and_consume_keyword(matched_phrase, query_tokens)

    # 2. Extract known sub-skills first (more specific)
    for sub_sk in sorted(SUB_SKILLS, key=lambda s: (len(get_query_tokens(s)), len(s)), reverse=True):
        matched, updated = match_and_consume_keyword(sub_sk, query_tokens)
        if matched:
            sub_sk_title = sub_sk.title()
            if sub_sk_title not in sub_skill_matches:
                sub_skill_matches.append(sub_sk_title)
            query_tokens = updated
            
    # 3. Extract known main skills
    for sk in sorted(SKILLS, key=lambda s: (len(get_query_tokens(s)), len(s)), reverse=True):
        matched, updated = match_and_consume_keyword(sk, query_tokens)
        if matched:
            sk_title = sk.title()
            if sk_title not in skill_matches:
                skill_matches.append(sk_title)
            query_tokens = updated
            
    # 4. Fallback regex skill extraction for remaining query tokens
    remaining_query = " ".join(query_tokens)
    skill_match = SKILL_MATCH_RE.search(remaining_query)
    if skill_match:
        skill_captured = skill_match.group(1).strip()
        for conn_re in CONNECTOR_RES:
            parts = conn_re.split(skill_captured, maxsplit=1)
            if len(parts) > 1 and parts[0].strip():
                skill_captured = parts[0].strip()
            
        if skill_captured.startswith("in "):
            skill_captured = skill_captured[3:].strip()
            
        skill_parts = SKILL_SPLIT_RE.split(skill_captured)
        regex_skills = [s.strip().title() for s in skill_parts if s.strip() and s.strip().lower() not in SKILL_STOP_WORDS]
        for rs in regex_skills:
            # Check if this rs matches any known sub-skill
            is_sub = False
            for sub_sk in SUB_SKILLS:
                if normalize_val(rs) == normalize_val(sub_sk):
                    sub_sk_title = sub_sk.title()
                    if sub_sk_title not in sub_skill_matches:
                        sub_skill_matches.append(sub_sk_title)
                    is_sub = True
                    break
            if not is_sub:
                # Check if it's a known main skill
                is_main = False
                for sk in SKILLS:
                    if normalize_val(rs) == normalize_val(sk):
                        sk_title = sk.title()
                        if sk_title not in skill_matches:
                            skill_matches.append(sk_title)
                        is_main = True
                        break
                if not is_main:
                    # Treat unknown extracted skill as general skill
                    if rs not in skill_matches:
                        skill_matches.append(rs)

    if skill_matches:
        result["skill"] = skill_matches[0] if len(skill_matches) == 1 else skill_matches
        result["skill_operator"] = detect_operator(q_clean, skill_matches, "and")
        
    if sub_skill_matches:
        result["sub_skill"] = sub_skill_matches[0] if len(sub_skill_matches) == 1 else sub_skill_matches
        result["sub_skill_operator"] = detect_operator(q_clean, sub_skill_matches, "or")
        
    # 10. Intent determination
    is_refinement = any(re.match(rf"^{trigger}", q_clean) for trigger in REFINEMENT_TRIGGERS)
    
    has_structured = any([
        result["designation"],
        result["department"],
        result["external_designation"],
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
        result["sub_skill"],
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
