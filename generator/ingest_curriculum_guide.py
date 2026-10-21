# from pypdf import PdfReader
from PIL import Image
from pathlib import Path
import pytesseract
from pypdf import PdfReader
import os


# 1. Extract the images from the pdf
# This is because this particular pdf (`HI MATHEMATICS GRADE 2.pdf`) does not contain text only images
# Using pyPDF to extract the images and pytesseracts OCR to extract the text from the images
reader = PdfReader("HI MATHEMATICS GRADE 2.pdf")
page = reader.pages[0]
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

i = 6
with open("output.txt", "a", encoding="utf-8") as file:
    for i, image_file_object in enumerate(page.images):
        file_name = "out-image-" + str(i) + "-" + image_file_object.name
        if image_file_object.image is None:
            print(f"Image on page {i} not found.")
        else:
            saved_image_path = Path("data-sets", file_name)
            image_file_object.image.save(saved_image_path)
            # text= pytesseract.image_to_string(Image.open(saved_image_path)))
            # file.write("\n"+text)
