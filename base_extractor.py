from abc import ABC, abstractmethod
from datetime import datetime

from bs4 import BeautifulSoup

UNIFIED_PARSE_DATE = '%Y-%m-%d'


class BaseExtractor(ABC):
    def __init__(self):
        self.format_str = UNIFIED_PARSE_DATE
        self.date_str_format = None
    
    def normalize_path(self, file_path):
        if file_path.startswith('../data/'):
            return file_path.replace('../data/', '')
        return file_path
    
    def parse_date(self, date):
        try:
            parsed = datetime.strptime(
                date, self.date_str_format
            ).strftime(self.format_str)
            return parsed
        except ValueError:
            return None
    
    def make_soup(self, file_path):
        try:
            with open(file_path, encoding='utf-8') as fp:
                html = fp.read()
            return BeautifulSoup(html, "html.parser")
        except FileNotFoundError:
            print(f"File not found: {file_path}")
            return None
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            return None
    
    def extract(self, file_path):
        """Extract article information from the HTML."""
        soup = self.make_soup(file_path)
        
        title = self.find_title(soup)
        parsed_date = self.find_date(soup)
        abstract = self.find_abstract(soup)
        article_body = self.find_article_body(soup)
        keywords = self.find_keywords(soup)
        genre = self.find_genre(soup)
        author = self.find_author(soup)

        return {
            "title": title,
            "date_published": parsed_date,
            "abstract": abstract,
            "article_body": article_body,
            "keywords": keywords,
            "genre": genre,
            "author": author,
            "file_path": self.normalize_path(file_path),
        }  
    
    @abstractmethod
    def find_title(self, soup) -> str:
        pass
    
    @abstractmethod
    def find_date(self, soup) -> str:
        pass
    
    @abstractmethod
    def find_abstract(self, soup) -> str:
        pass
    
    @abstractmethod
    def find_article_body(self, soup) -> str:
        pass
    
    @abstractmethod
    def find_keywords(self, soup) -> list:
        pass
    
    @abstractmethod
    def find_genre(self, soup) -> str:
        pass
    
    @abstractmethod
    def find_author(self, soup) -> str:
        pass