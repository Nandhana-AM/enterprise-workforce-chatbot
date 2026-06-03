import re
from typing import Dict, Any, Optional, List
from enum import Enum
from backend.app.structured_search import normalize_val, normalize_desig_abbreviations





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
EXP_RANGE_RE = re.compile(r"(\d+)\s*(?:-|to)\s*(\d+)\s*years?(?:\s*experience)?")
EXP_MIN_RE = re.compile(r"(?:more than|at least|over|minimum|min)?\s*(\d+)\s*(?:\+|years?)(?:\s*experience)?")
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
    "b.tech", "m.tech", "b.e.", "m.e.", "mba", "diploma", "ph.d", "b.arch", "degree", "master", "doctorate",
    "btech", "mtech", "be", "me", "barch", "phd", "ssc", "hsc", "ba", "ma", "bsc", "msc", "bcom", "mcom",
    "llb", "llm", "bba", "bca", "dce", "dme", "deee", "dee", "dct", "lce", "dtech", "iti", "amie",
    "amice", "ceng", "ieng", "pgpacm", "pgp-acm", "pgppem", "pgp-pem", "pgpifdm", "pgp-ifdm",
    "pgpqscm", "pgp-qscm", "pgppm", "pgp-pm", "pgemp", "pgdmp", "pgdom", "pgdtqm", "pgdpm",
    "pgdm", "pgdcm", "pgdbm", "pgdhrm", "epgp-qsc", "epgp-eicm", "mms", "mplan", "mbl", "std", "x std",
    "viii std", "ix std", "v std", "high school", "matriculation", "schooling"
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

PROFICIENCIES = ["basic", "functional", "intermediate", "proficient", "expert", "role model"]

REFINEMENT_TRIGGERS = [
    r"\bonly\b", r"\balso\b", r"\bfilter\b", r"\brefine\b", r"\badd\b", r"\bwith\b"
]

SKILL_STOP_WORDS = {
    "the", "a", "an", "in", "on", "at", "to", "for", "with", "by", "of", "and", "or", "but", "from",
    "is", "are", "was", "were", "be", "been", "have", "has", "had", "do", "does", "did",
    "this", "that", "these", "those", "they", "them", "their", "he", "him", "his", "she", "her",
    "it", "its", "we", "us", "our", "you", "your", "who", "whom", "whose", "which", "what",
    "department", "dept", "min", "minimum", "max", "maximum", "experience", "exp", "years", "year",
    "skills", "skill", "people", "person", "show", "find", "worked", "working", "ex", "former",
    "previous", "prior", "past", "current", "currently", "excluding", "exclude", "except",
    "other", "than", "designation", "designations", "located", "location", "locations", "allocated",
    "project", "projects"
}

SKILLS = ["project management", "civil engineering", "electrical engineering", "digital & it", "mechanical engineering"]
SUB_SKILLS = []
SKILL_ALIASES_MAP = {}

# --- BU (Business Unit) & SBG (Strategic Business Group) keyword maps ---
# Each entry: "canonical_value": [list_of_query_aliases]
# Canonical value should match exactly what is stored in the Excel / profile data.
BU_ALIAS_MAP = {
    "CRS - Residential Space BU": ["crs residential", "crs - residential", "residential space bu"],
    "PSA - Airports BU":          ["psa airports", "airports bu", "airport bu", "psa - airports bu"],
    "LTO":                         ["lto"],
    "PSA - Factories BU":          ["psa factories", "factories bu", "factory bu", "psa - factories"],
    "Common":                      ["common bu"],
    "EDRC (Common)":               ["edrc common", "edrc"],
    "CRS - Health Segment":        ["crs health", "health segment bu"],
    "CRS - IT, OS & DC Segment":   ["crs it", "it os dc"],
    "PSA - Public Space Segment":  ["psa public", "psa public space"],
    "CESC - Formwork Mfg. (TS)":   ["cesc formwork", "formwork mfg", "cesc - formwork"],
    "Resources (OS)":              ["resources os"],
    "CSTI":                        ["csti"],
    "EDRC (RBU)":                  ["edrc rbu"],
    "B&F - Fast":                  ["b&f fast bu", "b and f fast"],
    "EDRC (Factory BU)":           ["edrc factory", "edrc factory bu"],
    "Fast":                        ["fast bu"],
    "Contracts (Common)":          ["contracts common", "contracts bu", "contracts (common)"],
    "Corporate Centre":            ["corporate centre", "corporate center"],
    "CRS - SBG (Common)":          ["crs sbg common", "crs sbg bu"],
    "CESC - Steel Service Centre (TS)": ["cesc steel", "steel service centre", "steel service bu"],
    "BSCC - Formwork (TS)":        ["bscc formwork", "bscc"],
    "Procurement":                 ["procurement bu", "procurement"],
    "Head Office":                 ["head office", "ho bu"],
    "Workmen Mgmt. Centre (OS)":   ["workmen mgmt", "workmen management"],
    "Quarry (OS)":                 ["quarry bu", "quarry"],
    "Quality (OS)":                ["quality os", "quality bu"],
    "Finishing (TS)":              ["finishing bu", "finishing ts"],
}

