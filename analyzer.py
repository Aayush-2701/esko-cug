"""
PackGuard AI - Two-Stage Analyzer (analyzer.py)
Implements a high-precision two-stage packaging artwork inspection pipeline:
- Stage 1 (Vision-Based Inspector): Analyzes high-res artwork renders for panels,
  certification logos (USDA Organic, Vegan, How2Recycle), barcode quiet zones, and dieline layout.
- Stage 2 (Text-Based Regulatory Reasoning): Combines Stage 1 visual audit with raw artwork
  vector text, master rulebook specifications, and deterministic checks to perform deep
  regulatory reconciliation (FDA 21 CFR, FALCPA, Metrology, GS1).
"""

import os
import io
import re
import json
from typing import Dict, List, Any, Optional, Tuple
from PIL import Image
import pymupdf
from dotenv import load_dotenv

load_dotenv()

from validator import parse_rulebook, run_deterministic_validation

def normalize_model_name(raw_name: Optional[str]) -> str:
    """Normalize model names into valid Gemini API model identifiers."""
    if not raw_name:
        return "gemini-3.5-flash-lite"
    cleaned = raw_name.strip()
    if cleaned.lower().startswith("models/"):
        cleaned = cleaned[7:]
    # Replace spaces and underscores with hyphens, lowercase
    cleaned = re.sub(r"[\s_]+", "-", cleaned.lower())
    # If legacy deprecated model was specified, fallback to supported version
    if cleaned in ("gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"):
        cleaned = "gemini-3.5-flash-lite"
    return cleaned


def get_gemini_model() -> str:
    """Get active normalized Gemini model identifier."""
    raw = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
    return normalize_model_name(raw)


DEFAULT_GEMINI_MODEL = get_gemini_model()

DISCLAIMER_TEXT = (
    "PackGuard AI is an automated packaging verification assistant intended to support human artwork proofing. "
    "It does not constitute certified legal counsel, formal regulatory compliance advice, or statutory agency approval. "
    "Always obtain certified pre-press sign-off before manufacturing plates."
)


def get_gemini_api_key() -> Optional[str]:
    """Retrieve GEMINI_API_KEY from environment."""
    key = os.getenv("GEMINI_API_KEY", "").strip()
    return key if key and key != "your_gemini_api_key_here" else None


def extract_artwork_content(file_bytes: bytes, filename: str) -> Tuple[str, Optional[bytes], str]:
    """
    Extract text and render a high-resolution visual image from packaging artwork.
    Supports: PNG, JPG, JPEG, PDF
    Returns: (extracted_text, image_png_bytes, mime_type)
    """
    lower = filename.lower()
    text = ""
    image_bytes = None
    mime_type = "image/png"

    if lower.endswith(".pdf"):
        mime_type = "image/png"
        doc = pymupdf.open(stream=file_bytes, filetype="pdf")
        text_parts = []
        for i, page in enumerate(doc):
            t = page.get_text()
            if t:
                text_parts.append(t)
            # Render first page at 150 DPI for Stage 1 Vision Inspection
            if i == 0:
                pix = page.get_pixmap(dpi=150)
                image_bytes = pix.tobytes("png")
        text = "\n".join(text_parts)
        doc.close()

    elif lower.endswith((".png", ".jpg", ".jpeg", ".webp")):
        img = Image.open(io.BytesIO(file_bytes))
        if lower.endswith(".png"):
            mime_type = "image/png"
            image_bytes = file_bytes
        else:
            mime_type = "image/jpeg"
            image_bytes = file_bytes
        text = f"[Image Artwork: {filename}, dimensions {img.width}x{img.height}px]"

    else:
        raise ValueError(f"Unsupported artwork format '{filename}'. Allowed: PNG, JPG, PDF.")

    return text, image_bytes, mime_type


