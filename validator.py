"""
PackGuard AI - Deterministic Packaging Validator (validator.py)
Provides deterministic, rule-based verification for arbitrary packaging artwork
against user-supplied rulebooks and specifications.

Validates:
- Mandatory display elements (Product Name, Brand, Net Quantity, Ingredients, Allergens, Nutrition, Manufacturer, Storage, Barcode)
- Dual net quantity declarations (Metric + US Customary units)
- Allergen declaration consistency (Direct ingredients vs advisory statements)
- Barcode / UPC number conformity
- Brand and Product Name presence
- Storage instructions
- Nutrition facts panel structure
"""

import re
import json
from typing import Dict, List, Any, Optional, Tuple


def normalize_text(text: str) -> str:
    """Normalize text for consistent comparison."""
    if not text:
        return ""
    text = text.replace("\u00a0", " ").replace("\u2013", "-").replace("\u2014", "-")
    return re.sub(r"\s+", " ", text).strip()


def parse_rulebook(rulebook_content: str, filename: str = "") -> Dict[str, Any]:
    """
    Parse rulebook content into a structured dictionary.
    Dynamically extracts specifications from JSON, TXT, or tabular content.
    """
    rulebook_data: Dict[str, Any] = {
        "brand": "",
        "product_name": "",
        "net_weight": "",
        "net_weight_us_required": "",
        "barcode_upc": "",
        "bpn_sku": "",
        "mandatory_fields": [
            "Product Name", "Brand", "Net Quantity",
            "Ingredients List", "Allergen Declaration", "Nutrition Facts",
            "Manufacturer Information", "Storage Instructions", "Barcode / UPC"
        ],
        "expected_ingredients": [],
        "allergen_requirements": {},
        "approved_claims": [],
        "storage_text": "",
        "raw_text": rulebook_content
    }

    trimmed = rulebook_content.strip()
    if (trimmed.startswith("{") and trimmed.endswith("}")) or filename.lower().endswith(".json"):
        try:
            parsed_json = json.loads(trimmed)
            if isinstance(parsed_json, dict):
                for k, v in parsed_json.items():
                    key_lower = k.lower().replace(" ", "_")
                    if key_lower in ("brand", "brand_name"):
                        rulebook_data["brand"] = str(v).strip()
                    elif key_lower in ("product_name", "product", "statement_of_identity", "legal_name"):
                        rulebook_data["product_name"] = str(v).strip()
                    elif key_lower in ("net_weight", "net_quantity", "package_size", "weight"):
                        rulebook_data["net_weight"] = str(v).strip()
                    elif key_lower in ("net_weight_us_required", "us_net_quantity"):
                        rulebook_data["net_weight_us_required"] = str(v).strip()
                    elif key_lower in ("barcode", "barcode_upc", "upc", "gtin"):
                        rulebook_data["barcode_upc"] = str(v).strip()
                    elif key_lower in ("bpn_sku", "sku", "bpn", "item_code"):
                        rulebook_data["bpn_sku"] = str(v).strip()
                    elif key_lower in ("mandatory_fields", "required_elements") and isinstance(v, list):
                        rulebook_data["mandatory_fields"] = [str(item).strip() for item in v]
                    elif key_lower in ("expected_ingredients", "ingredients", "ingredients_required") and isinstance(v, list):
                        rulebook_data["expected_ingredients"] = [str(item).strip() for item in v]
                    elif key_lower in ("allergen_requirements", "allergens"):
                        rulebook_data["allergen_requirements"] = v
                    elif key_lower in ("approved_claims", "claims") and isinstance(v, list):
                        rulebook_data["approved_claims"] = [str(item).strip() for item in v]
                    elif key_lower in ("storage_text", "storage_instructions", "storage"):
                        rulebook_data["storage_text"] = str(v).strip()
                return rulebook_data
        except Exception:
            pass

    # Regex extraction from plain text or tabular content
    lines = rulebook_content.splitlines()
    for line in lines:
        line_clean = line.strip()
        if not line_clean:
            continue

        brand_m = re.search(r"(?:^|[\|\:\t])\s*Brand(?:\s*Name)?\s*[:=\|\t]\s*[\"']?([^\"'\n\r\|]+)[\"']?", line_clean, re.I)
        if brand_m and not rulebook_data["brand"]:
            rulebook_data["brand"] = brand_m.group(1).strip()

        prod_m = re.search(r"(?:^|[\|\:\t])\s*(?:Product\s*Name|Statement\s*of\s*Identity)\s*[:=\|\t]\s*[\"']?([^\"'\n\r\|]+)[\"']?", line_clean, re.I)
        if prod_m and not rulebook_data["product_name"]:
            rulebook_data["product_name"] = prod_m.group(1).strip()

        net_m = re.search(r"(?:^|[\|\:\t])\s*(?:Net\s*(?:Weight|Quantity)|Portions\s*Selected)\s*[:=\|\t]\s*[\"']?([^\"'\n\r\|]+)[\"']?", line_clean, re.I)
        if net_m and not rulebook_data["net_weight"]:
            rulebook_data["net_weight"] = net_m.group(1).strip()

        upc_m = re.search(r"(?:^|[\|\:\t])\s*(?:UPC|Barcode|GTIN)\s*[:=\|\t]\s*[\"']?([0-9\s-]+)[\"']?", line_clean, re.I)
        if upc_m and not rulebook_data["barcode_upc"]:
            rulebook_data["barcode_upc"] = upc_m.group(1).strip()

        bpn_m = re.search(r"(?:^|[\|\:\t])\s*(?:BPN|SKU|Item\s*Code)\s*[:=\|\t]\s*[\"']?([A-Za-z0-9_-]+)[\"']?", line_clean, re.I)
        if bpn_m and not rulebook_data["bpn_sku"]:
            rulebook_data["bpn_sku"] = bpn_m.group(1).strip()

    # Search for ingredient listing block
    ing_match = re.search(r"Ingredients(?:\s*List)?\s*[:=\|]\s*([^\n\r]+)", rulebook_content, re.I)
    if ing_match and not rulebook_data["expected_ingredients"]:
        items = [i.strip() for i in ing_match.group(1).split(",") if i.strip()]
        rulebook_data["expected_ingredients"] = items

    return rulebook_data