SBG_ALIAS_MAP = {
    "Commercial & Residential Spaces": [
        "commercial residential spaces", "commercial residential",
        "commercial & residential spaces", "commercial and residential spaces",
        "commercial & residential", "commercial and residential",
        "commercial projects", "commercial", "crs sbg",
    ],
    "Public Spaces & Airports": [
        "public spaces airports", "public spaces & airports",
        "public spaces and airports", "airports sbg",
        "public & airports", "public and airports",
        "public spaces",
    ],
    "Common": ["common sbg"],
    "B&F - FAST": ["b&f fast", "bnf fast", "b&f", "fast sbg", "b and f"],
}

# Flat alias lookup: alias_lower -> canonical value
_BU_ALIAS_LOOKUP: dict = {}
for _can, _aliases in BU_ALIAS_MAP.items():
    for _a in _aliases:
        _BU_ALIAS_LOOKUP[_a.lower()] = _can
    _BU_ALIAS_LOOKUP[_can.lower()] = _can  # canonical itself

_SBG_ALIAS_LOOKUP: dict = {}
for _can, _aliases in SBG_ALIAS_MAP.items():
    for _a in _aliases:
        _SBG_ALIAS_LOOKUP[_a.lower()] = _can
    _SBG_ALIAS_LOOKUP[_can.lower()] = _can  # canonical itself


def update_keyword_lists(profiles: List[Dict[str, Any]]):
    """
    Dynamically rebuilds keyword lists for the rule-based parser based on the loaded dataset.
    Also updates BU/SBG alias lookups from real profile data.
    """
    global DESIGNATIONS, CLUSTERS, CERTIFICATIONS, QUALIFICATIONS, SEGMENTS, ORGANIZATIONS, SKILLS, SUB_SKILLS, SKILL_ALIASES_MAP
    global _BU_ALIAS_LOOKUP, _SBG_ALIAS_LOOKUP
    
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
    original_skills_set = {
        "Project Management", "Civil Engineering", "Electrical Engineering", "Digital & IT", "Mechanical Engineering"
    }
    
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
                        for w in words:
                            w_clean = w.strip(".,()[]{}")
                            if w_clean and len(w_clean) > 2:
                                quals.add(w_clean)
                                norm_w = NORMALIZE_VAL_RE.sub("", w_clean)
                                if norm_w and norm_w != w_clean:
                                    quals.add(norm_w)
                                # Handle hyphenated prefixes e.g. "mtech-construction" -> add "mtech"
                                if "-" in w_clean:
                                    parts = w_clean.split("-")
                                    if parts:
                                        first_part = parts[0].strip()
                                        if first_part:
                                            quals.add(first_part)
                                            norm_first = NORMALIZE_VAL_RE.sub("", first_part)
                                            if norm_first and norm_first != first_part:
                                                quals.add(norm_first)
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
                original_skills_set.add(s["Skill"].strip())
            if s.get("Sub-Skill"):
                sub_skills.add(s["Sub-Skill"].strip().lower())
                original_skills_set.add(s["Sub-Skill"].strip())
                
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

    # Rebuild alias map
    SKILL_ALIASES_MAP = {}
    for orig in original_skills_set:
        aliases = get_skill_aliases(orig)
        for alias in aliases:
            alias_lower = alias.lower()
            if alias_lower not in SKILL_ALIASES_MAP:
                SKILL_ALIASES_MAP[alias_lower] = set()
            SKILL_ALIASES_MAP[alias_lower].add(orig)

    # Filter to prioritize exact canonical names when an alias matches a canonical name exactly
    for alias_lower, originals in list(SKILL_ALIASES_MAP.items()):
        exact_match = next((orig for orig in originals if orig.lower() == alias_lower), None)
        if exact_match:
            SKILL_ALIASES_MAP[alias_lower] = {exact_match}

    # Dynamically extend BU/SBG alias lookups from real profile data
    for p in profiles:
        bu_val = p.get("bu") or ""
        if bu_val and bu_val.lower() not in _BU_ALIAS_LOOKUP:
            _BU_ALIAS_LOOKUP[bu_val.lower()] = bu_val  # exact match
        sbg_val = p.get("sbg") or ""
        if sbg_val and sbg_val.lower() not in _SBG_ALIAS_LOOKUP:
            _SBG_ALIAS_LOOKUP[sbg_val.lower()] = sbg_val  # exact match

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
            stem = tok[:-3] + "y"
            if len(stem) >= 3:
                vars_.add(stem)
        elif tok.endswith("es") and not tok.endswith("ss"):
            stem1 = tok[:-2]
            stem2 = tok[:-1]
            if len(stem1) >= 3:
                vars_.add(stem1)
            if len(stem2) >= 3:
                vars_.add(stem2)
        elif tok.endswith("s") and not tok.endswith("ss"):
            stem = tok[:-1]
            if len(stem) >= 3:
                vars_.add(stem)
            
        # Strip common suffixes for matching variations (gerunds, adjectives, past tense)
        if tok.endswith("ing"):
            stem = tok[:-3]
            if len(stem) >= 3:
                vars_.add(stem)
                # Handle double consonant, e.g. "quarrying" -> "quarry", "tunnelling" -> "tunnel"
                if len(tok) > 5 and tok[-4] == tok[-5]:
                    stem_double = tok[:-4]
                    if len(stem_double) >= 3:
                        vars_.add(stem_double)
                # Handle e.g. "piping" -> "pipe"
                stem_pipe = tok[:-3] + "e"
                if len(stem_pipe) >= 3:
                    vars_.add(stem_pipe)
        elif tok.endswith("ed"):
            stem1 = tok[:-2]
            stem2 = tok[:-1]
            if len(stem1) >= 3:
                vars_.add(stem1)
            if len(stem2) >= 3:
                vars_.add(stem2)
            if len(tok) > 4 and tok[-3] == tok[-4]:
                stem3 = tok[:-3]
                if len(stem3) >= 3:
                    vars_.add(stem3)
        elif tok.endswith("er") or tok.endswith("or"):
            stem1 = tok[:-2]
            if len(stem1) >= 3:
                vars_.add(stem1)
            if len(tok) > 4 and tok[-3] == tok[-4]:
                stem2 = tok[:-3]
                if len(stem2) >= 3:
                    vars_.add(stem2)
    return vars_

