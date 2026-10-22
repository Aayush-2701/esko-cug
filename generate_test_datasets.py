"""
Generate high-precision packaging test datasets for PackGuard AI:
1. ApexBrew Cold Brew Oat Milk Latte (Can Flat Dieline - Compliant Beverage)
2. PeakFuel Almond Crunch Protein Bar (Wrapper Dieline - Multi-discrepancy Snack)
3. LittleSprout Baby Puree (Pouch Dieline - Infant Food with Safety Warnings)

Generates:
- Vector PDF Artwork
- 150 DPI PNG Artwork Proof
- JSON Brand Rulebook Spec
- TXT Brand Guidelines
- XLSX Specification Content Sheet
"""

import os
import json
import pymupdf
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAMPLE_DIR = os.path.join(BASE_DIR, "sample_data")


def draw_barcode(page, rect, upc_digits):
    """Draw a vector simulation of a UPC barcode on the page."""
    x0, y0, x1, y1 = rect
    w = x1 - x0
    h = y1 - y0
    
    # White background for quiet zones
    page.draw_rect(pymupdf.Rect(x0, y0, x1, y1), color=(1, 1, 1), fill=(1, 1, 1))
    page.draw_rect(pymupdf.Rect(x0, y0, x1, y1), color=(0.8, 0.8, 0.8), width=0.5)
    
    # Draw bars (alternating pseudo-random widths)
    bar_y0 = y0 + 5
    bar_y1 = y1 - 14
    cur_x = x0 + 10
    
    pattern = [2, 1, 3, 1, 2, 2, 1, 3, 1, 1, 2, 3, 1, 2, 1, 3, 2, 1, 2, 2, 1, 3, 1, 1, 2, 1, 3, 2, 1, 2]
    idx = 0
    while cur_x < (x1 - 12) and idx < len(pattern):
        bw = pattern[idx % len(pattern)]
        if idx % 2 == 0:
            page.draw_rect(pymupdf.Rect(cur_x, bar_y0, cur_x + bw, bar_y1), color=(0, 0, 0), fill=(0, 0, 0))
        cur_x += bw + 1.2
        idx += 1
        
    # Draw text below bars
    page.insert_text(
        pymupdf.Point(x0 + 12, y1 - 3),
        upc_digits,
        fontsize=8,
        color=(0, 0, 0)
    )


def draw_badge(page, center_x, center_y, radius, title, subtitle="", fill_col=(0.95, 0.95, 0.95), stroke_col=(0.2, 0.5, 0.2)):
    """Draw a circular certification badge."""
    page.draw_circle(pymupdf.Point(center_x, center_y), radius, color=stroke_col, fill=fill_col, width=1.5)
    page.draw_circle(pymupdf.Point(center_x, center_y), radius - 3, color=stroke_col, width=0.8)
    page.insert_text(pymupdf.Point(center_x - radius + 6, center_y - 2), title, fontsize=6.5, color=stroke_col)
    if subtitle:
        page.insert_text(pymupdf.Point(center_x - radius + 8, center_y + 7), subtitle, fontsize=5.5, color=(0.3, 0.3, 0.3))


