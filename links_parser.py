import os

from bs4 import BeautifulSoup


class SourceParser:
    def __init__(self, index_page_link=None, page_num=None):
        self.index_page_link = index_page_link
        self.page_num = page_num
    
    def make_soup(self, html_file):
        '''
        Creates a BeautifulSoup object from an html file.
        '''
        with open(html_file, 'r') as file:
            page = file.read()
        soup = BeautifulSoup(page, 'html.parser')
        return soup
  
    def parse_tag(self, html_file):
        '''
        Extracts links from the page. 
        Input: html_file -- a path to the file.
        Output: list of links for one html page.
        Must call make_soup() inside.
        '''
        raise NotImplementedError
    
    def get_file_dest(self, link, source_dir):
        '''
        Returns a full path to the file to be scraped from the link.
        Input: link -- a string with the link to the article.
        Output: a string with the full path to the file.
        
        Additional: for some sources, creates subdirectories in order to 
        recreate the structure of the website (in the _get_dest_dir() method).

        For the base class, returns just the full file name.
        '''
        parts = link.split('/')
        filename = parts[-1]
        file_dir = self._get_dest_dir(parts, source_dir)
        file_path = os.path.join(file_dir, filename)
        return file_path
        
    def _get_dest_dir(self, parts: list, source_dir: str):
        '''
        Returns a full path to the directory where the file should be saved.
        Input: parts -- a list of parts of the link.
               source_dir -- a string with the path to the source directory.

        For some sources, creates subdirectories in order to 
        recreate the structure of the website.
        For example, creates either "rubric" ('world' etc.) or "date" subdirectories.
        '''
        return source_dir


class HromadskeParser(SourceParser):
    def parse_tag(self, html):
        soup = self.make_soup(html)
        return [a_tag['href'] for a_tag in soup.find_all("a", class_="c-search-item__link")]


class NvParser(SourceParser):
    def __init__(self, index_page_link=None, page_num=None):
        super().__init__(index_page_link, page_num)
        self.subdirs = {}
        
    def parse_tag(self, html):
        soup = self.make_soup(html)
        return [a_tag['href'] for a_tag in soup.find_all("a", class_="row-result-body")]
    

    def _get_dest_dir(self, parts: list, source_dir: str):
        '''
        Returns a full path to the directory where the file should be saved.
        Input: parts -- a list of parts of the link.
               source_dir -- a string with the path to the source directory.

        For NV, creates subdirectories either for "rubric" ('world' etc.) or "nv.ua".
        Returns the full path to the subdirectory.
        '''
        rubric = parts[2].split('.')[0]
        if rubric != 'nv':
            # Check if we've already created this directory
            if rubric not in self.subdirs:
                article_dir = os.path.join(source_dir, rubric)
                os.makedirs(article_dir, exist_ok=True)
                self.subdirs[rubric] = article_dir
                return article_dir
            return self.subdirs[rubric]
        else:
            nv_basic_dir = os.path.join(source_dir, 'nv.ua')
            os.makedirs(nv_basic_dir, exist_ok=True)
            return nv_basic_dir


class SputnikParser(SourceParser):
    def parse_tag(self, html):
        soup = self.make_soup(html)
        return [header.find("a", class_="list__title")['href'] 
                for header in soup.find_all("div", class_="list__content")]
        
    def _get_dest_dir(self, parts: list, source_dir: str):
        '''
        Returns a full path to the directory where the file should be saved.
        Input: parts -- a list of parts of the link.
               source_dir -- a string with the path to the source directory.

        For Sputnik, creates subdirectories for the date of the article.

        Returns the full path to the subdirectory.
        '''
        date_part = parts[-2]
        article_dir = os.path.join(source_dir, date_part)
        os.makedirs(article_dir, exist_ok=True)
        return article_dir


class UkrinformParser(SourceParser):
    def __init__(self, index_page_link=None, page_num=None):
        super().__init__(index_page_link, page_num)
        # TODO: while scraping articles, sometimes I double the website prefix like
        # https://www.ukrinform.uahttps://www.ukrinform.ua
        # I fixed it manually in the .csv file, but it must be debugged somewhere
        self.prefix = 'https://www.ukrinform.ua'
        self.subdirs = {}

    def parse_tag(self, html):
        '''
        Since I saved ~84 index pages using the paginatiion on the website + 
        I saved google index pages manually (using google search and specifying the dates),
        here, I call either of the two methods to extract links.
        The google index pages have the name structure of `<year-pagenum>.html`
        while the website index pages have the name structure `<pagenum>`.
        '''
        soup = self.make_soup(html)
        html_name = os.path.basename(html).split('.')[0]
        if len(html_name) <= 2:
            return self._parse_tag_from_the_site(soup)
        return self._parse_tag_from_google(soup)

    def _parse_tag_from_the_site(self, soup):
        return [
            f"{self.prefix}{tag.find('a')['href']}"
            for tag in soup.find_all('article')
        ]

    def _parse_tag_from_google(self, soup):
        return [
            f"{self.prefix}{tag['href']}"
            for tag in soup.find_all('a', jsname="UWckNb")
        ]
        
    def _get_dest_dir(self, parts: list, source_dir: str):
        '''
        Returns a full path to the directory where the file should be saved.
        Input: parts -- a list of parts of the link.
               source_dir -- a string with the path to the source directory.

        For Ukrinform, creates subdirectories for the rubric of the article.

        Returns the full path to the subdirectory.
        '''
        rubric = parts[-2].split('-')[1]
        # Check if we've already created this directory
        if rubric not in self.subdirs:
            article_dir = os.path.join(source_dir, rubric)
            os.makedirs(article_dir, exist_ok=True)
            self.subdirs[rubric] = article_dir
            return article_dir
        return self.subdirs[rubric]