def get_skill_aliases(skill_name: str) -> List[str]:
    aliases = [skill_name]
    # Split by colon, comma, slash, hyphen, or standard connectors
    parts = re.split(r"[:;,\-/]|\band\b|\b&\b", skill_name)
    for p in parts:
        p_clean = p.strip()
        if p_clean and len(p_clean) > 2 and p_clean.lower() not in SKILL_STOP_WORDS:
            aliases.append(p_clean)
    return list(set(aliases))

def match_skill_in_tokens(alias: str, query_tokens: List[str], skipped_indices: set[int], exact_only: bool = False) -> Optional[List[int]]:
    alias_words = alias.lower().split()
    cleaned_parts = []
    for wp in alias_words:
        stripped = wp.strip(".,()[]{}\"';:?!*&")
        if stripped:
            cleaned_parts.append(stripped)
            
    if not cleaned_parts:
        return None
        
    def find_match(part_idx: int, current_indices: list[int]) -> Optional[list[int]]:
        if part_idx == len(cleaned_parts):
            return current_indices
            
        part = cleaned_parts[part_idx]
        part_norm = NORMALIZE_DASH_DOT_RE.sub("", part)
        part_variations = {part, part_norm} if part_norm else {part}
        
        part_all_vars = set()
        for pv in part_variations:
            if exact_only:
                part_all_vars.add(pv)
            else:
                part_all_vars.update(get_stem_variations(pv))
            
        for idx, tok in enumerate(query_tokens):
            if idx in skipped_indices or idx in current_indices:
                continue
            tok_norm = NORMALIZE_DASH_DOT_RE.sub("", tok)
            tok_variations = {tok, tok_norm} if tok_norm else {tok}
            
            tok_all_vars = set()
            for tv in tok_variations:
                if exact_only:
                    tok_all_vars.add(tv)
                else:
                    tok_all_vars.update(get_stem_variations(tv))
                
            if part_all_vars.intersection(tok_all_vars):
                new_indices = current_indices + [idx]
                if len(new_indices) > 1:
                    sorted_indices = sorted(new_indices)
                    span = sorted_indices[-1] - sorted_indices[0]
                    max_allowed = len(cleaned_parts) + 1
                    if span > max_allowed:
                        continue
                res = find_match(part_idx + 1, new_indices)
                if res is not None:
                    return res
        return None

    matched_indices = find_match(0, [])
    if matched_indices is None:
        return None
    return sorted(matched_indices)

PROF_MAP = {
    "basic": "Basic",
    "functional": "Functional",
    "intermediate": "Intermediate",
    "proficient": "Proficient",
    "expert": "Expert",
    "role model": "Role Model",
    "rolemodel": "Role Model"
}

def extract_proficiencies_from_window(window_tokens: List[str]) -> tuple[List[str], str]:
    found = []
    text = " ".join(window_tokens).lower()
    
    positions = []
    for key, val in PROF_MAP.items():
        pattern = re.compile(rf"\b{re.escape(key)}\b")
        for match in pattern.finditer(text):
            positions.append((match.start(), val))
            
    positions.sort()
    for pos, val in positions:
        if val not in found:
            found.append(val)
            
    operator = "or"
    if "and" in text or "&" in text:
        operator = "and"
        
    return found, operator