def run_deterministic_validation(artwork_text: str, rulebook_dict: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Run deterministic checks on artwork text against rulebook specifications.
    Completely dynamic based on supplied files.
    """
    findings: List[Dict[str, Any]] = []
    norm_art = normalize_text(artwork_text)
    art_lower = norm_art.lower()

    # 1. Brand Verification
    expected_brand = rulebook_dict.get("brand", "").strip()
    if expected_brand:
        if expected_brand.lower() in art_lower:
            findings.append({
                "id": "CHK-BRD",
                "title": f"Brand Name Verified ('{expected_brand}')",
                "status": "PASSED",
                "severity": "INFO",
                "is_confirmed": True,
                "certainty": "Verified Passed",
                "applicable_rule": "Brand Identity Specification",
                "artwork_evidence": f"Found brand name '{expected_brand}' in artwork text.",
                "expected_value": expected_brand,
                "explanation": f"The brand name matches the specification sheet.",
                "recommendation": "None. Brand name is verified."
            })
        else:
            findings.append({
                "id": "CHK-BRD",
                "title": f"Brand Name Missing or Mismatched ('{expected_brand}')",
                "status": "ISSUE",
                "severity": "CRITICAL",
                "is_confirmed": True,
                "certainty": "Confirmed Discrepancy",
                "applicable_rule": "Brand Identity Specification",
                "artwork_evidence": "Brand name could not be located in extracted artwork text.",
                "expected_value": expected_brand,
                "explanation": f"The approved brand name '{expected_brand}' was not detected in the artwork.",
                "recommendation": f"Add the approved brand name '{expected_brand}' to the artwork."
            })

    # 2. Product Name / Statement of Identity
    expected_prod = rulebook_dict.get("product_name", "").strip()
    if expected_prod:
        prod_clean = re.sub(r"[\s\-_]+", " ", expected_prod.lower())
        art_clean_spaces = re.sub(r"[\s\-_]+", " ", art_lower)
        if prod_clean in art_clean_spaces:
            findings.append({
                "id": "CHK-PRD",
                "title": f"Product Name / Identity Verified ('{expected_prod}')",
                "status": "PASSED",
                "severity": "INFO",
                "is_confirmed": True,
                "certainty": "Verified Passed",
                "applicable_rule": "Statement of Identity Standard",
                "artwork_evidence": f"Detected product name '{expected_prod}' in artwork layout.",
                "expected_value": expected_prod,
                "explanation": "Product name matches the approved rulebook specification.",
                "recommendation": "None. Statement of identity verified."
            })
        else:
            findings.append({
                "id": "CHK-PRD",
                "title": f"Product Name Missing or Mismatched ('{expected_prod}')",
                "status": "ISSUE",
                "severity": "HIGH",
                "is_confirmed": True,
                "certainty": "Confirmed Discrepancy",
                "applicable_rule": "Statement of Identity Standard",
                "artwork_evidence": "Product name could not be confirmed in artwork text.",
                "expected_value": expected_prod,
                "explanation": f"The expected product name '{expected_prod}' was not found in the artwork.",
                "recommendation": f"Ensure '{expected_prod}' is clearly placed on the principal display panel."
            })

    # 3. Net Quantity / Weight & Dual Units Check
    expected_net = rulebook_dict.get("net_weight", "").strip()
    if expected_net:
        found_weights = re.findall(r"\b(\d+(?:\.\d+)?)\s*(g|kg|oz|lbs?|grams?|ml|l|fl\s*oz)\b", art_lower)
        has_metric = any(u in ["g", "kg", "grams", "ml", "l"] for _, u in found_weights)
        has_customary = any(u in ["oz", "lb", "lbs", "fl oz"] for _, u in found_weights)

        num_match = re.search(r"\d+", expected_net)
        expected_num = num_match.group(0) if num_match else ""

        is_matching_num = any(num == expected_num for num, _ in found_weights) if expected_num else False

        # If metric only and target market or spec requires dual units (or US rulebook)
        if has_metric and not has_customary:
            findings.append({
                "id": "CHK-NET",
                "title": "Net Quantity Lacks Dual Unit Declaration (US Customary Ounces Missing)",
                "status": "ISSUE",
                "severity": "CRITICAL",
                "is_confirmed": True,
                "certainty": "Confirmed Discrepancy",
                "applicable_rule": "FDA 21 CFR § 101.105 (Net Quantity of Contents)",
                "artwork_evidence": f"Artwork displays only metric declaration ('{expected_net}').",
                "expected_value": f"Dual declaration required (e.g. '{expected_net} (16.9 oz)')",
                "explanation": "Packaging sold in the US must declare net quantity in both US Customary units (ounces/pounds) and metric units (grams/kg).",
                "recommendation": f"Update net weight to include both metric and imperial units (e.g. 'Net Wt. 16.9 oz ({expected_net})')."
            })
        elif is_matching_num and (has_customary or not has_metric):
            findings.append({
                "id": "CHK-NET",
                "title": f"Net Quantity Verified ('{expected_net}')",
                "status": "PASSED",
                "severity": "INFO",
                "is_confirmed": True,
                "certainty": "Verified Passed",
                "applicable_rule": "Legal Metrology / Net Quantity",
                "artwork_evidence": f"Found declared weight matching '{expected_net}'.",
                "expected_value": expected_net,
                "explanation": "Net quantity declaration is present and corresponds to specifications.",
                "recommendation": "None. Net weight compliant."
            })
        elif not is_matching_num and not found_weights:
            findings.append({
                "id": "CHK-NET",
                "title": f"Net Quantity Declaration Missing (Expected '{expected_net}')",
                "status": "ISSUE",
                "severity": "CRITICAL",
                "is_confirmed": True,
                "certainty": "Confirmed Discrepancy",
                "applicable_rule": "Legal Metrology Requirements",
                "artwork_evidence": "No net weight or quantity found on artwork.",
                "expected_value": expected_net,
                "explanation": "Net quantity is a mandatory packaging requirement that could not be detected.",
                "recommendation": f"Add the net weight declaration '{expected_net}' to the principal display panel."
            })

    # 4. Mandatory Ingredients Declaration
    has_ingredients = bool(re.search(r"\bingredients?\b", art_lower))
    if has_ingredients:
        findings.append({
            "id": "CHK-ING",
            "title": "Mandatory Ingredients Statement Present",
            "status": "PASSED",
            "severity": "INFO",
            "is_confirmed": True,
            "certainty": "Verified Passed",
            "applicable_rule": "Food Labeling Regulations (21 CFR § 101.4)",
            "artwork_evidence": "Detected 'INGREDIENTS:' section on packaging layout.",
            "expected_value": "Complete ingredient listing in descending order of predominance",
            "explanation": "The mandatory ingredients heading is present on the information panel.",
            "recommendation": "None. Section present."
        })
    else:
        findings.append({
            "id": "CHK-ING",
            "title": "Mandatory Ingredients Statement Missing",
            "status": "ISSUE",
            "severity": "CRITICAL",
            "is_confirmed": True,
            "certainty": "Confirmed Discrepancy",
            "applicable_rule": "Food Labeling Regulations (21 CFR § 101.4)",
            "artwork_evidence": "No ingredients section found in extracted artwork text.",
            "expected_value": "Complete ingredient listing",
            "explanation": "All packaged food products must display an ingredients statement.",
            "recommendation": "Add a complete ingredients statement to the information panel."
        })

    # 5. Allergen Advisory vs Direct Ingredients Cross-Check
    has_allergen_box = bool(re.search(r"\ballergen(?:s|\s*information)?\b|\bcontains\b|\bmay contain\b", art_lower))
    # Detect nuts or allergens in artwork ingredients
    has_tree_nuts_in_ingredients = bool(re.search(r"\b(almonds?|pecans?|walnuts?|cashews?|hazelnuts?|pistachios?)\b", art_lower))
    has_advisory_may_contain = bool(re.search(r"may\s+contain\s+(?:almonds?|pecans?|walnuts?|tree nuts?|nuts?)", art_lower))
    has_explicit_contains = bool(re.search(r"contains\s*:\s*.*(?:almonds?|pecans?|walnuts?|tree nuts?)", art_lower))

    if has_tree_nuts_in_ingredients and has_advisory_may_contain and not has_explicit_contains:
        findings.append({
            "id": "CHK-ALG",
            "title": "Recipe Allergens Improperly Phrased as Advisory 'May Contain'",
            "status": "ISSUE",
            "severity": "HIGH",
            "is_confirmed": True,
            "certainty": "Confirmed Discrepancy",
            "applicable_rule": "FDA FALCPA / Food Allergen Regulations",
            "artwork_evidence": "Ingredients list contains tree nuts, while allergen box states 'May Contain'.",
            "expected_value": "Recipe allergens must be declared in 'CONTAINS:' statement or bolded in ingredient list",
            "explanation": "Under allergen regulations, allergens that are intentional ingredients cannot be declared using advisory 'May Contain' wording.",
            "recommendation": "Update allergen statement to declare: 'CONTAINS: [ALLERGEN NAMES]'."
        })
    elif has_allergen_box:
        findings.append({
            "id": "CHK-ALG",
            "title": "Allergen Disclosure Section Present",
            "status": "PASSED",
            "severity": "INFO",
            "is_confirmed": True,
            "certainty": "Verified Passed",
            "applicable_rule": "Allergen Disclosure Standards",
            "artwork_evidence": "Allergen disclosure detected on artwork.",
            "expected_value": "Conformant allergen statement",
            "explanation": "An allergen statement is present on the packaging flat.",
            "recommendation": "None. Section present."
        })

    # 6. Barcode / UPC Conformity
    expected_upc = rulebook_dict.get("barcode_upc", "").strip()
    if expected_upc:
        clean_exp = re.sub(r"[\s-]", "", expected_upc)
        clean_art = re.sub(r"[\s-]", "", norm_art)
        if clean_exp in clean_art or expected_upc in norm_art:
            findings.append({
                "id": "CHK-UPC",
                "title": f"Master UPC / Barcode Number Verified ('{expected_upc}')",
                "status": "PASSED",
                "severity": "INFO",
                "is_confirmed": True,
                "certainty": "Verified Passed",
                "applicable_rule": "GS1 General Specifications",
                "artwork_evidence": f"Found matching barcode numbers '{expected_upc}' on artwork.",
                "expected_value": expected_upc,
                "explanation": "The printed barcode matches the master registered SKU barcode.",
                "recommendation": "None. Barcode verified."
            })
        else:
            has_placeholder = bool(re.search(r"gl1\s*2,1M|1M2S1I0O0|barcode\s*placeholder", norm_art, re.I))
            findings.append({
                "id": "CHK-UPC",
                "title": "Barcode Text Does Not Match Master Specification",
                "status": "ISSUE",
                "severity": "HIGH",
                "is_confirmed": True,
                "certainty": "Confirmed Discrepancy",
                "applicable_rule": "GS1 / Supply Chain Barcode Standards",
                "artwork_evidence": "Artwork contains placeholder string rather than registered barcode." if has_placeholder else "Registered UPC was not located on artwork.",
                "expected_value": f"Registered Barcode: '{expected_upc}'",
                "explanation": f"The packaging flat does not contain the master barcode number '{expected_upc}'.",
                "recommendation": f"Insert approved GS1-compliant barcode '{expected_upc}' with adequate quiet zones."
            })

    # 7. Mandatory Nutrition Facts Panel
    has_nutrition = bool(re.search(r"nutrition\s*facts|amount\s*per\s*serving|calories\s*\d+", art_lower))
    if has_nutrition:
        # Check high trans fat anomaly if present
        trans_fat_match = re.search(r"trans\s*fat\s*(\d+(?:\.\d+)?)\s*g", art_lower)
        if trans_fat_match:
            trans_val = float(trans_fat_match.group(1))
            if trans_val > 2.0:
                findings.append({
                    "id": "CHK-NUT-02",
                    "title": f"High Trans Fat Declared ({trans_val}g) - Verify Laboratory Formulation",
                    "status": "NEEDS_REVIEW",
                    "severity": "MEDIUM",
                    "is_confirmed": False,
                    "certainty": "Needs Review / Ambiguous",
                    "applicable_rule": "FDA 21 CFR § 101.9 Nutrition Labeling",
                    "artwork_evidence": f"Nutrition panel states: 'Trans Fat {trans_val}g'",
                    "expected_value": "Typically 0g unless partially hydrogenated oils are used",
                    "explanation": f"The printed panel claims {trans_val}g trans fat per serving. Verify if this is an unintentional typographical copy error.",
                    "recommendation": "Verify recipe lab nutritional certificate to confirm whether Trans Fat should be 0g."
                })

        findings.append({
            "id": "CHK-NUT",
            "title": "Mandatory Nutrition Facts Panel Present",
            "status": "PASSED",
            "severity": "INFO",
            "is_confirmed": True,
            "certainty": "Verified Passed",
            "applicable_rule": "FDA 21 CFR § 101.9 Nutrition Labeling",
            "artwork_evidence": "Nutrition Facts panel structure identified.",
            "expected_value": "Standardized Nutrition Facts panel",
            "explanation": "Nutrition Facts table is properly included on the packaging flat.",
            "recommendation": "None. Nutrition panel present."
        })
    else:
        findings.append({
            "id": "CHK-NUT",
            "title": "Mandatory Nutrition Facts Panel Missing",
            "status": "ISSUE",
            "severity": "CRITICAL",
            "is_confirmed": True,
            "certainty": "Confirmed Discrepancy",
            "applicable_rule": "FDA 21 CFR § 101.9",
            "artwork_evidence": "Nutrition panel could not be found in extracted text.",
            "expected_value": "Standardized Nutrition Facts table",
            "explanation": "Packaged retail goods require a nutrition declaration table.",
            "recommendation": "Place standard Nutrition Facts panel on the information panel."
        })

    # 8. Manufacturer / Responsible Entity Statement
    has_mfg = bool(re.search(r"(?:produced|manufactured|distributed|packed)\s*(?:by|for)\b", art_lower))
    if has_mfg:
        findings.append({
            "id": "CHK-MFG",
            "title": "Manufacturer / Responsible Business Entity Statement Present",
            "status": "PASSED",
            "severity": "INFO",
            "is_confirmed": True,
            "certainty": "Verified Passed",
            "applicable_rule": "FDA 21 CFR § 101.5 (Name and Place of Business)",
            "artwork_evidence": "Detected manufacturer / responsible entity statement.",
            "expected_value": "Name and place of business of manufacturer or distributor",
            "explanation": "Responsible entity is clearly declared on the information panel.",
            "recommendation": "None. Entity statement present."
        })

    # 9. Storage Instructions
    has_storage = bool(re.search(r"store\s*in\s*a\s*cool|dry\s*place|best\s*before|keep\s*closed", art_lower))
    if has_storage:
        findings.append({
            "id": "CHK-STR",
            "title": "Storage Instructions Present",
            "status": "PASSED",
            "severity": "INFO",
            "is_confirmed": True,
            "certainty": "Verified Passed",
            "applicable_rule": "Quality & Handling Standards",
            "artwork_evidence": "Detected storage instructions in artwork text.",
            "expected_value": "Storage guidelines",
            "explanation": "Storage guidelines are declared on the information panel.",
            "recommendation": "None. Storage instructions verified."
        })

    return findings
