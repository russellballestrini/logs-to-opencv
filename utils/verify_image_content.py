#!/usr/bin/env python3
"""
Verify that converted JPG images contain all the text from the original BMP
"""

import sys
from PIL import Image
import pytesseract


def extract_text_from_image(image_path):
    """Extract text from an image using OCR"""
    try:
        image = Image.open(image_path)
        text = pytesseract.image_to_string(image)
        return text
    except Exception as e:
        print(f"Error extracting text: {e}")
        return None


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 verify_image_content.py <bmp_file> <jpg_file>")
        sys.exit(1)

    bmp_file = sys.argv[1]
    jpg_file = sys.argv[2]

    print(f"Extracting text from BMP: {bmp_file}")
    bmp_text = extract_text_from_image(bmp_file)

    print(f"\nExtracting text from JPG: {jpg_file}")
    jpg_text = extract_text_from_image(jpg_file)

    if bmp_text and jpg_text:
        if bmp_text == jpg_text:
            print("\n✓ Text content is identical in both images!")
        else:
            print("\n✗ Text content differs between images")
            print(f"\nBMP text length: {len(bmp_text)}")
            print(f"JPG text length: {len(jpg_text)}")
