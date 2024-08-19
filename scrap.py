import requests
import validators
from io import BytesIO
from bs4 import BeautifulSoup
from urllib.parse import urlparse


def find_pdf_links(url: str, depth: int = 1) -> list[str]:
    if not validators.url(url) or depth < 1:
        return []
    parsed_url = urlparse(url)
    if parsed_url.path.endswith('pdf'):
        return [url]
    r = requests.get(url)
    if r.ok:
        if 'pdf' in (content_type := r.headers.get('content-type', '')):
            return [url]
        elif 'html' in content_type:
            arr = []
            soup = BeautifulSoup(r.content, 'html.parser')
            for link in soup.find_all('a'):
                parsed_url = link.get('href', '')
                arr += find_pdf_links(parsed_url, depth - 1)
            return arr
    return []
        

def download_pdf(url: str):
    r = requests.get(url)
    if r.ok and r.headers.get('content-type') == 'application/pdf':
        return BytesIO(r.content)
    else:
        return