def export_excel_spec(filepath: str, data: dict):
    """Generate professional Excel Content Sheet (.xlsx)."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Packaging Content Sheet"
    
    # Header styling
    header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    section_fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
    section_font = Font(name="Calibri", size=11, bold=True, color="1F4E79")
    bold_font = Font(name="Calibri", size=10, bold=True)
    normal_font = Font(name="Calibri", size=10)
    thin_border = Border(
        left=Side(style='thin', color='BFBFBF'),
        right=Side(style='thin', color='BFBFBF'),
        top=Side(style='thin', color='BFBFBF'),
        bottom=Side(style='thin', color='BFBFBF')
    )
    
    ws.column_dimensions['A'].width = 28
    ws.column_dimensions['B'].width = 55
    ws.column_dimensions['C'].width = 25

    # Title block
    ws.merge_cells('A1:C1')
    ws['A1'] = f"PACKAGING MASTER SPECIFICATION: {data.get('product_name', 'Specification')}"
    ws['A1'].font = Font(name="Calibri", size=14, bold=True, color="1F4E79")
    ws['A1'].alignment = Alignment(horizontal="left", vertical="center")
    ws.row_dimensions[1].height = 25
    
    row = 3
    headers = ["Specification Attribute", "Mandatory Copy / Requirement", "Regulatory Standard"]
    for col_idx, h in enumerate(headers, 1):
        cell = ws.cell(row=row, column=col_idx, value=h)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="left", vertical="center")
    row += 1
    
    spec_rows = [
        ("Brand Name", data.get("brand"), "Trademark & PDP Core"),
        ("Statement of Identity", data.get("product_name"), "21 CFR § 101.3"),
        ("Net Quantity / Weight", data.get("net_weight_us_required", data.get("net_weight")), "21 CFR § 101.105 Dual Units"),
        ("SKU / BPN", data.get("bpn_sku"), "Internal Master Data"),
        ("UPC Barcode", data.get("barcode_upc"), "GS1 Standard"),
        ("Serving Size", data.get("serving_size"), "21 CFR § 101.9(b)"),
        ("Servings Per Container", str(data.get("servings_per_container")), "21 CFR § 101.9(b)"),
        ("Ingredients List", ", ".join(data.get("expected_ingredients", [])), "21 CFR § 101.4 Descending Order"),
        ("Allergen Declaration", data.get("allergen_requirements", {}).get("rule", "Mandatory Allergen Rule"), "FDA FALCPA / FASTER Act"),
        ("Approved Claims", ", ".join(data.get("approved_claims", [])), "FDA Substantiation Required"),
        ("Storage Instructions", data.get("storage_text"), "Pre-Media Quality Directive")
    ]
    
    for attr, val, std in spec_rows:
        c1 = ws.cell(row=row, column=1, value=attr)
        c2 = ws.cell(row=row, column=2, value=val)
        c3 = ws.cell(row=row, column=3, value=std)
        c1.font = bold_font
        c2.font = normal_font
        c3.font = normal_font
        for c in (c1, c2, c3):
            c.border = thin_border
            c.alignment = Alignment(wrap_text=True, vertical="top")
        row += 1

    wb.save(filepath)


# ==============================================================================
# DATASET 1: APEX BREW - COLD BREW OAT MILK LATTE
# ==============================================================================
def generate_dataset_apex_brew():
    folder = os.path.join(SAMPLE_DIR, "apex_cold_brew")
    
    spec_json = {
        "brand": "Apex Brew",
        "product_name": "Organic Cold Brew Oat Milk Latte",
        "net_weight": "12 fl oz (355 mL)",
        "net_weight_us_required": "12 fl oz (355 mL)",
        "serving_size": "1 Can (355 mL)",
        "servings_per_container": "1",
        "barcode_upc": "8 50012 34567 8",
        "bpn_sku": "AB-OATLATTE-355ML-US",
        "mandatory_fields": [
            "Product Name", "Brand", "Net Quantity / Weight", "Nutrition Facts Panel",
            "Ingredients List", "Allergen Information Statement", "Manufacturer / Distributor Information",
            "Storage Instructions", "UPC Barcode"
        ],
        "expected_ingredients": [
            "Organic Cold Brew Coffee (Water, Organic Arabica Coffee Beans)",
            "Organic Oat Milk (Water, Organic Whole Grain Oats)",
            "Organic Cane Sugar",
            "Organic Sunflower Oil",
            "Sea Salt",
            "Organic Vanilla Extract"
        ],
        "allergen_requirements": {
            "contained_allergens": ["Gluten-Free Oats"],
            "advisory_allergens": ["Tree Nuts (Facility Advisory)"],
            "rule": "Made with gluten-free certified oats. Dairy-free. Advisory: Produced in a facility that also processes tree nuts."
        },
        "net_quantity_rules": {
            "rule": "Per 21 CFR § 101.105, liquid beverage commodities must declare net contents in fluid measure: dual unit declaration '12 fl oz (355 mL)' located on lower 30% of PDP."
        },
        "approved_claims": [
            "USDA Organic",
            "Certified Vegan",
            "Dairy Free",
            "Non-GMO",
            "150mg Natural Caffeine"
        ],
        "storage_text": "Perishable. Keep Refrigerated. Shake gently before opening."
    }
    
    # 1. Save JSON
    with open(os.path.join(folder, "ApexBrew_Spec.json"), "w", encoding="utf-8") as f:
        json.dump(spec_json, f, indent=2)
        
    # 2. Save TXT
    txt_content = f"""PACKAGING SPECIFICATION & REGULATORY GUIDELINE
Product: {spec_json['product_name']}
Brand: {spec_json['brand']}
Market: United States (RTD Beverage)
SKU / BPN: {spec_json['bpn_sku']}
UPC / Barcode: {spec_json['barcode_upc']}

1. PRINCIPAL DISPLAY PANEL (PDP)
- Brand Name: "Apex Brew"
- Statement of Identity: "Organic Cold Brew Oat Milk Latte"
- Net Volume: "12 fl oz (355 mL)" (Dual Declaration mandatory on PDP bottom 30%)
- Front Badges: USDA Organic Seal, Certified Vegan Mark, "150mg Natural Caffeine"

2. INFORMATION PANEL
- Nutrition Facts: Single Serving container (1 Can / 355mL)
  Calories: 110 | Total Fat: 3.5g | Sodium: 85mg | Total Carbs: 18g | Total Sugars: 12g | Protein: 2g
