import urllib.request
import json
import os

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "manual_upload_test_suite", "Real_World_Downloads")
os.makedirs(OUT_DIR, exist_ok=True)

PRODUCTS = [
    {
        "barcode": "0044000032029",
        "folder": "Oreo_Chocolate_Sandwich_Cookies",
        "brand": "Oreo, Nabisco",
        "name": "Chocolate Sandwich Cookies"
    },
    {
        "barcode": "0016000264625",
        "folder": "Nature_Valley_Oats_And_Honey_Granola_Bars",
        "brand": "Nature Valley",
        "name": "Crunchy Granola Bars, Oats 'n Honey"
    }
]

headers = {"User-Agent": "PackGuardAI-Research/1.0"}

for item in PRODUCTS:
    barcode = item["barcode"]
    prod_folder = os.path.join(OUT_DIR, item["folder"])
    os.makedirs(prod_folder, exist_ok=True)
    
    url = f"https://world.openfoodfacts.org/api/v2/product/{barcode}.json"
    req = urllib.request.Request(url, headers=headers)
    
    try:
        print(f"Fetching {item['name']} ({barcode})...")
        with urllib.request.urlopen(req, timeout=12) as response:
            data = json.loads(response.read().decode("utf-8"))
            
        if data.get("status") == 1:
            p = data["product"]
            brand = p.get("brands") or item["brand"]
            name = p.get("product_name") or item["name"]
            net_wt = p.get("quantity") or "14.3 oz (405g)"
            ingredients_text = p.get("ingredients_text") or "Sugar, Unbleached Enriched Flour, Palm Oil, Cocoa, High Fructose Corn Syrup, Leavening, Salt, Soy Lecithin, Chocolate, Artificial Flavor."
            allergens = p.get("allergens_tags") or ["en:soybeans", "en:gluten"]
            front_img_url = p.get("image_front_url") or p.get("image_url")
            
            spec = {
                "brand": brand,
                "product_name": name,
                "net_weight": net_wt,
                "net_weight_us_required": net_wt,
                "barcode_upc": barcode,
                "ingredients_list": ingredients_text,
                "allergens": allergens,
                "mandatory_fields": [
                    "Product Name", "Brand", "Net Quantity / Weight", "Nutrition Facts Panel",
                    "Ingredients List", "Allergen Information Statement", "UPC Barcode"
                ]
            }
            
            with open(os.path.join(prod_folder, "Step2_UPLOAD_THIS_RULEBOOK__Specification.json"), "w", encoding="utf-8") as f:
                json.dump(spec, f, indent=2)
                
            if front_img_url:
                img_path = os.path.join(prod_folder, "Step1_UPLOAD_THIS_ARTWORK__Packaging_Front.jpg")
                img_req = urllib.request.Request(front_img_url, headers=headers)
                with urllib.request.urlopen(img_req, timeout=15) as img_resp:
                    with open(img_path, "wb") as f_img:
                        f_img.write(img_resp.read())
                print(f"Successfully downloaded packaging photo for {name}")
    except Exception as e:
        print(f"Error {barcode}: {e}")

print("Done downloading real world products.")
