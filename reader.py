from pypdf import PdfReader

def split_text(text: str, chunk_size: int = 256, chunk_overlap: int = 128) -> list[str]:
    if chunk_size <= 0:
        raise Exception('chunk_size debe estar en el rango (0, infty)')
    if chunk_overlap > chunk_size or chunk_overlap <= 0:
        raise Exception('chunk_overlap debe estar en el rango (0, chunk_size)')
    current, next, split = '', '', []
    m, n = 0, chunk_overlap - chunk_size 
    for word in text.split():
        k = len(word) + 1
        if m < chunk_size:
            current += f'{word} '
            m += k
        else:
            split.append(current.strip())
            current = f'{word} '
            m = k 
        if n < chunk_size: 
            n += k 
            if n > 0:
                next += f'{word} '
        else:
            split.append(next.strip())
            next = f'{word} '
            n = k
    if split[-1] != current:
        split.append(current.strip())
    return split

def extract_pdf_text(pdf_obj, init_page: int | None = None, last_page: int | None = None):
    text = ''
    pages = pdf_obj.pages
    if last_page:
        pages = pages[:last_page]
    if init_page:
        pages =  pages[init_page:]
    for page in pages:
        text += f'{page.extract_text()} '
    return text.strip()

def process_pdf(file_obj, init_page: int | None = None, last_page: int | None = None, chunk_size: int = 1024, chunk_overlap: int = 512) -> list[str]:
    pdf = PdfReader(file_obj)
    text = extract_pdf_text(pdf, init_page, last_page)
    if text:
        split = split_text(text, chunk_size, chunk_overlap)
        return split
    else:
        return []
