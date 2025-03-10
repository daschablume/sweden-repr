from glob import glob
import os
import random
import sys
import time

from bs4 import BeautifulSoup
from tqdm import tqdm
import requests
import pandas as pd

from links_parser import (
    HromadskeParser, NvParser, SputnikParser,
    UkrinformParser, EurActivParser
)

DATA = '/Users/macuser/Documents/UPPSALA/thesis/data'

SOURCES_CONFIG = {
    'hromadske': HromadskeParser(),
    'nv': NvParser(
        index_page_link='https://nv.ua/ukr/search.html?query=%D1%88%D0%B2%D0%B5%D1%86%D1%96%D1%8F&page={}',
        page_num=402
    ),
    'sputnik': SputnikParser(),
    'ukrinform': UkrinformParser(
        index_page_link='https://www.ukrinform.ua/search-YToxOntzOjU6InF1ZXJ5IjtzOjEyOiLRiNCy0LXRhtGW0Y8iO30?page={}',
        page_num=84
    ),
    'euractiv': EurActivParser(
        index_page_link='https://www.euractiv.com/page/{}/?s=sweden',
        page_num=283
    ),
}


class SimpleScraper:
    def __init__(self, source, data_dir=DATA, delay=2, random_delay_range=(0, 2)):
        if source not in SOURCES_CONFIG:
            raise ValueError(
                f'Unsupported source: {source}. '
                f'Available sources: {", ".join(SOURCES_CONFIG.keys())}'
            )
        self.source = source
        self.delay = delay
        self.parser = SOURCES_CONFIG[source]

        self.data_dir = data_dir
        self.source_dir = f'{data_dir}/{source}'
        self.index_dir = f'{self.source_dir}/index-pages'
        os.makedirs(self.index_dir, exist_ok=True)
        self.links_file = f'{self.index_dir}/links.csv'
        
        self.links = self.get_links()
        # (0, 2) is enough for some websites, while for Ukrinform, use (2, 5)
        self.random_delay_range = random_delay_range

    def get_links(self):
        if os.path.exists(self.links_file):
            return pd.read_csv(self.links_file)
        return None

    def get_links_from_index_pages(self):
        all_links = []
        htmls = glob(f'{self.index_dir}/*.html')
        for html in tqdm(htmls, desc="Extracting links", total=len(htmls)):
            links = self.parser.parse_tag(html)
            
            all_links.extend(links)

        df = pd.DataFrame(all_links, columns=['link'])
        df.to_csv(f'{self.links_file}', index=False)

        self.links = df
    
    def scrape_articles(self):
        if self.links is None:
            self.get_links_from_index_pages()
        if self.links is None:
            raise ValueError('No links found')

        session = requests.Session()
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36',
            'Referer': 'https://www.ukrinform.ua/'
        }
        session.headers.update(headers)

        for ind, row in tqdm(self.links.iterrows(), total=len(self.links), desc="Downloading articles"):
            link = row['link']
            try:
                filename = self.parser.get_file_dest(link, self.source_dir)
            except Exception as e:
                print(f"Error getting file destination for {link}: {e}")
                continue

            if os.path.exists(filename) and os.path.getsize(filename) > 0:
                print(f"Skipping already downloaded: {filename}")
                continue

            retries = 3
            delay = self.delay
            for attempt in range(retries):
                try:
                    response = session.get(link, timeout=10)
                    if response.status_code == 200:
                        with open(filename, "w", encoding="utf-8") as f:
                            f.write(response.text)
                        break
                    else:
                        print(f"Attempt {attempt+1}: Failed {response.status_code} for {link}")

                except requests.RequestException as e:
                    print(f"Attempt {attempt+1}: Error {e} for {link}")

                time.sleep(delay + random.uniform(5, 15))  # Increase randomness
                delay *= 2  # Exponential backoff
            else:
                print(f"Skipping {ind}, {link} after {retries} attempts")
            
            time.sleep(delay + random.uniform(*self.random_delay_range))

    def get_index_pages(self):
        if self.parser.index_page_link is None:
            raise ValueError('Index pages link is not provided')
        
        page_num = self.parser.page_num
        
        session = requests.Session()
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36',
            'Referer': 'https://www.ukrinform.ua/'
        }
        session.headers.update(headers)
        
        for p in tqdm(range(1, page_num), desc="Downloading index pages", total=page_num-1):
            page = self.parser.index_page_link.format(p)
            response = session.get(page, timeout=10)

            if response.status_code == 200:
                file_path = os.path.join(self.index_dir, f'{p}.html')
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(response.text)
            
            # randomise delay to avoid being blocked
            time.sleep(self.delay + random.uniform(0, 2))
    
    # for EurActiv:
    #
    '''
    www.euractiv.com/section/health-consumers/opinion/type-1-diabetes-can-be-fast-but-we-can-be-faster-a-call-to-boost-early-detection/index.html
    filename = parts[-2]
    section = parts[-3] # opinion or news
    '''


if __name__ == '__main__':
    scraper = SimpleScraper('euractiv', delay=2)
    #scraper.get_index_pages()
    scraper.get_links_from_index_pages()