class EurActivParser(SourceParser):
    def parse_tag(self, html):
        soup = self.make_soup(html)
        return [h_tag.find('a')['href'] for h_tag in soup.find_all("h3")]

    def get_file_dest(self, link, source_dir):
        '''
        Returns a full path to the file to be scraped from the link.

        Since I have a lot of links from httrack, which are saved in the following way:
        www.euractiv.com/section/<section_name>/<genre_name>/<article_name>/index.html,
        I want to check first whether I have article saved. 
        Otherwise, I want to save the article in the same way for consistency,
        since httrack gave me ~1/2 of the articles I need.

        I also check whether the path exists in this function, so I can create a directory if needed
        '''
        dir_path = os.path.join(source_dir, link.replace('https://', ''))
        file_path = os.path.join(dir_path, 'index.html')
        if os.path.exists(file_path):
            return file_path
        os.makedirs(dir_path, exist_ok=True)
        return file_path


class TyzhdenParser(SourceParser):
    def parse_tag(self, html):
        soup = self.make_soup(html)
        return [
            tag.find('a')['href'] 
            for tag in soup.find_all('div', class_='news-item')
        ]

    def get_file_dest(self, link, source_dir):
        '''
        Returns a full path to the file to be scraped from the link.

        Since I have a lot of links from httrack, which are saved in the following way:
            TYZHDEN/<ARTICLE_NAME>/INDEX.HTM,
        I want to check first whether I have article saved. 
        Otherwise, I want to save the article in the same way for consistency,
        since httrack gave me ~3/4 of the articles I need.

        I also check whether the path exists in this function, so I can create a directory if needed.
        '''
        # make the file name shorter, like in the httrack version, uppercased and with underscores
        file_dir = link.split('/')[-2].upper().replace('-', '_')[:31]
        file_full_dir = os.path.join(source_dir, 'TYZHDEN', file_dir)
        file_path = os.path.join(file_full_dir, 'INDEX.HTM')

        if os.path.exists(file_path):
            return file_path
        os.makedirs(file_full_dir, exist_ok=True)
        return file_path


class KyivpostArchiveParser(SourceParser):
    def __init__(self, index_page_link=None, page_num=None):
        super().__init__(index_page_link, page_num)
        self.subdirs = set()
        self.archive_subdir = 'archive_kyivpost'

    def parse_tag(self, html):
        soup = self.make_soup(html)
        return [
            grid.find('a')['href'] 
            for grid in soup.find_all('div', class_='grid-3')
        ]

    def get_file_dest(self, link, source_dir):
        '''
        Returns a full path to the file to be scraped from the link.

        I check whether we already have the directory (rubric) to avoid creating it in each
        function call.

        I also save archive articles in the `archive_kyivpost/` subdirectory, since
        `archive.kyipost.com` led to bugs (because of dots).
        '''
        splitted = link.split('/')
        rubric_subdir, article_name = splitted[-2], splitted[-1]
        article_dir = os.path.join(source_dir, self.archive_subdir, rubric_subdir)
        if rubric_subdir not in self.subdirs:
            # 'kyivpost/archive_kyivpost/world/'
            os.makedirs(article_dir, exist_ok=True)
            self.subdirs.add(rubric_subdir)
        return os.path.join(article_dir, article_name)
    

if __name__ == '__main__':
    # real kyivpost path data/kyivpost/www.kyivpost.com/opinion
    parser = KyivpostArchiveParser()
    #print(parser.get_file_dest('https://archive.kyivpost.com/world/russias-rosneft-reports-889-mn-loss-from-assets-transfer-in-germany.html', 'kyivpost'))
    #print(parser.get_file_dest('https://archive.kyivpost.com/ukraine-politics/shmyhal-ukraine-sweden-to-boost-cooperation-in-energy-ecology-cyber-security.html', 'kyivpost'))

    tyzhden = TyzhdenParser()
    print(tyzhden.get_file_dest('https://tyzhden.ua/mistechko-iak-alternatyva-podilu-na-stolychnist-i-provintsijnist/', 'tyzhden'))

    euroactiv = EurActivParser()
    print(euroactiv.get_file_dest('https://www.euractiv.com/section/politics/news/hungary-drops-veto-on-eus-russia-sanctions-rollover-after-several-oligarchs-de-listed/', 'euractiv'))

    print(parser.subdirs)