- Ingredients: Organic Cold Brew Coffee (Water, Organic Arabica Coffee Beans), Organic Oat Milk (Water, Organic Whole Grain Oats), Organic Cane Sugar, Organic Sunflower Oil, Sea Salt, Organic Vanilla Extract.
- Allergen Statement: "Dairy-Free. Contains Gluten-Free Oats. Produced in a facility that also processes tree nuts."
- Storage: "Perishable. Keep Refrigerated. Shake gently before opening."
- Manufacturer: "Brewed and canned by Apex Beverage Co., Portland, OR 97201, USA"
- Barcode: GS1 UPC-A {spec_json['barcode_upc']} with required quiet zones.
"""
    with open(os.path.join(folder, "ApexBrew_Spec.txt"), "w", encoding="utf-8") as f:
        f.write(txt_content)
        
    # 3. Save Excel
    export_excel_spec(os.path.join(folder, "ApexBrew_Spec.xlsx"), spec_json)

    # 4. Generate Vector PDF Dieline
    pdf_path = os.path.join(folder, "ApexBrew_ColdBrew_Can_Artwork.pdf")
    doc = pymupdf.open()
    page = doc.new_page(width=900, height=520)
    
    # Outer Dieline / Can Wrap flat
    page.draw_rect(pymupdf.Rect(30, 30, 870, 490), color=(0.1, 0.2, 0.4), fill=(0.96, 0.97, 0.99), width=1.5)
    
    # Dieline Guide Margins (cyan printer guide)
    page.draw_rect(pymupdf.Rect(40, 40, 860, 480), color=(0, 0.7, 0.9), width=0.8, dashes="[3 3] 0")
    page.insert_text(pymupdf.Point(45, 52), "DIELINE SAFETY MARGIN (KEEP TEXT INSIDE)", fontsize=7, color=(0, 0.7, 0.9))

    # Panel Dividers (Left: Info Panel, Center: PDP, Right: Brand & Barcode)
    page.draw_line(pymupdf.Point(310, 40), pymupdf.Point(310, 480), color=(0.8, 0.8, 0.8), width=1, dashes="[4 4] 0")
    page.draw_line(pymupdf.Point(600, 40), pymupdf.Point(600, 480), color=(0.8, 0.8, 0.8), width=1, dashes="[4 4] 0")

    # ---- PANEL 1 (LEFT): INFORMATION & NUTRITION PANEL ----
    page.insert_text(pymupdf.Point(55, 75), "Nutrition Facts", fontsize=15, color=(0, 0, 0))
    page.insert_text(pymupdf.Point(55, 90), "1 serving per container", fontsize=8.5, color=(0.2, 0.2, 0.2))
    page.insert_text(pymupdf.Point(55, 102), "Serving size              1 Can (355 mL)", fontsize=9, color=(0, 0, 0))
    page.draw_rect(pymupdf.Rect(55, 108, 290, 114), color=(0, 0, 0), fill=(0, 0, 0))
    
    page.insert_text(pymupdf.Point(55, 126), "Amount per serving", fontsize=8, color=(0.2, 0.2, 0.2))
    page.insert_text(pymupdf.Point(55, 142), "Calories                 110", fontsize=14, color=(0, 0, 0))
    page.draw_line(pymupdf.Point(55, 148), pymupdf.Point(290, 148), color=(0, 0, 0), width=1.5)
    
    page.insert_text(pymupdf.Point(55, 162), "Total Fat 3.5g                                  4%", fontsize=8.5, color=(0, 0, 0))
    page.insert_text(pymupdf.Point(55, 176), "  Saturated Fat 0.5g                          3%", fontsize=8, color=(0.3, 0.3, 0.3))
    page.insert_text(pymupdf.Point(55, 190), "Sodium 85mg                                     4%", fontsize=8.5, color=(0, 0, 0))
    page.insert_text(pymupdf.Point(55, 204), "Total Carbohydrate 18g                  7%", fontsize=8.5, color=(0, 0, 0))
    page.insert_text(pymupdf.Point(55, 218), "  Total Sugars 12g", fontsize=8, color=(0.3, 0.3, 0.3))
    page.insert_text(pymupdf.Point(55, 232), "Protein 2g", fontsize=8.5, color=(0, 0, 0))
    page.draw_line(pymupdf.Point(55, 240), pymupdf.Point(290, 240), color=(0, 0, 0), width=3)

    # Ingredients & Allergen
    page.insert_text(pymupdf.Point(55, 260), "INGREDIENTS:", fontsize=8.5, color=(0, 0, 0))
    ing_text = (
        "Organic Cold Brew Coffee (Water, Organic Arabica Coffee Beans), "
        "Organic Oat Milk (Water, Organic Whole Grain Oats), Organic Cane Sugar, "
        "Organic Sunflower Oil, Sea Salt, Organic Vanilla Extract."
    )
    rect_ing = pymupdf.Rect(55, 268, 290, 345)
    page.insert_textbox(rect_ing, ing_text, fontsize=7.5, color=(0.2, 0.2, 0.2))

    page.insert_text(pymupdf.Point(55, 360), "ALLERGEN INFORMATION:", fontsize=8, color=(0, 0, 0))
    page.insert_text(pymupdf.Point(55, 373), "Dairy-Free. Contains Gluten-Free Oats.", fontsize=7.5, color=(0, 0, 0))
    page.insert_text(pymupdf.Point(55, 385), "Produced in a facility that also processes tree nuts.", fontsize=7, color=(0.3, 0.3, 0.3))

    page.insert_text(pymupdf.Point(55, 415), "DISTRIBUTED BY:", fontsize=7.5, color=(0, 0, 0))
    page.insert_text(pymupdf.Point(55, 428), "Apex Beverage Co., Portland, OR 97201, USA", fontsize=7.5, color=(0.2, 0.2, 0.2))
    page.insert_text(pymupdf.Point(55, 442), "Product of USA", fontsize=7.5, color=(0.2, 0.2, 0.2))

    # ---- PANEL 2 (CENTER): PRINCIPAL DISPLAY PANEL (PDP) ----
    page.draw_rect(pymupdf.Rect(325, 45, 585, 475), color=(0.93, 0.94, 0.98), fill=(0.93, 0.94, 0.98))
    page.draw_circle(pymupdf.Point(455, 120), 45, color=(0.15, 0.3, 0.6), fill=(0.15, 0.3, 0.6))
    page.insert_text(pymupdf.Point(433, 126), "APEX", fontsize=15, color=(1, 1, 1))

    page.insert_text(pymupdf.Point(395, 195), "Apex Brew", fontsize=24, color=(0.1, 0.2, 0.4))
    page.insert_text(pymupdf.Point(345, 225), "ORGANIC COLD BREW", fontsize=14, color=(0.7, 0.3, 0.1))
    page.insert_text(pymupdf.Point(375, 248), "Oat Milk Latte", fontsize=16, color=(0.2, 0.2, 0.2))

    page.insert_text(pymupdf.Point(370, 280), "Smooth & Creamy / Non-Dairy", fontsize=9, color=(0.4, 0.4, 0.4))

    # Badges on PDP
    draw_badge(page, 385, 340, 24, "USDA", "ORGANIC", fill_col=(0.95, 1, 0.95), stroke_col=(0.1, 0.5, 0.1))
    draw_badge(page, 455, 340, 24, "VEGAN", "CERTIFIED", fill_col=(1, 1, 0.95), stroke_col=(0.7, 0.5, 0.1))
    draw_badge(page, 525, 340, 24, "NON", "GMO", fill_col=(0.95, 0.95, 1), stroke_col=(0.2, 0.3, 0.7))

    page.insert_text(pymupdf.Point(395, 395), "150mg Natural Caffeine", fontsize=9.5, color=(0.1, 0.2, 0.4))

    # Mandatory Dual Net Quantity on PDP (Bottom 30%)
    page.draw_rect(pymupdf.Rect(355, 425, 555, 455), color=(0.1, 0.2, 0.4), fill=(1, 1, 1), width=1)
    page.insert_text(pymupdf.Point(375, 445), "12 fl oz (355 mL)", fontsize=13, color=(0, 0, 0))

    # ---- PANEL 3 (RIGHT): BRAND STORY, STORAGE & BARCODE ----
    page.insert_text(pymupdf.Point(620, 75), "BREWED SLOW & CRAFTED PURE", fontsize=10, color=(0.1, 0.2, 0.4))
    story_text = (
        "We steep our specialty organic Arabica beans in pure filtered water for 18 hours. "
        "Blended seamlessly with silky oat milk for a rich, low-acid coffee experience."
    )
    page.insert_textbox(pymupdf.Rect(620, 90, 840, 160), story_text, fontsize=8, color=(0.3, 0.3, 0.3))

    page.insert_text(pymupdf.Point(620, 180), "STORAGE & HANDLING:", fontsize=8.5, color=(0, 0, 0))
    page.insert_text(pymupdf.Point(620, 195), "Perishable. Keep Refrigerated.", fontsize=8, color=(0.8, 0.1, 0.1))
    page.insert_text(pymupdf.Point(620, 208), "Shake gently before opening.", fontsize=7.5, color=(0.3, 0.3, 0.3))

    page.insert_text(pymupdf.Point(620, 240), "RECYCLABILITY:", fontsize=8, color=(0, 0, 0))
    page.insert_text(pymupdf.Point(620, 252), "100% Recyclable Aluminum Can", fontsize=7.5, color=(0.2, 0.4, 0.2))

    # Barcode
    draw_barcode(page, (635, 290, 825, 365), "8 50012 34567 8")
    
    page.insert_text(pymupdf.Point(635, 395), "BPN / SKU: AB-OATLATTE-355ML-US", fontsize=7.5, color=(0.3, 0.3, 0.3))

    doc.save(pdf_path)
    
    # Export 150 DPI PNG
    pix = page.get_pixmap(dpi=150)
    png_path = os.path.join(folder, "ApexBrew_ColdBrew_Can_Artwork.png")
    pix.save(png_path)
    doc.close()
    print("Dataset 1 (Apex Brew) generated successfully.")


# ==============================================================================
# DATASET 2: PEAKFUEL - DARK CHOCOLATE ALMOND PROTEIN BAR (MULTI-DISCREPANCY)
# ==============================================================================
def generate_dataset_peakfuel():
    folder = os.path.join(SAMPLE_DIR, "peakfuel_protein_bar")
    
    spec_json = {
        "brand": "PeakFuel",
        "product_name": "Dark Chocolate Almond Crunch Protein Bar",
        "net_weight": "60g",
        "net_weight_us_required": "60g (2.12 oz)",
        "serving_size": "1 Bar (60g)",
        "servings_per_container": "1",
        "barcode_upc": "0 98765 43210 9",
        "bpn_sku": "PF-BAR-ALMOND-60G",
        "mandatory_fields": [
            "Product Name", "Brand", "Net Quantity / Weight", "Nutrition Facts Panel",
            "Ingredients List", "Allergen Information Statement", "Manufacturer / Distributor Information",
            "Storage Instructions", "UPC Barcode"
        ],
        "expected_ingredients": [
            "Brown Rice Protein",
            "Pea Protein",
            "Dark Chocolate Chips (Cocoa Butter, Sugar)",
            "Almond Butter",
            "Chopped Almonds",
            "Tapioca Syrup",
            "Sea Salt"
        ],
        "allergen_requirements": {
            "contained_allergens": ["Almonds (Tree Nut)"],
            "advisory_allergens": ["Peanuts", "Soy"],
            "rule": "Per FDA FALCPA regulations, tree nuts used as recipe ingredients (Almonds) must be explicitly disclosed in the ingredients list and declared in a 'Contains: Almonds' statement. Generic 'May contain nuts' advisory alone is a statutory violation."
        },
        "net_quantity_rules": {
            "rule": "Per 21 CFR § 101.105, net quantity on the Principal Display Panel must display dual units (US Customary ounces + metric grams): '60g (2.12 oz)'. Displaying metric grams alone fails US food labeling requirements."
        },
        "approved_claims": [
            "20g Plant Protein",
            "Non-GMO Project Verified",
            "Gluten Free"
        ],
        "unapproved_claims_flag": "No drug, disease prevention, or unapproved structure/function claims are permitted.",
        "storage_text": "Store in a cool, dry place away from direct sunlight."
    }
    
    # 1. Save JSON
    with open(os.path.join(folder, "PeakFuel_Spec.json"), "w", encoding="utf-8") as f:
        json.dump(spec_json, f, indent=2)
        
    # 2. Save TXT
    txt_content = f"""PACKAGING SPECIFICATION & REGULATORY AUDIT RULEBOOK
