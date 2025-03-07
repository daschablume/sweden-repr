from datetime import datetime
from glob import glob
import os
import time

from bs4 import BeautifulSoup
from tqdm import tqdm
import requests
import pandas as pd

DATA = '/Users/macuser/Documents/UPPSALA/thesis/data'
SPUTNIK = f'{DATA}/sputnik'
SPUTNIK_INDEX = f'{SPUTNIK}/index-pages'
SPUTNIK_LINKS = f'{SPUTNIK_INDEX}/links.csv'

NV_LINK = 'https://nv.ua/ukr/search.html?query=%D1%88%D0%B2%D0%B5%D1%86%D1%96%D1%8F&page='
NV = f'{DATA}/nv'
NV_INDEX = f'{NV}/index-pages'
NV_LINKS = f'{NV_INDEX}/links.csv'

HRO = f'{DATA}/hromadske'
HRO_INDEX = f'{HRO}/index-pages'
HRO_LINKS = f'{HRO_INDEX}/links.csv'


def get_sputnik_links():
    LINKS = []
    htmls = glob(f'{SPUTNIK_INDEX}/*.html')
    for html in htmls:
        with open(html, 'r') as file:
            page = file.read()
        soup = BeautifulSoup(page, 'html')
        articles_headers = soup.find_all("div", class_="list__content")
        links = [
            header.find("a", class_="list__title")['href'] 
            for header in articles_headers
        ]
        LINKS.extend(links)

    df = pd.DataFrame(LINKS)
    df.to_csv(f'{SPUTNIK_LINKS}', index=False, header=['link'])


def save_from_sputnik(file_path=SPUTNIK_LINKS, save_dir=SPUTNIK, delay=2):
    '''
    Iterates over a list of links and saves each article as a separate file.
    Recreates the structure of the website: each article is saved in a separate folder
    named after the article date.
    '''

    links = pd.read_csv(file_path)
    
    for link in tqdm(links['link'], desc="Downloading articles", total=len(links['link'])):
        parts = link.split('/')
        date_part = parts[-2]
        filename = parts[-1]
        
        article_dir = os.path.join(save_dir, date_part)
        os.makedirs(article_dir, exist_ok=True)
        
        response = requests.get(link)
        
        if response.status_code == 200:
            file_path = os.path.join(article_dir, filename)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(response.text)
        
        time.sleep(delay)


def get_nv_index_pages(delay=2):
    '''
    Iterate over a search query "Sweden" for 402 pages and save each index page as an html file.
    402 pages are hardcoded as the number of pages in the search query.
    Data of scraping: 2025-03-07.
    '''
    for p in tqdm(range(1, 402), desc="Downloading articles", total=402):
        page = NV_LINK + str(p)
        response = requests.get(page)

        if response.status_code == 200:
            file_path = os.path.join(NV_INDEX, f'{p}.html')
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(response.text)
        
        time.sleep(delay)


def get_nv_links():
    LINKS = []
    htmls = glob(f'{NV_INDEX}/*.html')
    for html in tqdm(htmls, desc="Extracting links", total=len(htmls)):
        with open(html, 'r') as file:
            page = file.read()
        soup = BeautifulSoup(page, 'html')
        links = [
            a_tag['href'] 
            for a_tag in soup.find_all("a", class_="row-result-body")
        ]
        LINKS.extend(links)

    df = pd.DataFrame(LINKS)
    df.to_csv(f'{NV_LINKS}', index=False, header=['link'])


def save_from_nv(file_path=NV_LINKS, save_dir=NV, delay=2):
    '''
    Iterates over a list of links and saves each article as a separate file.
    Recreates the structure of the website: each article is saved in a separate folder
    named after the article date.
    '''

    links = pd.read_csv(file_path)
    nv_basic_dir = os.path.join(save_dir, 'nv.ua')
    os.makedirs(nv_basic_dir, exist_ok=True)

    for link in tqdm(links['link'], desc="Downloading articles", total=len(links['link'])):
        parts = link.split('/')
        rubric = parts[2].split('.')[0]  # extract section of the article, like "sport"
        if rubric != 'nv':
            article_dir = os.path.join(save_dir, rubric)
            os.makedirs(article_dir, exist_ok=True)
        else:
            article_dir = nv_basic_dir
    
        filename = parts[-1]

        response = requests.get(link)
        if response.status_code == 200:
            file_path = os.path.join(article_dir, filename)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(response.text)
        
        time.sleep(delay)


def get_hro_links():
    '''
    HRO = f'{DATA}/hromadske'
    HRO_INDEX = f'{HRO}/index-pages'
    HRO_LINKS = f'{HRO_INDEX}/links.csv'
    '''
    LINKS = []
    htmls = glob(f'{HRO_INDEX}/*.html')
    for html in tqdm(htmls, desc="Extracting links", total=len(htmls)):
        with open(html, 'r') as file:
            page = file.read()
        soup = BeautifulSoup(page, 'html')
        links = [
            a_tag['href'] 
            for a_tag in soup.find_all("a", class_="c-search-item__link")
        ]
        LINKS.extend(links)

    df = pd.DataFrame(LINKS)
    df.to_csv(f'{HRO_LINKS}', index=False, header=['link'])


def save_from_hro(file_path=HRO_LINKS, save_dir=HRO, delay=2):
    '''
    Iterates over a list of links and saves each article as a separate file.
    Recreates the structure of the website: each article is saved in a separate folder
    named after the article date.
    '''

    links = pd.read_csv(file_path)

    for ind, row in tqdm(links.iterrows(), desc="Downloading articles", total=len(links)):
        link = row['link']
        parts = link.split('/')
        filename = parts[-1]
        try:
            response = requests.get(link)        
            if response.status_code == 200:
                file_path = os.path.join(save_dir, filename)
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(response.text)
        
            time.sleep(delay)
        except requests.exceptions.TooManyRedirects:
            print(f"Skipping {ind} due to TooManyRedirects, {link}")
            continue