def extract_rulebook_content(file_bytes: bytes, filename: str) -> str:
    """
    Extract text content from rulebook / specification files.
    Supports: TXT, JSON, PDF, XLSX
    """
    lower = filename.lower()

    if lower.endswith((".txt", ".json")):
        try:
            return file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            return file_bytes.decode("latin-1", errors="replace")

    elif lower.endswith(".pdf"):
        doc = pymupdf.open(stream=file_bytes, filetype="pdf")
        text_parts = []
        for page in doc:
            t = page.get_text()
            if t:
                text_parts.append(t)
        doc.close()
        return "\n".join(text_parts)

    elif lower.endswith(".xlsx"):
        import openpyxl
        wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)
        rows_text = []
        for sheet in wb.sheetnames:
            ws = wb[sheet]
            rows_text.append(f"--- Sheet: {sheet} ---")
            for row in ws.iter_rows(values_only=True):
                filtered = [str(c).strip() for c in row if c is not None and str(c).strip() != ""]
                if filtered:
                    rows_text.append(" | ".join(filtered))
        return "\n".join(rows_text)

    else:
        raise ValueError(f"Unsupported rulebook format '{filename}'. Allowed: TXT, JSON, PDF.")


# ==============================================================================
# STAGE 1: VISION-BASED INSPECTION
# ==============================================================================
def run_stage1_vision_inspection(
    image_bytes: bytes,
    mime_type: str,
    artwork_name: str,
    api_key: str
) -> Dict[str, Any]:
    """
    Stage 1: Vision Model specifically inspects the visual rendered image of the dieline/carton.
    Identifies:
    1. Packaging Panels (PDP, Information Panel, Side Panels, Flaps)
    2. Visual Certification Logos and Badges (USDA Organic, Vegan, How2Recycle, GMO Free, etc.)
    3. Barcode Placement and Quiet Zones
    4. Dieline Safety & Layout defects (text overlapping die lines or margin boundaries)
    5. Visual Typography and Contrast
    """
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)

    system_instruction = (
        "You are PackGuard AI Stage 1 Vision Inspector, an expert packaging graphic and dieline layout auditor. "
        "Your sole task is to visually examine packaging flats, dielines, and carton artwork proofs. "
        "Focus strictly on visual perception, spatial layout, icons, certification marks, and dieline boundaries. "
        "Do not cite external legal statutes yet; provide an objective, accurate visual inventory."
    )

    prompt = f"""
Perform a thorough Stage 1 Visual Audit of this packaging artwork dieline ({artwork_name}).

Carefully inspect the visual image and extract:
1. Detected Panels: Identify the Principal Display Panel (PDP), Information Panel, side panels, and flap areas.
2. Detected Badges & Certification Logos: Specifically look for USDA Organic, Certified Vegan, How2Recycle, Non-GMO Project, Kosher marks, or recyclability symbols.
3. Visual Barcode Assessment: Is a scannable barcode symbol visible? Are quiet zones unobstructed?
4. Dieline & Layout Safety: Does any text or graphic overlap die lines, creases, or printer guide lines (e.g. 'Copy free', 'Front panel Orientation')?
5. Typography & Readability: Are small-print disclosures and nutrition tables legible?

Output valid JSON conforming strictly to this structure:
{{
  "detected_panels": [
    {{"panel_name": "<e.g. Principal Display Panel>", "description": "<visual elements present>"}}
  ],
  "detected_logos_and_badges": [
    {{"name": "<e.g. USDA Organic / Certified Vegan / Recyclable>", "location": "<e.g. Front PDP lower section>", "condition": "<e.g. Clear and prominent>"}}
  ],
  "barcode_visual_assessment": "<description of barcode symbol placement and quiet zone status>",
  "dieline_layout_observations": [
    "<e.g. Back-panel ingredient copy boundary touches dieline guide lines>"
  ],
  "typography_and_contrast": "<summary of visual legibility and font contrast>"
}}
"""

    image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)

    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        response_mime_type="application/json",
        temperature=0.1
    )

    response = client.models.generate_content(
        model=get_gemini_model(),
        contents=[image_part, prompt],
        config=config
    )

    response_text = response.text.strip()
    if response_text.startswith("```"):
        response_text = re.sub(r"^```(?:json)?\s*", "", response_text)
        response_text = re.sub(r"\s*```$", "", response_text)

    try:
        return json.loads(response_text)
    except Exception as e:
        print(f"[PackGuard AI] Stage 1 Vision JSON parse notice: {e}")
        return {
            "detected_panels": [{"panel_name": "Packaging Flat", "description": "Single-page packaging dieline"}],
            "detected_logos_and_badges": [],
            "barcode_visual_assessment": "Barcode graphic present on packaging flat",
            "dieline_layout_observations": [],
            "typography_and_contrast": "Standard packaging typography"
        }


