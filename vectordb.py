import chromadb
import json
import os
import re
import requests

from tqdm import tqdm
from termcolor import cprint

# opentextbooks url
URL = 'https://open.umn.edu/opentextbooks/textbooks.json'
chroma_client = chromadb.PersistentClient('data')


def get_books() -> list[dict]:
    next, iter, n = URL, 0, 165 # al parecer son 165 paginas
    data = []
    with tqdm(total=n) as pbar:
        while next and iter < n:
            r = requests.get(next).json()
            data += r.get('data', [])
            iter += 1
            next = r.get('links', {}).get('next')
            pbar.update(1)
    return data


def process_books(books: list[dict]) -> list[dict]:
    arr, i = [], 1
    for book in tqdm(books):
        pdf_link = [
            el.get('url', '') for el in book.get('formats', []) 
            if el.get('format', '').lower() == 'pdf'
        ]
        if pdf_link and book.get('language', '').lower() == 'eng':
            clean_book = {
                'id': f'id{i}',
                'title': book.get('title', ''),
                'language': book.get('language', ''),
                'description': book.get('description', ''),
                'processed': False,
                'active': True
            }
            authors = [
                re.sub(r'\bNone\b|\s{2,}', '', f'{el.get("first_name", "")} {el.get("middle_name", "")} {el.get("last_name", "")}').strip()
                for el in book.get('contributors', []) if el.get('contribution', '').lower() == 'author'
            ]
            subjects = '; '.join(s.get('name', '').lower() for s in book.get('subjects', []))
            clean_book['authors'] = '; '.join(authors)
            clean_book['link'] = pdf_link[0]
            clean_book['subjects'] = subjects 
            arr.append(clean_book)
            i += 1
    return arr

def search(query: str, filters: dict | None = None, n_results: int = 10, collection_name: str = 'books') -> list:
    collection = chroma_client.get_collection(name=collection_name)
    input = {'query_texts': query, 'n_results': n_results, 'where': {'active': True}}
    if filters:
        input['where'] = input.get('where', {}).update(filters)
    query_result = collection.query(**input)
    if (metadatas := query_result.get('metadatas')) and (documents := query_result.get('documents')):
        return [documents[0], metadatas[0]]
    else:
        return []

def main():
    if not os.path.exists('data'):
        cprint('Creating data directory...',  'blue')
        os.mkdir('data')
        cprint('Done.', 'blue')
    if not os.path.exists('data/books_raw.json'):
        cprint('Creating book file...', 'blue')
        cprint('Downloading books from Opentextbooks.', 'green')
        books = get_books()
        cprint('Saving books (raw) as data/books_raw.json', 'green')
        with open('data/books_raw.json', 'w') as f:
            json.dump(books, f, indent=4)
        cprint('Done.')
    else:
        cprint('Reading books file...', 'blue')
        with open('data/books_raw.json', 'r') as f:
            books = json.load(f)
        cprint('Done.')
    if not os.path.exists('data/books.json'):
        cprint('Processing books.', 'blue')
        books = process_books(books)
        cprint('Saving processed books as data/books.json', 'green')
        with open('data/books.json', 'w') as f:
            json.dump(books, f, indent=4)
        cprint('Done.', 'blue')
    else:
        cprint('Reading (processed) books file...', 'blue')
        with open('data/books.json', 'r') as f:
            books = json.load(f)
        cprint('Done.', 'blue')
    collections = [c.name for c in chroma_client.list_collections()]
    choice = 'x'
    msg = 'Creating'
    if 'excerpts' not in collections:
        cprint('Creating "excerpts" collection.', 'blue')
        chroma_client.create_collection('excerpts')
        cprint('Done.', 'blue')
    if 'books' in collections:
        msg = 'Updating'
        while choice not in ['u', 'a']:
            choice = input('The "books" collection already exists. Choose an option\nu (update) / a (abort). ')
    if choice in ['u', 'x']:
        cprint(f'{msg} vector database.', 'blue')
        documents = [f'{book.get("title", "")}: {book.get("description", "")}' for book in books]
        ids = [book.get('id') for book in books]
        if None in ids:
            ids = [f'id{i}' for i in range(len(books))]
        cprint(f'Saving {len(books)} books.', 'green')
        collection = chroma_client.get_or_create_collection('books')
        collection.upsert(ids=ids, metadatas=books, documents=documents)
        assert collection.count() == len(books)
        cprint('Done.', 'green')
    else:
        cprint('Script aborted.', 'red')


if __name__ == '__main__':
    main()
