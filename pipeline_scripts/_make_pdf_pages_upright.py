import glob
import os
from PDFExtract.Document import make_pages_upright

if __name__ == "__main__":
    files_to_process = glob.glob(r"test_pdfs\rotation\*.pdf")
    for file in files_to_process:
        make_pages_upright(file, r"processed_pdf")
