import streamlit as st
import chromadb
from scrap import download_pdf, find_pdf_links
from reader import process_pdf
from vectordb import search
from llm import transform_query


chroma_client = chromadb.PersistentClient('data')

def set_ss(key: str, val: str | int | list | dict | None = None):
    st.session_state[key] = val


def copy_ss(key1: str, key2: str):
    set_ss(key2, st.session_state.get(key1))


def search_callback(query: str):
    st.toast(':blue[Buscando libros relacionados a la busqueda..]', icon='🧠')
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

def process_upload_file(id, file_obj):
    st.toast(':blue[Procesando el libro...]', icon='🧠')
    split = process_pdf(file_obj, init_page=15, last_page=100, chunk_size=10, chunk_overlap=5)
    excerpts = chroma_client.get_collection('excerpts')
    ids = [f'id{id}_{i}' for i in range(len(split))]
    metadatas = [{'book_id': id} for _ in range(len(split))]
    books = chroma_client.get_collection('books')
    try:
        excerpts.add(ids=ids, metadatas=metadatas, documents=split)
    except:
        books.update(ids=id, metadatas={'active': False})
        st.session_state['_query_results'][id]['active'] = False
        st.toast(':red[Este libro no puede ser procesado]', icon='🚫')
        set_ss(f'_check_{id}', False)
    else:
        st.toast(':green[El libro fue procesado con exito]', icon='✅')
        books.update(ids=id, metadatas={'processed': True})
        st.session_state['_query_results'][id]['processed'] = True


def extract_excerpts(query: str, ids: list):
    excerpts, _ = search(
        query=query,
        filters={'book_id': {'$in': ids}},
        collection_name='excerpts'
    )
    st.session_state['_excerpts'] = excerpts


def search_pdf(url: str):
    st.toast(':blue[Descargando libro...]', icon='🧠')
    pdfs = find_pdf_links(url, 2)
    st.info(pdfs)
    if pdfs:
        pdf_objs = [download_pdf(pdf) for pdf in pdfs]
        pdf_objs = [obj for obj in pdf_objs if obj]
        pdf = max(pdf_objs, key=lambda p: p.getbuffer().nbytes)
        st.toast(':green[El libro fue descargado con exito]', icon='✅')
        st.session_state['_']
    else:
        st.toast(':red[El libro no pudo ser descargado automaticamente]', icon='🚫')