def extract_proficiencies_for_skill(indices: List[int], query_tokens: List[str], other_skill_indices: set[int]) -> tuple[List[str], str]:
    start_idx = indices[0]
    end_idx = indices[-1]
    
    pre_start = max(0, start_idx - 5)
    for idx in range(start_idx - 1, pre_start - 1, -1):
        if idx in other_skill_indices:
            pre_start = idx + 1
            break
    preceding_tokens = query_tokens[pre_start:start_idx]
    
    post_end = min(len(query_tokens), end_idx + 4)
    for idx in range(end_idx + 1, post_end):
        if idx in other_skill_indices:
            post_end = idx
            break
    following_tokens = query_tokens[end_idx + 1:post_end]
    
    pre_found, pre_op = extract_proficiencies_from_window(preceding_tokens)
    post_found, post_op = extract_proficiencies_from_window(following_tokens)
    
    if pre_found:
        return pre_found, pre_op
    if post_found:
        return post_found, post_op
        
    return [], "or"

def is_department_term_valid(term: str, query_tokens: List[str]) -> bool:
    """Returns True only if the dept term appears in a department context.
    Blocks the term if it is surrounded by skill-context words or if it is part of
    a multi-word skill match present in the query.
    """
    indices = match_skill_in_tokens(term, query_tokens, set())
    if not indices:
        return False
    first_idx = indices[0]
    last_idx = indices[-1]
    # Block if the next token suggests a skill context
    if last_idx + 1 < len(query_tokens):
        next_tok = query_tokens[last_idx + 1].lower()
        if next_tok in ("skill", "skills", "sub", "category", "area", "work", "works"):
            return False
    # Block if the previous token suggests a skill context
    if first_idx > 0:
        prev_tok = query_tokens[first_idx - 1].lower()
        if prev_tok in ("sub", "sub-skill", "sub-skills", "skill", "skills"):
            return False
            
    # Block if this term is part of a longer multi-word skill match in the query
    # to prevent single-word department matching from breaking multi-word skills.
    for alias in SKILL_ALIASES_MAP.keys():
        alias_words = alias.split()
        if len(alias_words) > 1 and term.lower() in alias_words:
            # Check if this multi-word skill matches the query
            alias_indices = match_skill_in_tokens(alias, query_tokens, set())
            if alias_indices:
                # Check if the current term's index is part of the matched skill indices
                if any(idx in alias_indices for idx in indices):
                    return False
    return True


def is_false_positive_qual(tok: str, prev_tok: Optional[str], next_tok: Optional[str]) -> bool:
    tok_lower = tok.lower()
    if tok_lower == "me":
        verbs = {"show", "find", "give", "list", "tell", "get", "identify", "search"}
        nouns = {"people", "person", "employee", "employees", "candidate", "candidates", "resume", "resumes", "profile", "profiles"}
        if prev_tok and prev_tok.lower() in verbs:
            return True
        if next_tok and next_tok.lower() in nouns:
            return True
    elif tok_lower == "be":
        aux_verbs = {"should", "must", "to", "can", "will", "would", "could", "shall", "may", "might"}
        if prev_tok and prev_tok.lower() in aux_verbs:
            return True
    return False


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
        for i, tok in enumerate(temp_tokens):
            tok_norm = NORMALIZE_DASH_DOT_RE.sub("", tok)
            tok_variations = {tok, tok_norm} if tok_norm else {tok}
            
            tok_all_vars = set()
            for tv in tok_variations:
                tok_all_vars.update(get_stem_variations(tv))
                
            if part_all_vars.intersection(tok_all_vars):
                prev_tok = temp_tokens[i - 1] if i > 0 else None
                next_tok = temp_tokens[i + 1] if i < len(temp_tokens) - 1 else None
                if is_false_positive_qual(tok, prev_tok, next_tok):
                    continue
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
        patterns = []
        m_escaped = re.escape(m.lower())
        patterns.append(rf"\b{m_escaped}\b")
        
        m_norm = NORMALIZE_VAL_RE.sub("", m.lower())
        if m_norm != m.lower():
            patterns.append(rf"\b{re.escape(m_norm)}\b")
            
        m_flex = re.sub(r"\\?[\.\-\s]+", r"[\.\-\\s]*", m_escaped)
        if m_flex != m_escaped:
            patterns.append(rf"\b{m_flex}\b")
            
        search = None
        for pat in patterns:
            try:
                search = re.compile(pat).search(query_lower)
                if search:
                    break
            except re.error:
                continue
                
        if search:
            positions.append((search.start(), search.end(), m))
            
    if len(positions) < 2:
        return default_op
        
    positions.sort()
    
    has_or = False
    has_and = False
    has_comma = False
    for i in range(len(positions) - 1):
        end_current = positions[i][1]
        start_next = positions[i+1][0]
        between_text = query_lower[end_current:start_next]
        if OR_RE.search(between_text):
            has_or = True
        if AND_RE.search(between_text):
            has_and = True
        if "," in between_text:
            has_comma = True
            
    if has_comma and default_op == "or":
        return "or"
        
    if has_or and not has_and:
        return "or"
    if has_and and not has_or:
        return "and"
        
    if "or" in query_lower:
        return "or"
    if "and" in query_lower or "both" in query_lower:
        return "and"
        
    return default_op