Product: {spec_json['product_name']}
Brand: {spec_json['brand']}
Market: United States (Nutrition Bars / Confectionery)
SKU / BPN: {spec_json['bpn_sku']}
Master GS1 Barcode: {spec_json['barcode_upc']}

1. MANDATORY REQUIREMENTS & SPECIFICATION LIMITS
- Brand: "PeakFuel"
- Identity Statement: "Dark Chocolate Almond Crunch Protein Bar"
- Net Weight Declaration: "60g (2.12 oz)" - MUST declare both avoirdupois ounces and metric grams per 21 CFR § 101.105.
- Mandatory Allergen Clause: Direct recipe ingredients include Chopped Almonds and Almond Butter. Under FALCPA / 21 U.S.C. 343(w), package MUST declare "CONTAINS: ALMONDS". A vague "May contain nuts" disclaimer is legally defective.
- Health / Functional Claims: Only "20g Plant Protein", "Non-GMO", "Gluten Free" are approved. Any disease prevention claim is strictly prohibited.
- Barcode: Must exactly match GS1 registered UPC {spec_json['barcode_upc']}.
"""
    with open(os.path.join(folder, "PeakFuel_Spec.txt"), "w", encoding="utf-8") as f:
        f.write(txt_content)
        
    # 3. Save Excel Content Sheet
    export_excel_spec(os.path.join(folder, "PeakFuel_Spec.xlsx"), spec_json)

    # 4. Generate Vector PDF Artwork with INTENTIONAL DISCREPANCIES to test the engine
    pdf_path = os.path.join(folder, "PeakFuel_ProteinBar_Wrapper.pdf")
    doc = pymupdf.open()
    page = doc.new_page(width=850, height=480)
    
    # Dieline wrapper boundary
    page.draw_rect(pymupdf.Rect(25, 25, 825, 455), color=(0.8, 0.2, 0.2), fill=(0.99, 0.98, 0.95), width=1.5)
    
    # Guide bleed line
    page.draw_rect(pymupdf.Rect(35, 35, 815, 445), color=(1, 0, 0), width=0.8, dashes="[2 2] 0")
    page.insert_text(pymupdf.Point(40, 48), "TRIM / BLEED LINE (DISCREPANCY TEST PROOF)", fontsize=7, color=(0.8, 0, 0))

    # Fin-seal flap markers
    page.draw_line(pymupdf.Point(25, 120), pymupdf.Point(825, 120), color=(0.7, 0.7, 0.7), width=1, dashes="[3 3] 0")
    page.draw_line(pymupdf.Point(25, 360), pymupdf.Point(825, 360), color=(0.7, 0.7, 0.7), width=1, dashes="[3 3] 0")
    page.insert_text(pymupdf.Point(30, 114), "TOP SEAL FOLD FLAP", fontsize=7, color=(0.5, 0.5, 0.5))
    page.insert_text(pymupdf.Point(30, 372), "BOTTOM SEAL FOLD FLAP", fontsize=7, color=(0.5, 0.5, 0.5))

    # ---- MAIN FRONT WRAPPER PANEL (PDP: Center Area) ----
    page.draw_rect(pymupdf.Rect(50, 130, 520, 350), color=(0.1, 0.1, 0.1), fill=(0.12, 0.12, 0.14))
    
    page.insert_text(pymupdf.Point(70, 170), "PeakFuel", fontsize=28, color=(0.95, 0.65, 0.1))
    page.insert_text(pymupdf.Point(70, 195), "DARK CHOCOLATE ALMOND CRUNCH", fontsize=13, color=(1, 1, 1))
    page.insert_text(pymupdf.Point(70, 215), "Plant-Based High Performance Protein Bar", fontsize=9.5, color=(0.8, 0.8, 0.8))

    # Approved Claim
    page.draw_rect(pymupdf.Rect(70, 230, 190, 255), color=(0.95, 0.65, 0.1), fill=(0.95, 0.65, 0.1))
    page.insert_text(pymupdf.Point(82, 248), "20g PLANT PROTEIN", fontsize=9.5, color=(0, 0, 0))

    # [DISCREPANCY 1]: Unapproved Medical Disease Claim
    page.draw_rect(pymupdf.Rect(210, 230, 480, 255), color=(0.8, 0.2, 0.2), fill=(0.8, 0.1, 0.1))
    page.insert_text(pymupdf.Point(218, 248), "* Cures Chronic Fatigue & Prevents Cellular Aging", fontsize=8, color=(1, 1, 1))

    # [DISCREPANCY 2]: Metric Only Net Weight (Missing required 2.12 oz dual unit)
    page.insert_text(pymupdf.Point(70, 335), "Net Wt. 60g", fontsize=14, color=(1, 1, 1))
    page.insert_text(pymupdf.Point(170, 335), "(Note: No US Customary Ounces Declared)", fontsize=7.5, color=(0.8, 0.4, 0.4))

    # Certification Badges
    draw_badge(page, 440, 310, 20, "NON", "GMO", fill_col=(0.2, 0.2, 0.2), stroke_col=(0.9, 0.9, 0.9))
    draw_badge(page, 490, 310, 20, "GLUTEN", "FREE", fill_col=(0.2, 0.2, 0.2), stroke_col=(0.9, 0.9, 0.9))

    # ---- REAR / FLAP COPY PANEL (Right Side: 540 - 810) ----
    page.insert_text(pymupdf.Point(545, 140), "Nutrition Facts", fontsize=13, color=(0, 0, 0))
    page.insert_text(pymupdf.Point(545, 153), "Serving size: 1 Bar (60g)", fontsize=8, color=(0.2, 0.2, 0.2))
    page.insert_text(pymupdf.Point(545, 168), "Calories 240 | Total Fat 11g | Protein 20g", fontsize=8, color=(0, 0, 0))
    page.draw_line(pymupdf.Point(545, 174), pymupdf.Point(800, 174), color=(0, 0, 0), width=1)

    # Ingredients List
    page.insert_text(pymupdf.Point(545, 190), "INGREDIENTS:", fontsize=8, color=(0, 0, 0))
    bar_ing = (
        "Brown Rice Protein, Pea Protein, Dark Chocolate Chips (Cocoa Butter, Sugar), "
        "Almond Butter, Chopped Almonds, Tapioca Syrup, Sea Salt."
    )
    page.insert_textbox(pymupdf.Rect(545, 196, 805, 255), bar_ing, fontsize=7.5, color=(0.2, 0.2, 0.2))

    # [DISCREPANCY 3]: Defective Allergen Advisory (Direct Almonds not declared in Contains statement)
    page.insert_text(pymupdf.Point(545, 265), "ALLERGEN WARNING:", fontsize=8, color=(0.8, 0, 0))
    page.insert_text(pymupdf.Point(545, 278), "May contain traces of tree nuts and dairy.", fontsize=7.5, color=(0.8, 0, 0))
    page.insert_text(pymupdf.Point(545, 290), "(Mandatory 'CONTAINS: ALMONDS' statement omitted)", fontsize=6.5, color=(0.6, 0.6, 0.6))

    # [DISCREPANCY 4]: Barcode Mismatch (Artwork prints 0 98765 99999 9 instead of 0 98765 43210 9)
    draw_barcode(page, (550, 310, 750, 370), "0 98765 99999 9")

    # Manufacturer
    page.insert_text(pymupdf.Point(545, 395), "Manufactured by PeakFuel Nutrition LLC, Boulder, CO 80301", fontsize=7, color=(0.3, 0.3, 0.3))
    page.insert_text(pymupdf.Point(545, 410), "Storage: Store in a cool, dry place.", fontsize=7, color=(0.3, 0.3, 0.3))

    # [DISCREPANCY 5]: Text encroaching dieline border
    page.insert_text(pymupdf.Point(545, 442), "BATCH CODE EXP 12/2027 LOT 4022A [OVERLAPS TRIM GUIDE]", fontsize=6.5, color=(0.9, 0, 0))

    doc.save(pdf_path)
    
    # Export 150 DPI PNG
    pix = page.get_pixmap(dpi=150)
    png_path = os.path.join(folder, "PeakFuel_ProteinBar_Wrapper.png")
    pix.save(png_path)
    doc.close()
    print("Dataset 2 (PeakFuel Protein Bar) generated successfully.")


# ==============================================================================
# DATASET 3: LITTLESPROUT - ORGANIC APPLE MANGO BABY PUREE POUCH
# ==============================================================================
def generate_dataset_littlesprout():
    folder = os.path.join(SAMPLE_DIR, "littlesprout_baby_puree")
    
    spec_json = {
        "brand": "LittleSprout Organics",
        "product_name": "Organic Apple Mango Carrot Baby Puree",
        "net_weight": "99g (3.5 oz)",
        "net_weight_us_required": "99g (3.5 oz)",
        "serving_size": "1 Pouch (99g)",
        "servings_per_container": "1",
        "barcode_upc": "7 12345 67890 1",
        "bpn_sku": "LS-PUREE-APPLMNG-99G",
        "mandatory_fields": [
            "Product Name", "Brand", "Net Quantity / Weight", "Nutrition Facts Panel",
            "Ingredients List", "Allergen Information Statement", "Manufacturer / Distributor Information",
            "Storage Instructions", "UPC Barcode"
        ],
        "expected_ingredients": [
            "Organic Apple Puree (55%)",
            "Organic Mango Puree (30%)",
            "Organic Carrot Puree (15%)",
            "Organic Lemon Juice Concentrate"
        ],
        "allergen_requirements": {
            "contained_allergens": [],
            "advisory_allergens": [],
            "rule": "Product is naturally allergen-free. Allergen statement should confirm allergen-free status or state 'Contains no major food allergens'."
        },
        "net_quantity_rules": {
            "rule": "Dual unit declaration required on bottom 30% of PDP: '99g (3.5 oz)'."
        },
        "approved_claims": [
            "USDA Organic",
            "Non-GMO",
            "No Added Sugars",
            "BPA-Free Packaging",
            "Stage 2 (6+ Months)"
        ],
        "safety_warnings": {
            "rule": "Mandatory FDA infant pouch warning: 'CHOKING HAZARD: Keep cap out of reach of children under 3 years. Do not microwave pouch.'"
        },
        "storage_text": "Store unopened at room temperature. Refrigerate within 1 hour after opening and serve within 24 hours."
    }
    
    # 1. Save JSON
    with open(os.path.join(folder, "LittleSprout_Spec.json"), "w", encoding="utf-8") as f:
        json.dump(spec_json, f, indent=2)
        
    # 2. Save TXT
    txt_content = f"""PACKAGING SPECIFICATION & REGULATORY COMPLIANCE DIRECTIVE