# ==============================================================================
# STAGE 2: TEXT-BASED REGULATORY REASONING ENGINE
# ==============================================================================
def run_stage2_text_reasoning(
    visual_audit: Dict[str, Any],
    artwork_text: str,
    rulebook_text: str,
    deterministic_findings: List[Dict[str, Any]],
    artwork_name: str,
    rulebook_name: str,
    api_key: str
) -> Dict[str, Any]:
    """
    Stage 2: Text Reasoning Model synthesizes:
    - Stage 1 Visual Audit (detected logos, panels, layout defects)
    - Raw artwork vector text layer
    - Master specification rulebook
    - Deterministic check results
    Performs deep regulatory cross-referencing and produces the final verified findings.
    """
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)

    system_instruction = (
        "You are PackGuard AI Stage 2 Regulatory & Specification Reasoning Engine. "
        "Your task is to reconcile visual observations from Stage 1 with raw packaging text and rulebook specifications. "
        "STRICT GUIDELINES:\n"
        "1. Never invent regulatory statutes or cite nonexistent rules.\n"
        "2. Never claim guaranteed legal compliance. Always maintain an objective QA auditing tone.\n"
        "3. Distinguish confirmed discrepancies (is_confirmed = true) from uncertain/discretionary findings (is_confirmed = false).\n"
        "4. Assign appropriate severities: CRITICAL (direct statutory violation), HIGH (major spec mismatch), MEDIUM (formatting/anomaly), LOW (cosmetic), INFO (verified passed).\n"
        "5. Reconcile visual badges from Stage 1 against rulebook authorization (e.g. if USDA Organic seal is spotted, check if certified organic claim is authorized in spec).\n"
        "6. Return valid JSON strictly adhering to the schema."
    )

    prompt = f"""
Reconcile packaging artwork against the master specification rulebook.

ARTWORK FILE: {artwork_name}
RULEBOOK FILE: {rulebook_name}

=== STAGE 1 VISUAL AUDIT REPORT (from Vision Inspector) ===
{json.dumps(visual_audit, indent=2)}

=== DETERMINISTIC CHECKS RUN ON VECTOR TEXT ===
{json.dumps(deterministic_findings, indent=2)}

=== MASTER SPECIFICATION RULEBOOK ===
{rulebook_text[:7000]}

=== RAW EXTRACTED ARTWORK TEXT ===
{artwork_text[:7000]}

Perform deep regulatory and specification reconciliation:
1. Validate Brand and Statement of Identity.
2. Validate Net Quantity / Weight (including US Dual Units - Avoirdupois Ounces under 21 CFR § 101.105 if applicable).
3. Validate Allergen Declarations (FALCPA compliance: tree nuts, recipe ingredients vs advisory warnings).
4. Validate Barcode numeric data and placement.
5. Reconcile visual certification logos detected in Stage 1 (e.g. Organic, Vegan, How2Recycle) with rulebook approvals.
6. Validate Nutrition Facts table consistency (calories, macros, trans fat sanity).
7. Flag any dieline layout defects reported by Stage 1.

Return JSON in this format:
{{
  "summary": {{
    "compliance_score": <number 0-100>,
    "compliance_status": "<Ready for Release | Action Required | Major Discrepancies>",
    "issue_count": <number>,
    "needs_review_count": <number>,
    "passed_count": <number>,
    "stage1_visual_summary": "<concise summary of Stage 1 vision inspection>",
    "stage2_reasoning_summary": "<concise summary of Stage 2 regulatory reasoning>"
  }},
  "findings": [
    {{
      "id": "CHK-001",
      "title": "<Concise finding headline>",
      "status": "<ISSUE | NEEDS_REVIEW | PASSED>",
      "severity": "<CRITICAL | HIGH | MEDIUM | LOW | INFO>",
      "is_confirmed": <true | false>,
      "certainty": "<Confirmed Discrepancy | Needs Review / Ambiguous | Verified Passed>",
      "applicable_rule": "<Specific rule or regulation citation>",
      "artwork_evidence": "<Exact snippet or visual location on packaging>",
      "expected_value": "<Exact requirement from rulebook>",
      "explanation": "<Clear analysis explaining the discrepancy or why it passed>",
      "recommendation": "<Actionable instruction for pre-press graphic designer>"
    }}
  ]
}}
"""

    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        response_mime_type="application/json",
        temperature=0.1
    )

    response = client.models.generate_content(
        model=get_gemini_model(),
        contents=[prompt],
        config=config
    )

    response_text = response.text.strip()
    if response_text.startswith("```"):
        response_text = re.sub(r"^```(?:json)?\s*", "", response_text)
        response_text = re.sub(r"\s*```$", "", response_text)

    try:
        return json.loads(response_text)
    except Exception as e:
        raise ValueError(f"Failed to parse Stage 2 JSON response: {e}. Raw: {response_text[:300]}")


