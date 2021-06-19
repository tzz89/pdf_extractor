from PyPDF2 import PdfFileReader, PdfFileWriter
# import pdfminer.six
import pdfplumber
import os
import json
import random
import io
import glob

def __get_pagelabel_num_child(root):
    """recursively find the num child

    Args:
        root ([]): could be anything
    """
    # print(root)
    if not (isinstance(root, dict) or isinstance(root, list)):
        return None
    if isinstance(root, dict):
        childrens = root.keys()
             
        # print(childrens)
        if "/Nums" in childrens:
            return root['/Nums']

        for children in childrens:
            result = __get_pagelabel_num_child(root[children])
            if result is not None:
                return result

    else:
        for list_item in root:
            try:
                new_root = list_item.getObject()
                result = __get_pagelabel_num_child(new_root)
                if result is not None:
                    return result
            except:
                continue
            

    return None

def __get_pdf_metadata(pdf_obj):
    """This Function takes in a PdfFileReader object and returns document metadata

    Args:
        pdf_obj ([PdfWriteObj]): [description]

    Returns: diction of
         {
            "author": null,
            "creator": "Adobe InDesign 16.0 (Macintosh)",
            "producer": "Adobe PDF Library 15.0",
            "subject": null,
            "title": null,
            "pages": 342,
            "page_offset": []
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
    pdf_metadata_dict['page_offset'] = None 

    pdf_meta_root = pdf_obj.trailer["/Root"]
    if "/PageLabels" in pdf_meta_root.keys():
        offset_labels = []
        page_labels = __get_pagelabel_num_child(pdf_meta_root['/PageLabels'])
        if page_labels is not None:
            for page_label in page_labels:
                if isinstance(page_label, int):
                    offset_labels.append(page_label)
                else:
                    offset_labels.append(page_label.getObject())
            pdf_metadata_dict['page_offset'] = offset_labels

    return pdf_metadata_dict

def get_document_info(pdf):
    """This method takes in either the pdf path of type string or a PdfFileReader Oject and returns
       the pdf meta data

    Args:
        pdf ([string/PyPDFFileReader]): can be a string path or PDFReader

    Returns: dictionary
        {
            "author": null,
            "creator": "Adobe InDesign 16.0 (Macintosh)",
            "producer": "Adobe PDF Library 15.0",
            "subject": null,
            "title": null,
            "pages": 342
            "page_offset": None
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

            if __are_texts_upright(current_page):
                main_pdf_writer.addPage(current_page)
                continue

            current_page.rotateClockwise(90)
            if __are_texts_upright(current_page):
                main_pdf_writer.addPage(current_page)
                print("Rotated CW")
                continue

            current_page.rotateCounterClockwise(180)
            if __are_texts_upright(current_page):
                main_pdf_writer.addPage(current_page)
                print("Rotated CCW")
                continue

            current_page.rotateClockwise(90)
            main_pdf_writer.addPage(current_page)

        destination_pdf_fp = os.path.join(destination_pdf_dir, file_name)
        with open(destination_pdf_fp, "wb") as destination_pdf_path:
            main_pdf_writer.write(destination_pdf_path)

def __are_texts_upright(current_page, num_samples=50):
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

def create_single_page_pdfs(pdf_path, pages, pdf_destination_folder):
    """
    This function takes in a pdf_path, a page number or a list of page_numbers. For each of the page, create single page pdf
    and save it in the destination folder

    Sample usage:
    create_single_page_pdfs(r"test_pdfs\table_extraction\2003_EDION_AR.pdf", [2,4,8,10,19,21,22,26], r"test_pdfs\full_page_layout\table_extraction")
    output
    ['2003_EDION_AR.pdf_page_10.pdf', '2003_EDION_AR.pdf_page_19.pdf', '2003_EDION_AR.pdf_page_2.pdf', '2003_EDION_AR.pdf_page_21.pdf', 
    '2003_EDION_AR.pdf_page_22.pdf', '2003_EDION_AR.pdf_page_26.pdf', '2003_EDION_AR.pdf_page_4.pdf', '2003_EDION_AR.pdf_page_8.pdf']

    Args:
        pdf_path ([string]): the file path to the source pdf file to extract the pages from
        pages ([int/list of ints]): pages to create single page pdf
        pdf_destination_folder ([string]): destination folder 
    """
    if not (isinstance(pages, int) or isinstance(pages, list)):
        print("Please provide pages as a single int or a list of intergers that is more than 0")
        return

    if isinstance(pages, int):
        pages = [pages] 

    if len(pages) < 1:
        print("list of pages is empty")
        return
    
    for page in pages:
        if not (isinstance(page, int) and page > 0):
            print("Please provide pages as a single int or a list of intergers that is more than 0")
            return

    #create destination folder if not exist
    os.makedirs(pdf_destination_folder, exist_ok=True)

    #create pdf reader 

    with open(pdf_path, "rb") as f:
        pdf_document = PdfFileReader(f)
        pdf_max_pages = pdf_document.getNumPages()

       
        #create single page page for each pdf
        for page in pages:
            if page > pdf_max_pages:
                print("input page exceed document max page number")
                continue

            pdf_page = pdf_document.getPage(page-1)
            pdf_writer = PdfFileWriter()
            pdf_writer.addPage(pdf_page)
            destination_file_name = os.path.basename(pdf_path) + "_page_{:04d}".format(page)+".pdf"
            destination_file_path = os.path.join(pdf_destination_folder, destination_file_name)
            
            with open(destination_file_path, 'wb') as destination_f:
                pdf_writer.write(destination_f)

def decrypt_pdf_document(pdf_)



if __name__ == "__main__":
    # make_pages_upright(
    #     r"test_pdfs\rotation\2020PTTEPAR_en.pdf", r"processed_pdf")


    # create_single_page_pdfs(r"test_pdfs\table_extraction\2020 Origin Annual Report online version.pdf",
    #                          [1,2,3,4,5,6], r"test_pdfs\full_page_layout\table_extraction")

 
    # create_single_page_pdfs(r"test_pdfs\table_extraction\2003_EDION_AR.pdf",
    #                          [2], r"test_pdfs\full_page_layout\table_extraction")

    # pdf_with_offset = glob.glob(r"test_pdfs\page_number_offset\have_offset\*.pdf")
    # pdf_without_offset =glob.glob(r"test_pdfs\page_number_offset\no_offset\*.pdf")
    
    # for pdf in pdf_without_offset:

    #     document_metadata = get_document_info(pdf)
    #     print(document_metadata['page_offset'])
    #     print()
    print()
   