Product: {spec_json['product_name']}
Brand: {spec_json['brand']}
Market: United States (Infant & Toddler Foods - Stage 2 Pouch)
SKU / BPN: {spec_json['bpn_sku']}
UPC / Barcode: {spec_json['barcode_upc']}

1. PRINCIPAL DISPLAY PANEL (PDP)
- Brand Name: "LittleSprout Organics"
- Product Name: "Organic Apple Mango Carrot Baby Puree"
- Target Age: "Stage 2 | 6+ Months"
- Net Weight: "99g (3.5 oz)" (Dual declaration on lower PDP)
- Certifications: USDA Organic, Non-GMO Project Verified, BPA-Free Packaging

2. INFANT SAFETY & MANDATORY WARNING COPY
- Choking Notice: "WARNING: Keep cap out of reach of children under 3. If pouch is damaged or swollen, do not consume. Do not microwave pouch."
- Ingredients: Organic Apple Puree (55%), Organic Mango Puree (30%), Organic Carrot Puree (15%), Organic Lemon Juice Concentrate.
- Allergen Declaration: "Contains No Major Food Allergens."
- Storage: "Refrigerate within 1 hour of opening and serve within 24 hours."
- Barcode: {spec_json['barcode_upc']}
"""
    with open(os.path.join(folder, "LittleSprout_Spec.txt"), "w", encoding="utf-8") as f:
        f.write(txt_content)
        
    # 3. Save Excel
    export_excel_spec(os.path.join(folder, "LittleSprout_Spec.xlsx"), spec_json)

    # 4. Generate Vector PDF Pouch Proof
    pdf_path = os.path.join(folder, "LittleSprout_BabyPuree_Pouch.pdf")
    doc = pymupdf.open()
    page = doc.new_page(width=800, height=550)
    
    # Background pouch dieline (2 panels side by side: Back Panel Left, Front PDP Right)
    page.draw_rect(pymupdf.Rect(40, 30, 760, 520), color=(0.2, 0.6, 0.4), fill=(0.97, 0.99, 0.96), width=1.5)
    page.draw_rect(pymupdf.Rect(50, 40, 750, 510), color=(0.4, 0.8, 0.4), width=0.8, dashes="[3 3] 0")
    page.insert_text(pymupdf.Point(55, 52), "POUCH STAND-UP GUSSET DIELINE (150 DPI PROOF)", fontsize=7, color=(0.2, 0.6, 0.3))

    page.draw_line(pymupdf.Point(400, 40), pymupdf.Point(400, 510), color=(0.7, 0.7, 0.7), width=1, dashes="[4 4] 0")

    # ---- LEFT HALF: BACK INFORMATION & SAFETY PANEL ----
    page.insert_text(pymupdf.Point(65, 80), "Nutrition Facts", fontsize=14, color=(0, 0, 0))
    page.insert_text(pymupdf.Point(65, 94), "1 serving per pouch | Serving size: 1 Pouch (99g)", fontsize=8, color=(0.2, 0.2, 0.2))
    page.insert_text(pymupdf.Point(65, 110), "Calories 60 | Total Fat 0g | Total Sugars 12g | Potassium 180mg", fontsize=8, color=(0, 0, 0))
    page.draw_line(pymupdf.Point(65, 116), pymupdf.Point(380, 116), color=(0, 0, 0), width=1.5)

    page.insert_text(pymupdf.Point(65, 135), "INGREDIENTS:", fontsize=8.5, color=(0, 0, 0))
    puree_ing = (
        "Organic Apple Puree (55%), Organic Mango Puree (30%), "
        "Organic Carrot Puree (15%), Organic Lemon Juice Concentrate."
    )
    page.insert_textbox(pymupdf.Rect(65, 142, 380, 195), puree_ing, fontsize=8, color=(0.2, 0.2, 0.2))

    page.insert_text(pymupdf.Point(65, 205), "ALLERGENS:", fontsize=8, color=(0, 0, 0))
    page.insert_text(pymupdf.Point(65, 218), "Contains No Major Food Allergens. Gluten Free.", fontsize=7.5, color=(0.1, 0.5, 0.2))

    # MANDATORY CHOKING HAZARD WARNING BOX
    page.draw_rect(pymupdf.Rect(65, 235, 380, 290), color=(0.8, 0.4, 0), fill=(1, 0.97, 0.9), width=1)
    page.insert_text(pymupdf.Point(75, 252), "WARNING: CHOKING HAZARD", fontsize=8.5, color=(0.8, 0.2, 0))
    warning_text = (
        "Keep cap out of reach of children under 3 years. "
        "If pouch is damaged or swollen, do not consume. "
        "Do not microwave pouch directly."
    )
    page.insert_textbox(pymupdf.Rect(75, 258, 375, 288), warning_text, fontsize=7.5, color=(0.2, 0.2, 0.2))

    # Storage Directions
    page.insert_text(pymupdf.Point(65, 310), "FEEDING & STORAGE INSTRUCTIONS:", fontsize=8, color=(0, 0, 0))
    page.insert_text(pymupdf.Point(65, 323), "Store unopened pouch at room temperature.", fontsize=7.5, color=(0.3, 0.3, 0.3))
    page.insert_text(pymupdf.Point(65, 335), "Refrigerate within 1 hour after opening and serve within 24 hours.", fontsize=7.5, color=(0.3, 0.3, 0.3))

    page.insert_text(pymupdf.Point(65, 360), "LittleSprout Baby Nutrition Inc., Austin, TX 78701", fontsize=7.5, color=(0.4, 0.4, 0.4))
    page.insert_text(pymupdf.Point(65, 372), "Certified Organic by QAI | BPA-Free Packaging", fontsize=7.5, color=(0.2, 0.5, 0.2))

    # Barcode
    draw_barcode(page, (80, 400, 310, 470), "7 12345 67890 1")

    # ---- RIGHT HALF: PRINCIPAL DISPLAY PANEL (PDP) ----
    page.draw_rect(pymupdf.Rect(415, 50, 740, 500), color=(0.94, 0.98, 0.94), fill=(0.94, 0.98, 0.94))

    # Age recommendation banner
    page.draw_rect(pymupdf.Rect(440, 70, 715, 95), color=(0.2, 0.6, 0.4), fill=(0.2, 0.6, 0.4))
    page.insert_text(pymupdf.Point(510, 87), "STAGE 2  |  6+ MONTHS", fontsize=11, color=(1, 1, 1))

    page.insert_text(pymupdf.Point(475, 140), "LittleSprout", fontsize=24, color=(0.15, 0.5, 0.3))
    page.insert_text(pymupdf.Point(535, 160), "ORGANICS", fontsize=10, color=(0.7, 0.4, 0.1))

    page.insert_text(pymupdf.Point(450, 205), "Apple Mango Carrot", fontsize=18, color=(0.85, 0.35, 0.1))
    page.insert_text(pymupdf.Point(495, 230), "Smooth Organic Puree", fontsize=12, color=(0.3, 0.3, 0.3))

    # Features
    page.insert_text(pymupdf.Point(470, 275), "* Made with Real Fruit & Veggies", fontsize=9, color=(0.2, 0.4, 0.2))
    page.insert_text(pymupdf.Point(470, 292), "* No Artificial Preservatives or Sugars", fontsize=9, color=(0.2, 0.4, 0.2))
    page.insert_text(pymupdf.Point(470, 309), "* Unsweetened & Non-GMO", fontsize=9, color=(0.2, 0.4, 0.2))

    # Badges
    draw_badge(page, 480, 370, 25, "USDA", "ORGANIC", fill_col=(0.95, 1, 0.95), stroke_col=(0.1, 0.5, 0.1))
    draw_badge(page, 570, 370, 25, "NON", "GMO", fill_col=(1, 1, 0.95), stroke_col=(0.7, 0.5, 0.1))
    draw_badge(page, 660, 370, 25, "BPA", "FREE", fill_col=(0.95, 0.98, 1), stroke_col=(0.2, 0.4, 0.7))

    # Net Weight Dual Declaration on PDP
    page.draw_rect(pymupdf.Rect(480, 435, 680, 470), color=(0.2, 0.6, 0.4), fill=(1, 1, 1), width=1)
    page.insert_text(pymupdf.Point(525, 458), "NET WT 99g (3.5 oz)", fontsize=13, color=(0, 0, 0))

    doc.save(pdf_path)
    
    # Export 150 DPI PNG
    pix = page.get_pixmap(dpi=150)
    png_path = os.path.join(folder, "LittleSprout_BabyPuree_Pouch.png")
    pix.save(png_path)
    doc.close()
    print("Dataset 3 (LittleSprout Puree) generated successfully.")


if __name__ == "__main__":
    generate_dataset_apex_brew()
    generate_dataset_peakfuel()
    generate_dataset_littlesprout()
    print("All test datasets generated successfully!")