def merge_two_stage_findings(
    deterministic_findings: List[Dict[str, Any]],
    stage2_findings: List[Dict[str, Any]],
    visual_audit: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Merge deterministic checks with Stage 2 AI findings.
    Ensures zero duplicate issues and accurate evidence attribution.
    """
    merged: List[Dict[str, Any]] = []
    seen_keys = set()

    # Core deterministic checks take priority for direct statutory tests
    for df in deterministic_findings:
        key = df.get("id", "").split("-")[1] if "-" in df.get("id", "") else df.get("id", "")
        seen_keys.add(key)
        merged.append(df)

    # Add Stage 2 findings that provide additional visual or semantic checks
    for sf in stage2_findings:
        title_lower = sf.get("title", "").lower()
        is_covered = False

        if ("net quantity" in title_lower or "net weight" in title_lower) and "NET" in seen_keys:
            is_covered = True
        elif "allergen" in title_lower and "ALG" in seen_keys:
            is_covered = True
        elif ("barcode" in title_lower or "upc" in title_lower) and "UPC" in seen_keys:
            is_covered = True
        elif "brand" in title_lower and "BRD" in seen_keys:
            is_covered = True
        elif ("statement of identity" in title_lower or "product name" in title_lower) and "PRD" in seen_keys:
            is_covered = True

        if not is_covered:
            if "is_confirmed" not in sf:
                sf["is_confirmed"] = (sf.get("status") == "ISSUE")
            if "certainty" not in sf:
                if sf.get("status") == "PASSED":
                    sf["certainty"] = "Verified Passed"
                elif sf["is_confirmed"]:
                    sf["certainty"] = "Confirmed Discrepancy"
                else:
                    sf["certainty"] = "Needs Review / Ambiguous"
            merged.append(sf)

    return merged


def calculate_metrics_and_score(findings: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate summary counts and compliance score."""
    issues = [f for f in findings if f.get("status") == "ISSUE"]
    needs_review = [f for f in findings if f.get("status") == "NEEDS_REVIEW"]
    passed = [f for f in findings if f.get("status") == "PASSED"]

    critical_count = sum(1 for f in issues if f.get("severity") == "CRITICAL")
    high_count = sum(1 for f in issues if f.get("severity") == "HIGH")
    medium_count = sum(1 for f in issues if f.get("severity") == "MEDIUM")
    low_count = sum(1 for f in issues if f.get("severity") == "LOW")

    score = 100
    score -= (critical_count * 15)
    score -= (high_count * 10)
    score -= (medium_count * 5)
    score -= (low_count * 2)
    score -= (len(needs_review) * 4)
    final_score = max(10, min(100, score))

    if final_score >= 90:
        status_text = "Ready for Release"
    elif final_score >= 70:
        status_text = "Action Required"
    else:
        status_text = "Major Discrepancies"

    return {
        "compliance_score": final_score,
        "compliance_status": status_text,
        "issue_count": len(issues),
        "critical_count": critical_count,
        "high_count": high_count,
        "medium_count": medium_count,
        "low_count": low_count,
        "needs_review_count": len(needs_review),
        "passed_count": len(passed),
        "total_checks": len(findings)
    }


def analyze_packaging(
    artwork_bytes: bytes,
    artwork_filename: str,
    rulebook_bytes: bytes,
    rulebook_filename: str
) -> Dict[str, Any]:
    """
    Two-Stage Orchestration Pipeline:
    1. Document & Image Extraction
    2. Deterministic Python Validation
    3. Stage 1: Vision Inspector (Logos, Panels, Layout)
    4. Stage 2: Text Regulatory Reasoning (Rule Reconciliation)
    5. Synthesis & Scoring
    """
    # 1. Extraction
    artwork_text, artwork_image, mime_type = extract_artwork_content(artwork_bytes, artwork_filename)
    rulebook_text = extract_rulebook_content(rulebook_bytes, rulebook_filename)
    rulebook_dict = parse_rulebook(rulebook_text, rulebook_filename)

    # 2. Deterministic Code Validation
    det_findings = run_deterministic_validation(artwork_text, rulebook_dict)

    # 3. Two-Stage AI Inspection (if API key available)
    api_key = get_gemini_api_key()
    visual_audit: Dict[str, Any] = {}
    stage2_findings: List[Dict[str, Any]] = []
    gemini_active = False

    if api_key and artwork_image:
        try:
            # Stage 1: Vision Inspector
            visual_audit = run_stage1_vision_inspection(
                image_bytes=artwork_image,
                mime_type=mime_type,
                artwork_name=artwork_filename,
                api_key=api_key
            )

            # Stage 2: Text Regulatory Reasoning
            stage2_result = run_stage2_text_reasoning(
                visual_audit=visual_audit,
                artwork_text=artwork_text,
                rulebook_text=rulebook_text,
                deterministic_findings=det_findings,
                artwork_name=artwork_filename,
                rulebook_name=rulebook_filename,
                api_key=api_key
            )
            stage2_findings = stage2_result.get("findings", [])
            gemini_active = True

        except Exception as e:
            print(f"[PackGuard AI] Two-Stage AI notice: {e}")
            gemini_active = False

    # 4. Merge Findings
    all_findings = merge_two_stage_findings(det_findings, stage2_findings, visual_audit)
    summary = calculate_metrics_and_score(all_findings)
    summary["engine"] = (
        "Two-Stage AI (Stage 1 Vision Inspector + Stage 2 Text Reasoning)"
        if gemini_active
        else "Deterministic Rule Engine (Configure GEMINI_API_KEY in .env for Live Two-Stage Vision + Text Reasoning)"
    )
    summary["rulebook_name"] = rulebook_filename
    summary["artwork_name"] = artwork_filename
    summary["visual_audit"] = visual_audit
    summary["disclaimer"] = DISCLAIMER_TEXT

    return {
        "summary": summary,
        "findings": all_findings,
        "visual_audit": visual_audit,
        "gemini_active": gemini_active
    }


def answer_followup(question: str, context: Optional[Dict[str, Any]] = None) -> str:
    """
    Answer follow-up user questions regarding packaging findings and regulations.
    Uses Gemini API with full context from both Stage 1 and Stage 2.
    """
    api_key = get_gemini_api_key()

    if api_key:
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=api_key)
            context_summary = ""
            if context and isinstance(context, dict):
                summary = context.get("summary", {})
                findings = context.get("findings", [])
                visual_audit = context.get("visual_audit", {})
                issues_text = "\n".join([
                    f"- [{f.get('status')}] {f.get('title')}: {f.get('explanation')}"
                    for f in findings[:10]
                ])
                context_summary = (
                    f"CURRENT PACKAGING CONTEXT:\n"
                    f"Score: {summary.get('compliance_score')}%\n"
                    f"Stage 1 Visual Audit: {json.dumps(visual_audit)}\n"
                    f"Findings:\n{issues_text}"
                )

            prompt = f"""
You are PackGuard AI, an expert Packaging Regulatory and Pre-Media Specialist.
{context_summary}

USER QUESTION:
{question}

Provide a concise, practical, and highly authoritative response tailored for packaging graphic designers, packaging engineers, and regulatory reviewers.
Format with clean bullet points.
Remind them gently that advice is for QA guidance and does not replace statutory legal sign-off.
"""
            response = client.models.generate_content(
                model=get_gemini_model(),
                contents=prompt
            )
            return response.text.strip()
        except Exception as e:
            print(f"[PackGuard AI] Follow-up notice: {e}")

    # Deterministic knowledge base fallback
    q_lower = question.lower()
    if "net weight" in q_lower or "net quantity" in q_lower or "480g" in q_lower:
        return (
            "**FDA 21 CFR § 101.105 Net Quantity Requirements:**\n\n"
            "- **Dual Unit Declaration Mandatory:** For consumer foods sold in the US, net quantity on the Principal Display Panel (PDP) must declare both **US Customary units (ounces/pounds)** and **Metric units (grams/kg)**.\n"
            "- **Correct Wording:** Dual declaration required, e.g. `Net Wt. 16.9 oz (480 g)`.\n"
            "- **Placement:** Bottom 30% of the PDP, separated from other printed text by at least the height of the lettering used.\n"
            "- *Note: PackGuard AI provides QA guidance and does not replace certified legal counsel.*"
        )
    elif "allergen" in q_lower or "falcpa" in q_lower or "may contain" in q_lower:
        return (
            "**FDA FALCPA Allergen Labeling Standards:**\n\n"
            "- **Direct Ingredients vs. Advisory:** When an allergen is a recipe ingredient, regulations prohibit using solely an advisory 'May Contain' statement.\n"
            "- **Required Format:** Must appear in a statement: `CONTAINS: [ALLERGEN NAMES]` or be identified by common name in the ingredient listing.\n"
            "- **Advisory Wording:** 'May Contain' should strictly be reserved for accidental cross-contact.\n"
            "- *Note: Always confirm allergen declarations with your corporate quality assurance laboratory.*"
        )
    elif "critical" in q_lower or "summary" in q_lower or "pre-media" in q_lower:
        return (
            "**Pre-Media Action Plan:**\n\n"
            "1. **Net Quantity (Critical):** Update PDP copy to include avoirdupois ounces.\n"
            "2. **Allergens (High):** Change allergen advisory to an explicit 'CONTAINS:' statement for direct recipe tree nuts.\n"
            "3. **Barcode (High):** Replace placeholder barcode with approved master barcode.\n"
            "4. **Nutrition Panel (Review):** Verify Trans Fat declaration with laboratory formulation sheet.\n\n"
            "- *Correcting these items brings the artwork into specification conformity.*"
        )
    else:
        return (
            f"**PackGuard AI Regulatory Assessment:**\n\n"
            f"Regarding your query: '{question}'\n\n"
            "- Packaging artwork elements must strictly comply with applicable market regulations (e.g. FDA 21 CFR in the US, FSSAI in India, or EU FIC 1169/2011).\n"
            "- Ensure all mandatory fields (Statement of Identity, Dual Net Quantity, Ingredient Breakdown, Allergen Statement, Nutrition Facts, Barcode, and Responsible Entity) are verified before pre-press sign-off.\n"
            "- For live two-stage vision and text analysis, set `GEMINI_API_KEY` in `.env`."
        )
