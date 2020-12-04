import re
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from io import StringIO


def convert_pdf_to_txt(path):
    rsrcmgr = PDFResourceManager()
    retstr = StringIO()
    codec = 'ascii'  # 'utf-8'
    laparams = LAParams()
    device = TextConverter(rsrcmgr, retstr,
                           codec=codec,
                           laparams=laparams)
    fp = open(path, 'rb') # binary
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    password = ""
    maxpages = 0
    caching = True
    pagenos = set()
    for page in PDFPage.get_pages(fp, pagenos, maxpages=maxpages, password=password, caching=caching, check_extractable=True):
        interpreter.process_page(page)
    text = retstr.getvalue()
    fp.close()
    device.close()
    retstr.close()
    return text


def clean_up_first_page_and_reference(text):
    paper_body_start = 0
    search_result = re.search(r'JSTOR\sis\sa\snot-for-profit\sservice', text)
    if search_result:
        search_result_new_page = re.search(r'\x0c', text)
        if search_result_new_page.start() - search_result.start() < 1000:
            paper_body_start = search_result_new_page.end()
    references_startPoint = 0
    regex_references = re.compile(r'^\s*References\s*$', re.MULTILINE | re.UNICODE | re.IGNORECASE)
    result_references = regex_references.search(text, paper_body_start)
    if result_references:
        references_startPoint = result_references.start()
    else:
        regex_references_2 = re.compile(r'\fREFERENCES', re.MULTILINE | re.UNICODE)
        result_references_2 = regex_references_2.search(text, paper_body_start)
        if result_references_2:
            references_startPoint = result_references_2.start()
        else:
            regex_references_2 = re.compile(r'REFERENCES', re.MULTILINE | re.UNICODE)
            result_references_2 = regex_references_2.search(text, paper_body_start)
            if result_references_2:
                references_startPoint = result_references_2.start()
            else:
                regex_references_2 = re.compile(r'REEERENCES', re.MULTILINE | re.UNICODE)
                result_references_2 = regex_references_2.search(text, paper_body_start)
                if result_references_2:
                    references_startPoint = result_references_2.start()
                else:
                    # print string_for_error
                    print('cannot find References')
                    return text[paper_body_start:]
    return text[paper_body_start: references_startPoint]


def remove_header_and_footer(content):
    if not content:
        return content
    content = re.sub(r'\-\s*\n\s*', '', content, flags=re.MULTILINE | re.UNICODE | re.IGNORECASE)

    first_words_of_new_page = re.compile('This\s*content\s*downloaded.*\n*.*JSTOR.*\n*.*\n*\x0c',
                                         re.IGNORECASE | re.UNICODE | re.MULTILINE)
    result_first_words_of_new_page = first_words_of_new_page.findall(content)
    max_len = 0
    for v in result_first_words_of_new_page:
        max_len = max(max_len, len(v))
    if max_len > 350:
        print('find too long string')
        print(result_first_words_of_new_page)
    content1 = first_words_of_new_page.sub('\n\n\x0c', content)
    return content1



def clean_up(path):
    t = convert_pdf_to_txt(path)
    t1 = clean_up_first_page_and_reference(t)
    if len(t1) <= 0 :
        print('error')
    t2 = remove_header_and_footer(t1)
    if len(t2) <= 0 :
        print('error')
    cleaned_text = remove_header_and_footer(t2)
    return cleaned_text


# if __name__ == "__main__":
#     path = "../../papers/21945227.pdf"
#     cleaned_text = clean_up(path)
#     print(cleaned_text)
