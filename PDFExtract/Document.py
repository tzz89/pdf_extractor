from PyPDF2 import PdfFileReader, PdfFileWriter
# import pdfminer.six
import pdfplumber
import os
import json
import random
import io


def __get_pdf_metadata(pdf_obj):
    """This Function takes in a PdfFileReader object and returns document metadata

    Args:
        pdf_obj ([PdfWriteObj]): [description]

    Returns:
         {
            "author": null,
            "creator": "Adobe InDesign 16.0 (Macintosh)",
            "producer": "Adobe PDF Library 15.0",
            "subject": null,
            "title": null,
            "pages": 342
        }
    """
    pdf_metadata_dict = {}

    info = pdf_obj.getDocumentInfo()
    number_of_pages = pdf_obj.getNumPages()

    pdf_metadata_dict['author'] = info.author
    pdf_metadata_dict['creator'] = info.creator
    pdf_metadata_dict['producer'] = info.producer
    pdf_metadata_dict['subject'] = info.subject
    pdf_metadata_dict['title'] = info.title
    pdf_metadata_dict['pages'] = number_of_pages

    meta_data = pdf_metadata_dict

    return meta_data


def get_document_info(pdf):
    """This method takes in either the pdf path of type string or a PdfFileReader Oject and returns
       the pdf meta data

    Args:
        pdf ([string/PyPDFFileReader]): can be a string path or PDFReader

    Returns:
        {
            "author": null,
            "creator": "Adobe InDesign 16.0 (Macintosh)",
            "producer": "Adobe PDF Library 15.0",
            "subject": null,
            "title": null,
            "pages": 342
        }
    """
    if isinstance(pdf, str):
        pdf_fp = pdf
        file_name = os.path.basename(pdf)
        print("Opening {}".format(file_name))
        with open(pdf_fp, 'rb') as pdf_file:
            pdf_obj = PdfFileReader(pdf_file)
            meta_data = __get_pdf_metadata(pdf_obj)

    elif isinstance(pdf, PdfFileReader):
        meta_data = __get_pdf_metadata(pdf)
    else:
        print("Unsupported type, accepts pdf string path or PyPDFFileReader object")
        return None

    return meta_data


def make_pages_upright(source_pdf_path, destination_pdf_dir):
    file_name = os.path.basename(source_pdf_path)
    print("Opening {}".format(file_name))

    # Creating main pdf writer
    main_pdf_writer = PdfFileWriter()

    with open(source_pdf_path, 'rb') as pdf_file:
        pdf_document = PdfFileReader(pdf_file)
        document_meta_data = get_document_info(pdf_document)
        print(json.dumps(document_meta_data, indent=4))
        num_pages = document_meta_data['pages']

        for i in range(num_pages):
            print("Processing page {}".format(i))
            current_page = pdf_document.getPage(i)

            if are_texts_upright(current_page):
                main_pdf_writer.addPage(current_page)
                continue

            current_page.rotateClockwise(90)
            if are_texts_upright(current_page):
                main_pdf_writer.addPage(current_page)
                print("Rotated CW")
                continue

            current_page.rotateCounterClockwise(180)
            if are_texts_upright(current_page):
                main_pdf_writer.addPage(current_page)
                print("Rotated CCW")
                continue

            current_page.rotateClockwise(90)
            main_pdf_writer.addPage(current_page)

        destination_pdf_fp = os.path.join(destination_pdf_dir, file_name)
        with open(destination_pdf_fp, "wb") as destination_pdf_path:
            main_pdf_writer.write(destination_pdf_path)


def are_texts_upright(current_page, num_samples=50):
    temp_file = io.BytesIO()
    temp_pdf_writer = PdfFileWriter()
    temp_pdf_writer.addPage(current_page)
    temp_pdf_writer.write(temp_file)

    with pdfplumber.open(temp_file) as pdf:
        page = pdf.pages[0]
        page_texts = page.chars
        random.shuffle(page_texts)
        random_chars = page_texts[:num_samples]
        orientations = [char["upright"] for char in random_chars]
        if len(orientations) == 0:
            return True
        percentage_upright = sum(orientations)/len(orientations)

    temp_file.close()
    return percentage_upright > 0.5


if __name__ == "__main__":
    make_pages_upright(
        r"test_pdfs\rotation\2020PTTEPAR_en.pdf", r"processed_pdf")
