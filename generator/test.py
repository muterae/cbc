from pathlib import Path
from PIL import Image
from pathlib import Path
import pytesseract
from pypdf import PdfReader
import os
import re
import time
DOCUMENTS_DIR = Path('documents')





def get_documents():
    document_paths = []
    for doc in DOCUMENTS_DIR.iterdir():
        if doc.is_file():
            document_paths.append({
                'name':doc.name,
                'path':doc
            })
    return document_paths


def ingest_documents_OCR():
    for d in get_documents():
        print(f"Reading document {d['path']}")
        reader = PdfReader(d['path'])
        page = reader.pages[0]
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

        with open(f"{d['name']}.txt", "a", encoding="utf-8") as file:
            for i, image_file_object in enumerate(page.images):
                file_name = f"{d['name']}-image-" + str(i) + "-" + image_file_object.name
                print(f"Writing document image {file_name}")
                if image_file_object.image is None:
                    print(f"Image on page {i} not found.")
                else:
                    saved_image_path = Path("images_temp", file_name)
                    image_file_object.image.save(saved_image_path)
                    text = pytesseract.image_to_string(Image.open(saved_image_path))
                    file.write("\n"+text)



def ingest_document():
    document_paths = get_documents()
    print(f"Decoding document {document_paths[2]['name']}")
    reader = PdfReader(document_paths[2]['path'])
    total_pages = len(reader.pages)
    page = reader.pages[10].extract_text()

    for d in document_paths:
        output_path = Path('output', f"{d['name']}.txt")
        print(f"Decoding document {output_path}")
        with open(output_path, "a", encoding="utf-8") as file:
            reader = PdfReader(document_paths[2]['path'])
            total_pages = len(reader.pages)
            print(f"Writing to {output_path}, total pages: {total_pages}")
            for i in reader.pages:
                file.write("\n"+i.extract_text())




# document id=2 does not need OCR


start_time = time.perf_counter()
ingest_document()
end_time = time.perf_counter()
print(f"Finished in: {end_time-start_time:.6f} s")
