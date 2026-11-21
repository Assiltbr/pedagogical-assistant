import sys
import pymupdf

doc = pymupdf.open(sys.argv[1])
print("pages:", len(doc), "| metadata:", doc.metadata.get("producer"), "/", doc.metadata.get("creator"))
for i, page in enumerate(doc):
    print(f"page {i+1}: {len(page.get_text().strip())} chars, {len(page.get_images())} images")
    if i >= 9:
        break

# Try to repair: rewrite the file with cleaned-up structure
try:
    doc.save("repaired.pdf", garbage=4, clean=True, deflate=True)
    print("repaired.pdf written")
except Exception as e:
    print("repair failed:", e)