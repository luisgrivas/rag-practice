from pypdf import PdfReader
from nltk.corpus import words


vocabulary = set((word.lower() for word in words.words('en')))


def split_text(text: str, chunk_size: int = 256, chunk_overlap: int = 128) -> list[str]:
    if chunk_size <= 0:
        raise Exception('chunk_size must be in the range (0, infty)')
    if chunk_overlap > chunk_size or chunk_overlap <= 0:
        raise Exception('chunk_overlap must be in the range (0, chunk_size)')
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


def words_in_vocabulary_ratio(text: str) -> float:
    counter, length = 0, 0 #pretty naive function
    for word in text.split(): 
        if word.isalpha():
            if word.lower() in vocabulary:
                counter += 1
            length += 1
    return counter / max(length, 1) #prevents division by zero


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


def process_pdf(file_obj, init_page: int | None = None, last_page: int | None = None, chunk_size: int = 1024, chunk_overlap: int = 512, threshold: float = 1.0) -> list[str]:
    pdf = PdfReader(file_obj)
    text = extract_pdf_text(pdf, init_page, last_page)
    if text:
        split = split_text(text, chunk_size, chunk_overlap)
        if threshold < 1.0:
            m = len(split)
            split = [chunk for chunk in split if words_in_vocabulary_ratio(chunk) > threshold ]
            print(f'Discarded chunks: {m - len(split)}')
        return split
    else:
        return []
