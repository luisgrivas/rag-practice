import streamlit as st
import chromadb
from scrap import download_pdf, find_pdf_links
from reader import process_pdf
from vectordb import search
from llm import transform_query, answer_questions, generate_questions


chroma_client = chromadb.PersistentClient('data')

def set_ss(key: str, val: str | int | list | dict | None = None):
    st.session_state[key] = val


def copy_ss(key1: str, key2: str):
    set_ss(key2, st.session_state.get(key1))


def search_callback(query: str):
    st.toast(':blue[Searching related books...]', icon='🧠')
    transformed_query, _ = transform_query(query)
    _, books = search(transformed_query)
    books = {book.get('id', ''): book for book in books}
    set_ss('_query_results', books)


def init_app(init_data: list):
    for k, v in init_data: 
        if k not in st.session_state:
            set_ss(k, v)

def reset_app():
    for k, v in st.session_state.items():
        if isinstance(k, str) and k.startswith('_'):
            if isinstance(v, (list, dict)):
                set_ss(k, type(v)())
            elif isinstance(v, bool):
                set_ss(k, False)
            else:
                set_ss(k)


def process_file(id, file_obj):
    st.toast(':blue[Processing book...]', icon='🧠')
    split = process_pdf(file_obj, init_page=15, last_page=100, chunk_size=1024, chunk_overlap=512, threshold=0.5)
    excerpts = chroma_client.get_collection('excerpts')
    ids = [f'id{id}_{i}' for i in range(len(split))]
    metadatas = [{'book_id': id} for _ in range(len(split))]
                        
    books = chroma_client.get_collection('books')
    try:
        excerpts.add(ids=ids, metadatas=metadatas, documents=split)
    except:
        books.update(ids=id, metadatas={'active': False})
        st.session_state['_query_results'][id]['active'] = False
        st.toast(':red[This book cannot be processed]', icon='🚫')
        set_ss(f'_check_{id}', False)
    else:
        st.toast(':green[The book has been processed successfully]', icon='✅')
        books.update(ids=id, metadatas={'processed': True})
        st.session_state['_query_results'][id]['processed'] = True


def extract_excerpts(query: str, ids: list):
    excerpts, _ = search(
        query=query,
        filters={'book_id': {'$in': ids}},
        collection_name='excerpts'
    )
    return excerpts


def search_pdf(id: int, url: str):
    st.toast(':blue[Downloading book...]', icon='🧠')
    pdfs = find_pdf_links(url, 2)
    st.session_state[f'_searched_{id}'] = True
    if pdfs:
        pdf_objs = [download_pdf(pdf) for pdf in pdfs]
        pdf_objs = [obj for obj in pdf_objs if obj]
        if pdf_objs:
            pdf = max(pdf_objs, key=lambda p: p.getbuffer().nbytes)
            st.toast(':green[The book has been successfully downloaded]', icon='✅')
            process_file(id, pdf)
        else:
            st.toast(':red[The book could not be automatically downloaded]', icon='🚫')
    else:
        st.toast(':red[The book could not be automatically downloaded]', icon='🚫')


def generate_answer(query: str, ids: list):
    st.toast(':blue[Extracting text...]', icon='🧠')
    questions = generate_questions(query)
    excerpts = extract_excerpts(questions, ids)
    excerpts = '\n\n'.join(f'Excerpt {i + 1}:\n{e}' for i, e in enumerate(excerpts))
    st.toast(':blue[Generating answer...]', icon='🧠')
    answer = answer_questions(questions, excerpts)
    st.session_state['_answer'] = answer