def parse_operator_refinements(query: str, result: Dict[str, Any]) -> bool:
    """
    Parses explicit requests to change logical operators (e.g. 'use OR logic for qualifications')
    and updates result in-place. Returns True if any operator refinement was detected.
    """
    q_clean = query.lower().strip()
    
    # Check for patterns like "or logic", "and logic", "or operator", "and operator"
    logic_match = re.search(r"\b(and|or)\b\s+(?:logic|operator|mode|relationship)", q_clean)
    if not logic_match:
        # Check reverse pattern: "qualification and/or" / "qualification logic is and/or"
        logic_match = re.search(r"(?:logic|operator)\s+(?:is\s+)?\b(and|or)\b", q_clean)
    if not logic_match:
        # Also match simple "use and/or for..."
        logic_match = re.search(r"\buse\s+\b(and|or)\b", q_clean)
        
    if logic_match:
        op = logic_match.group(1).lower()
        target_field = None
        if "qualification" in q_clean or "degree" in q_clean or "qual" in q_clean:
            target_field = "qualification"
        elif "certification" in q_clean or "cert" in q_clean:
            target_field = "certification"
        elif "location" in q_clean or "place" in q_clean or "cluster" in q_clean:
            target_field = "location"
        elif "designation" in q_clean or "role" in q_clean or "job" in q_clean:
            target_field = "designation"
        elif "department" in q_clean or "dept" in q_clean:
            target_field = "department"
            
        if target_field:
            result[f"{target_field}_operator"] = op
            result["intent"] = IntentType.REFINEMENT
            return True
            
    # Also support simpler patterns like: "qualification: or" or "qualification operator: or"
    for field, terms in [
        ("qualification", ["qualification", "degree", "qual"]),
        ("certification", ["certification", "cert"]),
        ("location", ["location", "place", "cluster"]),
        ("designation", ["designation", "role", "job"]),
        ("department", ["department", "dept"])
    ]:
        for term in terms:
            pattern = rf"\b{term}\b.*?\b(and|or)\b"
            m = re.search(pattern, q_clean)
            if m:
                op = m.group(1).lower()
                result[f"{field}_operator"] = op
                result["intent"] = IntentType.REFINEMENT
                return True
                
    return False


