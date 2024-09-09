#!/bin/bash
python3 vectordb.py
python3 -m nltk.downloader words names
streamlit run app.py
