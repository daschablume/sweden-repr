from glob import glob
import os
import time

from bs4 import BeautifulSoup
from tqdm import tqdm
import requests
import pandas as pd

DATA = '/Users/macuser/Documents/UPPSALA/thesis/data'


class SimpleScraper:
    source_type2tag_parse = {
        'hromadske': 
            {'parse_tag_func': '_parse_link_tag_hromadske',
             'dest_parse_func': '_get_file_dest_hromadske',
             }, 
        'nv' : {
            'parse_tag_func': '_parse_link_tag_nv',
             'dest_parse_func': '_get_file_dest_nv',
        },
        'sputnik': {
            'parse_tag_func': '_parse_link_tag_sputnik',
             'dest_parse_func': '_get_file_dest_sputnik',     
        }, 
    }

    def __init__(self, source, data_dir=DATA, delay=2):
        '''
        Since each source has its own layout of HTML but the whole process is the same,
        we can use the same class for all sources.
        Each class has its own functions to parse tags (self.parse_tag)
        and get file destination (self.get_file_dest), based on the source.
        File destinations varies only because I want to preserve partially
        the structure of the website. For example, Sputnik has an easily extracted data
        while NV rubrics which can also be used for analysis maybe.
        '''
        if source not in self.source_type2tag_parse:
            raise ValueError(f'Unknown source: {source}')
        self.source = source

        self.delay = delay

        funcs = self.source_type2tag_parse[source]
        self.parse_tag = getattr(self, funcs['parse_tag_func'])
        self.get_file_dest = getattr(self, funcs['dest_parse_func'])

        self.data_dir = data_dir
        self.source_dir = f'{data_dir}/{source}'
        self.index_dir = f'{self.source_dir}/index-pages'
        self.links_file = f'{self.index_dir}/links.csv'

        if source == 'nv':
            self.nv_dirs = {}
            self.nv_basic_dir = os.path.join(self.source_dir, 'nv.ua')
            os.makedirs(self.nv_basic_dir, exist_ok=True)

            self.index_pages_link = 'https://nv.ua/ukr/search.html?query=%D1%88%D0%B2%D0%B5%D1%86%D1%96%D1%8F&page='
        
        self.links = self.get_links()

    def get_links(self):
        if os.path.exists(self.links_file):
            return pd.read_csv(self.links_file)
        return None

    def get_links_from_index_pages(self):
        all_links = []
        htmls = glob(f'{self.index_dir}/*.html')
        for html in tqdm(htmls, desc="Extracting links", total=len(htmls)):
            with open(html, 'r') as file:
                page = file.read()
            soup = BeautifulSoup(page, 'html')
            links = self.parse_tag(soup)

            all_links.extend(links)

        df = pd.DataFrame(all_links, columns=['link'])
        df.to_csv(f'{self.links_file}', index=False)

        self.links = df
    
    def scrape_articles(self):
        if self.links is None:
            self.get_links_from_index_pages()
            self.links = self.get_links()

        if self.links is None:
            raise ValueError('No links found')

        for ind, row in tqdm(
            self.links.iterrows(), desc="Downloading articles", total=len(self.links)
        ):
            link = row['link']
            parts = link.split('/')
            dest_dir = self.get_file_dest(parts)
            filename = parts[-1]
            try:
                response = requests.get(link)        
                if response.status_code == 200:
                    file_path = os.path.join(dest_dir, filename)
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(response.text)
            
                time.sleep(self.delay)
            except requests.exceptions.TooManyRedirects:
                print(f"Skipping {ind} due to TooManyRedirects, {link}")
                continue
    
    def get_nv_index_pages(self, page_num=402):
        '''
        Iterate over a search query "Sweden" for 402 pages and save each index page as an html file.
        402 pages are hardcoded as the number of pages in the search query.
        Data of scraping: 2025-03-07.
        '''
        for p in tqdm(range(1, page_num), desc="Downloading articles", total=page_num):
            page = self.nv_index_pages_link + str(p)
            response = requests.get(page)

            if response.status_code == 200:
                file_path = os.path.join(self.index_dir, f'{p}.html')
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(response.text)
            
            time.sleep(self.delay)

    def _parse_link_tag_hromadske(self, soup):
        return  [
            a_tag['href'] 
            for a_tag in soup.find_all("a", class_="c-search-item__link")
        ]

    def _parse_link_tag_nv(self, soup):
        return [
            a_tag['href'] 
            for a_tag in soup.find_all("a", class_="row-result-body")
        ]
    
    def _parse_link_tag_sputnik(self, soup):
        return [
            header.find("a", class_="list__title")['href'] 
            for header in soup.find_all("div", class_="list__content")
        ]

    def _get_file_dest_hromadske(self, parts):
        return self.source_dir

    def _get_file_dest_nv(self, parts):
        '''
        If a link looks like sport.nv.ua/<...>, then the article is saved in the
        sport folder. If it looks like nv.ua/<...>, then the article is saved in the nv.ua folder.
        '''
        rubric = parts[2].split('.')[0]
        if rubric != 'nv':
            # Check if we've already created this directory
            if rubric not in self.nv_dirs:
                article_dir = os.path.join(self.source_dir, rubric)
                os.makedirs(article_dir, exist_ok=True)
                self.nv_dirs[rubric] = article_dir
            return self.nv_dirs[rubric]
        else:
            return self.nv_basic_dir
    
    def _get_file_dest_sputnik(self, parts):
        '''
        Save each article in a correspondent folder in the format yyyymmdd.
        '''
        date_part = parts[-2]
        article_dir = os.path.join(self.source_dir, date_part)
        os.makedirs(article_dir, exist_ok=True)
        
        return article_dir