def parse_query_rules(query: str) -> Dict[str, Any]:
    """
    Rule-based parser using spaCy, regex, and keyword lists to extract structured components.
    """
    q_clean = query.lower().strip()
    # Normalize spaces after dots (e.g., "b. tech" -> "b.tech", "b. e." -> "b.e.")
    # Exclude trailing dots followed by stop words to prevent merging "b.e. and" into "b.e.and"
    q_clean = re.sub(r"\b([a-zA-Z]+)\.\s+(?!(?:and|or|with|in|has|who|for)\b)([a-zA-Z])", r"\1.\2", q_clean)
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
        "exclude_department": None,
        "exclude_department_operator": "or",
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
        "skill_requirements": None,
        "skills_text": query # Fallback full query for semantic search
    }
    
    # Check for operator refinements first
    parse_operator_refinements(query, result)
    
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

    # 1b. BU & SBG extraction — run EARLY, before designation/department/segment
    # so tokens like 'formwork', 'contracts', 'airports' are claimed by BU/SBG first.
    _has_bu_keyword  = "bu"  in q_clean.split()
    _has_sbg_keyword = "sbg" in q_clean.split()

    # Aliases that only trigger when their context keyword ('bu'/'sbg') is present in the query
    _bu_needs_context  = {"common bu", "contracts bu", "procurement bu", "quarry bu",
                          "fast bu", "finishing bu", "ho bu", "quality bu"}
    _sbg_needs_context = {"common sbg", "psa"}

    def _extract_bu(tokens):
        for alias in sorted(_BU_ALIAS_LOOKUP.keys(), key=len, reverse=True):
            if alias in _bu_needs_context and not _has_bu_keyword:
                continue
            alias_toks = alias.lower().split()
            temp = list(tokens)
            hit_toks = []
            found_all = True
            for at in alias_toks:
                at_n = NORMALIZE_DASH_DOT_RE.sub("", at)
                hit = next((t for t in temp if t == at or NORMALIZE_DASH_DOT_RE.sub("", t) == at_n), None)
                if hit:
                    hit_toks.append(hit); temp.remove(hit)
                else:
                    found_all = False; break
            if found_all and hit_toks:
                updated = list(tokens)
                for ht in hit_toks:
                    try: updated.remove(ht)
                    except ValueError: pass
                if "bu" in updated: updated.remove("bu")
                return _BU_ALIAS_LOOKUP[alias], updated
        return None, tokens

    def _extract_sbg(tokens):
        for alias in sorted(_SBG_ALIAS_LOOKUP.keys(), key=len, reverse=True):
            if alias in _sbg_needs_context and not _has_sbg_keyword:
                continue
            alias_toks = alias.lower().split()
            temp = list(tokens)
            hit_toks = []
            found_all = True
            for at in alias_toks:
                at_n = NORMALIZE_DASH_DOT_RE.sub("", at)
                hit = next((t for t in temp if t == at or NORMALIZE_DASH_DOT_RE.sub("", t) == at_n), None)
                if hit:
                    hit_toks.append(hit); temp.remove(hit)
                else:
                    found_all = False; break
            if found_all and hit_toks:
                updated = list(tokens)
                for ht in hit_toks:
                    try: updated.remove(ht)
                    except ValueError: pass
                if "sbg" in updated: updated.remove("sbg")
                return _SBG_ALIAS_LOOKUP[alias], updated
        return None, tokens

    # When 'sbg' explicit, try SBG first; then BU; then fallback SBG
    if _has_sbg_keyword:
        sbg_val, query_tokens = _extract_sbg(query_tokens)
        if sbg_val: result["sbg"] = sbg_val
    if not result.get("bu"):
        bu_val, query_tokens = _extract_bu(query_tokens)
        if bu_val: result["bu"] = bu_val
    if not result.get("sbg"):
        sbg_val, query_tokens = _extract_sbg(query_tokens)
        if sbg_val: result["sbg"] = sbg_val

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
        # NOTE: "finishing"/"finishes"/"formwork" removed — these are skill categories,
        # not organizational departments. Department filter for FORMWORKS preserved.
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
        "qa & qc": "QA/QC",
        "qa&qc": "QA/QC",
        "qa": "QA/QC",
        "qc": "QA/QC",
        "quantity survey": "QUANTITY SURVEY",
        "quantity surveying": "QUANTITY SURVEY",
        "steel structure": "STEEL STRUCTURE",
        "stores": "STORES",
        "survey": "SURVEY"
    }
    
    # 2b. Exclude Department extraction
    exclude_matches = []
    
    # Check for exclusion phrases in the query
    exclude_pattern = re.compile(r"\b(exclude|excluding|except(?:\s+for)?|other\s+than|not\s+in)\s+([a-zA-Z\s\&]+)\b")
    for match_obj in exclude_pattern.finditer(q_clean):
        exclude_phrase = match_obj.group(2).strip()
        phrase_tokens = get_query_tokens(exclude_phrase)
        for term in sorted(dept_terms.keys(), key=lambda t: len(t), reverse=True):
            if not is_department_term_valid(term, query_tokens):
                continue
            matched, updated = match_and_consume_keyword(term, phrase_tokens)
            if matched:
                dept_name = dept_terms[term]
                if dept_name not in exclude_matches:
                    exclude_matches.append(dept_name)
                phrase_tokens = updated
                
        # Remove matched exclude departments from the main query_tokens
        for em in exclude_matches:
            for term in sorted(dept_terms.keys(), key=lambda t: len(t), reverse=True):
                if dept_terms[term] == em:
                    matched_main, updated_main = match_and_consume_keyword(term, query_tokens)
                    if matched_main:
                        query_tokens = updated_main
                        break
                        
    # Clean exclude keywords and department/dept from query_tokens
    for ex_keyword in ["exclude", "excluding", "except", "other", "than", "not", "in", "department", "dept"]:
        while ex_keyword in query_tokens:
            query_tokens.remove(ex_keyword)
            
    if exclude_matches:
        result["exclude_department"] = exclude_matches[0] if len(exclude_matches) == 1 else exclude_matches
        result["exclude_department_operator"] = detect_operator(q_clean, exclude_matches, "or")

    # 2c. Positive Department extraction
    department_matches = []
    for term in sorted(dept_terms.keys(), key=lambda t: len(t), reverse=True):
        if not is_department_term_valid(term, query_tokens):
            continue
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
        Returns (groups, consumed_tokens) if a slash-group pattern is found, else (None, []).
        """
        if "/" not in query_str:
            return None, []
            
        and_parts = AND_SPLIT_RE.split(query_str)
        
        all_groups = []
        all_consumed = []
        for part in and_parts:
            slash_candidates = SLASH_SPLIT_RE.split(part.strip())
            group = []
            part_consumed = []
            
            N = len(slash_candidates)
            for idx, candidate in enumerate(slash_candidates):
                candidate_clean = candidate.strip().lower()
                
                matched_kw = None
                for kw in sorted(keyword_list, key=lambda k: (len(get_query_tokens(k)), len(k)), reverse=True):
                    kw_lower = kw.lower()
                    kw_norm = NORMALIZE_VAL_RE.sub("", kw_lower)
                    
                    if N == 1:
                        cand_tokens = [NORMALIZE_VAL_RE.sub("", t) for t in get_query_tokens(candidate_clean)]
                        if kw_norm in cand_tokens:
                            matched_kw = kw
                            for t in get_query_tokens(candidate_clean):
                                if NORMALIZE_VAL_RE.sub("", t) == kw_norm:
                                    part_consumed.append(t)
                                    break
                            break
                    elif idx == 0:
                        cand_words = candidate_clean.split()
                        if cand_words:
                            kw_word_count = len(kw_lower.split())
                            if len(cand_words) >= kw_word_count:
                                target_phrase = " ".join(cand_words[-kw_word_count:])
                                if NORMALIZE_VAL_RE.sub("", target_phrase) == kw_norm:
                                    matched_kw = kw
                                    part_consumed.append(target_phrase)
                                    break
                    elif idx == N - 1:
                        cand_words = candidate_clean.split()
                        if cand_words:
                            kw_word_count = len(kw_lower.split())
                            if len(cand_words) >= kw_word_count:
                                target_phrase = " ".join(cand_words[:kw_word_count])
                                if NORMALIZE_VAL_RE.sub("", target_phrase) == kw_norm:
                                    matched_kw = kw
                                    part_consumed.append(target_phrase)
                                    break
                    else:
                        if NORMALIZE_VAL_RE.sub("", candidate_clean) == kw_norm:
                            matched_kw = kw
                            part_consumed.append(candidate_clean)
                            break
                            
                if matched_kw:
                    display = matched_kw.upper() if not is_qual else matched_kw.title()
                    if display.lower() in ("b.tech", "btech"):
                        display = "B.Tech"
                    elif display.lower() in ("b.e.", "be", "b.e"):
                        display = "B.E."
                    elif display.lower() in ("m.tech", "mtech"):
                        display = "M.Tech"
                    elif display.lower() in ("m.e.", "me", "m.e"):
                        display = "M.E."
                    group.append(display)
                    
            if group:
                all_groups.append(group)
                all_consumed.extend(part_consumed)
                
        has_multi_item_group = any(len(g) > 1 for g in all_groups)
        if all_groups and has_multi_item_group:
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
        standard_degree_terms = {
            "b.tech", "m.tech", "b.e.", "mba", "diploma", "ph.d", "b.arch", "degree", "master", "doctorate",
            "btech", "mtech", "be", "barch", "phd", "bachelor", "bachelors", "masters", "doctor",
            "ssc", "hsc", "aissce", "cbse", "icse", "schooling", "matriculation",
            "ba", "ma", "bsc", "msc", "bcom", "mcom", "llb", "llm", "mplan", "mms", "bba", "bca", "mbl",
            "b.a.", "m.a.", "b.sc.", "m.sc.", "b.com.", "m.com.", "l.l.b.", "l.l.m.", "b.ca.", "m.b.l.",
            "dce", "dme", "deee", "dee", "dct", "lce", "dtech",
            "pgp", "pgd", "pgdm", "pgdcm", "pgdbm", "pgdhrm", "pgp-acm", "pgpacm", "pgppem", "pgp-pem", 
            "pgpifdm", "pgp-ifdm", "pgpqscm", "pgp-qscm", "pgppm", "pgp-pm", "pgemp", "pgdmp", "pgdom", 
            "pgdtqm", "pgdpm", "epgp", "epgp-qsc", "epgpqsc", "epgp-eicm", "epgpeicm", "pgdacm", "pgd-acm",
            "iti", "ceng", "ieng", "amie", "amice", "high school", "std", "exam", "certificate", "school",
            "de", "me", "m.e."
        }
        query_has_degree_term = any(
            re.search(rf"\b{re.escape(term)}\b", q_clean)
            for term in standard_degree_terms
        )
        for qual in sorted(QUALIFICATIONS, key=lambda q: (len(get_query_tokens(q)), len(q)), reverse=True):
            qual_lower = qual.lower()
            is_discipline_only = not any(term in qual_lower for term in standard_degree_terms)
            if is_discipline_only:
                if not qualification_context and not query_has_degree_term:
                    continue
            matched, updated = match_and_consume_keyword(qual, query_tokens)
            if matched:
                qualification_matches.append(qual.title())
                query_tokens = updated
        if qualification_matches:
            from backend.app.structured_search import CANONICAL_QUAL_MAP
            seen_canonical = set()
            deduped_matches = []
            for q in qualification_matches:
                q_norm = normalize_val(q)
                q_canon = CANONICAL_QUAL_MAP.get(q_norm, q_norm)
                if q_canon not in seen_canonical:
                    seen_canonical.add(q_canon)
                    deduped_matches.append(q)
            qualification_matches = deduped_matches

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
            
    # Proficiency filters block is moved to run after skill requirements extraction
        
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

    skill_matches = []
    sub_skill_matches = []
    skill_requirements = []
    
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

    # 2. Extract skills using the alias map and locate proficiencies
    alias_skipped_indices = set()
    matched_alias_skills = []
    
    # Sort aliases by number of tokens desc, then length desc
    sorted_aliases = sorted(SKILL_ALIASES_MAP.keys(), key=lambda a: (len(get_query_tokens(a)), len(a)), reverse=True)
    
    # Pass 1: Match exact aliases first to prevent stemmed versions (like "finishing") from stealing exact matches (like "finishes")
    for alias in sorted_aliases:
        indices = match_skill_in_tokens(alias, query_tokens, alias_skipped_indices, exact_only=True)
        if indices:
            matched_alias_skills.append({
                "alias": alias,
                "original_names": SKILL_ALIASES_MAP[alias],
                "indices": indices
            })
            alias_skipped_indices.update(indices)
            
    # Pass 2: Match stemmed variations for the remaining query tokens
    for alias in sorted_aliases:
        indices = match_skill_in_tokens(alias, query_tokens, alias_skipped_indices, exact_only=False)
        if indices:
            matched_alias_skills.append({
                "alias": alias,
                "original_names": SKILL_ALIASES_MAP[alias],
                "indices": indices
            })
            alias_skipped_indices.update(indices)
            
    # Compile all skill indices
    all_skill_indices = {idx for s in matched_alias_skills for idx in s["indices"]}
    
    # Track tokens to remove from query_tokens
    tokens_to_remove = []
    
    for ms in matched_alias_skills:
        # Extract proficiencies from neighborhood
        proficiencies, operator = extract_proficiencies_for_skill(ms["indices"], query_tokens, all_skill_indices)
        
        orig_names = list(ms["original_names"])
        
        # Add ONE skill_requirements entry per alias match,
        # with a `skills` list so multiple expansions are OR'd (not AND'd)
        skill_requirements.append({
            "skills": orig_names,        # OR-group: employee needs ANY of these
            "proficiency": proficiencies if proficiencies else None,
            "operator": operator          # operator between proficiency values
        })
        
        # For backward compatibility, populate skill_matches or sub_skill_matches
        for orig in orig_names:
            orig_lower = orig.lower()
            if orig_lower in SUB_SKILLS:
                if orig not in sub_skill_matches:
                    sub_skill_matches.append(orig)
            else:
                if orig not in skill_matches:
                    skill_matches.append(orig)
                    
        # Mark skill tokens for removal
        for idx in ms["indices"]:
            tokens_to_remove.append(query_tokens[idx])
            
        # Mark proficiency tokens in the neighborhood for removal
        start_idx = ms["indices"][0]
        end_idx = ms["indices"][-1]
        
        # Preceding window
        pre_start = max(0, start_idx - 5)
        for idx in range(start_idx - 1, pre_start - 1, -1):
            if idx in all_skill_indices:
                pre_start = idx + 1
                break
        for idx in range(pre_start, start_idx):
            tok = query_tokens[idx]
            if any(p_word in tok.lower() for p_word in ["basic", "functional", "intermediate", "proficient", "expert", "role", "model"]):
                tokens_to_remove.append(tok)
                
        # Following window
        post_end = min(len(query_tokens), end_idx + 4)
        for idx in range(end_idx + 1, post_end):
            if idx in all_skill_indices:
                post_end = idx
                break
        for idx in range(end_idx + 1, post_end):
            tok = query_tokens[idx]
            if any(p_word in tok.lower() for p_word in ["basic", "functional", "intermediate", "proficient", "expert", "role", "model"]):
                tokens_to_remove.append(tok)
                
    # Now remove all marked tokens from query_tokens safely
    for t in tokens_to_remove:
        if t in query_tokens:
            query_tokens.remove(t)

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
        regex_skills = []
        for s in skill_parts:
            s_clean = s.strip()
            if not s_clean:
                continue
            words = s_clean.split()
            cleaned_words = [w for w in words if w.lower() not in SKILL_STOP_WORDS]
            if cleaned_words:
                cleaned_phrase = " ".join(cleaned_words)
                regex_skills.append(cleaned_phrase.title())
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
                        
                    # Find indices of rs in query_tokens
                    rs_indices = match_skill_in_tokens(rs, query_tokens, set())
                    if rs_indices:
                        proficiencies, operator = extract_proficiencies_for_skill(rs_indices, query_tokens, set(rs_indices))
                        skill_requirements.append({
                            "skill": rs,
                            "proficiency": proficiencies if proficiencies else None,
                            "operator": operator
                        })

    if skill_matches:
        result["skill"] = skill_matches[0] if len(skill_matches) == 1 else skill_matches
        result["skill_operator"] = detect_operator(q_clean, skill_matches, "and")
        
    if sub_skill_matches:
        result["sub_skill"] = sub_skill_matches[0] if len(sub_skill_matches) == 1 else sub_skill_matches
        result["sub_skill_operator"] = detect_operator(q_clean, sub_skill_matches, "or")

    if skill_requirements:
        result["skill_requirements"] = skill_requirements
        
    # 8. Proficiency filters (extracted from query_tokens only if not consumed by skills)
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
        
    # 10. Intent determination
    is_refinement = any(re.match(rf"^{trigger}", q_clean) for trigger in REFINEMENT_TRIGGERS)
    
    has_structured = any([
        result["designation"],
        result["department"],
        result["exclude_department"],
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
    
    if result["intent"] == IntentType.REFINEMENT:
        pass
    elif is_refinement:
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
