from abc import ABC, abstractmethod
from datetime import datetime
import re

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
        """
        Parses a date string to a unified format.
        The input data format must be defined in the child class.
        """
        try:
            parsed = datetime.strptime(
                date, self.date_str_format
            ).strftime(self.format_str)
            return parsed
        except ValueError:
            return None
    
    def make_soup(self, file_path):
        """Reads a file and returns a BeautifulSoup object."""
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
        article_body = self.find_article_body(soup)
        if not article_body:
            return None
        
        title = self.find_title(soup)
        parsed_date = self.parse_date(self.find_date(soup))
        abstract = self.find_abstract(soup)
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

    def _remove_html_tags(self, text: str) -> str:
        """
        Removes HTML tags from a str of text.
        It can be done with just BeautifulSoup, but BS deletes tags and merges 
        the text. So "he crushed into a<br>tree" => "he crushed into atree".
        This leads to errors in the future processing of the text.
        With regex, we get "he crushed into a tree". 

        Should be used in find_article_body() method.
        """
        cleaned_text = re.sub(r'<[^>]+>', ' ', text)       
        cleaned_text = cleaned_text.replace('\xa0', ' ').replace('<0xa0>', ' ') 
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
        cleaned_text = cleaned_text.replace('\xa0', ' ').replace('<0xa0>', ' ')
        return cleaned_text