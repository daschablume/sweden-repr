import re

from base_extractor import BaseExtractor


UKR2ENG = {
    "Січня": "January", "Лютого": "February", "Березня": "March", "Квітня": "April",
    "Травня": "May", "Червня": "June", "Липня": "July", "Серпня": "August",
    "Вересня": "September", "Жовтня": "October", "Листопада": "November", "Грудня": "December"
}


class SputnikExtractor(BaseExtractor):
    def __init__(self):
        super().__init__()
        self.date_str_format = '%Y-%m-%dT%H:%M%z'

    def extract(self, file_path):
        soup = self.make_soup(file_path)
        meta = soup.find("div", class_="article__meta")
        body = soup.find("div", class_="article__body")
        footer = soup.find("div", class_="article__footer")
        
        if not meta or not body:
            return
        
        return {
            "title": self.find_title(soup),
            "date_published": self.find_date(meta),
            "abstract": self.find_abstract(soup),
            "article_body": self.find_article_body(body),
            "keywords": self.find_keywords(meta, footer),
            "genre": self.find_genre(meta),
            "author": self.find_author(meta),
            "file_path": self.normalize_path(file_path),
        }            

    def find_title(self, soup):
        header = soup.find("div", class_="article__header")
        title = soup.find("h1", class_="article__title").get_text(strip=True) if header else None
        return title

    def find_date(self, meta):
        parsed_date = None
        if date_publ := meta.find(itemprop="datePublished"):
            date_published = date_publ.text
            if date_published:
                parsed_date = self.parse_date(date_published)
        return parsed_date
    
    def find_abstract(self, soup):
        if announced_text := soup.find("div", class_="article__announce-text"):
            return announced_text.text
        return None
    
    def find_article_body(self, body):
        text_blocks = [
            self._remove_html_tags(str(block))
            for block 
            in body.find_all("div", class_="article__block")
        ]
        cleaned_text =  " ".join(text_blocks).replace(' .', '.')
        cleaned_text = self._remove_all_copyright_text(cleaned_text)
        return cleaned_text

    def _remove_all_copyright_text(self, text: str) -> str:
        '''Removes captions to copiritghted images'''
        return re.sub(r'©.*?©', '', text, flags=re.DOTALL)
    
    def find_keywords(self, meta, footer):
        '''
        Sometimes keywords are scattered in both footer and meta, so let's find all of them.
        '''
        keywords = []
        if meta_keywords := meta.find(itemprop="keywords"):
            keywords = [
                kw.strip().lower() 
                for kw in meta_keywords.get_text(strip=True).split(',')
            ] 

        if footer:
            footer_keywords = [
                tag.get_text(strip=True).lower() for tag in footer.find_all("li", class_="tag")
            ]
            keywords = list(set(footer_keywords + keywords))
        return keywords
    
    def find_genre(self, meta):
        genre = None
        if genre_meta := meta.find(itemprop="genre"):
            genre = genre_meta.text
        return genre
    
    def find_author(self, meta):
        author = None
        if author_meta := meta.find(itemprop="author"):
            author = author_meta.find(itemprop="name").text
        return author
    

class HromadskeExtractor(BaseExtractor):
    def __init__(self):
        super().__init__()
        self.date_str_format = '%Y-%m-%d'
    
    def find_title(self, soup):
        if header := soup.find("h1"):
            return header.get_text(strip=True)
        return None

    def find_date(self, soup):
        parsed_date = None
        if date := soup.find("time"):
            date_publ = date["datetime"].split('T')[0]
            parsed_date = self.parse_date(date_publ)
        return parsed_date
    
    def find_abstract(self, soup):
        if lead := soup.find("div", class_="o-lead"):
            return lead.get_text(strip=True)
        return None
    
    def find_article_body(self, soup):
        # text_list = soup.find_all("p", class_="text-start")
        content = soup.find("div", class_="s-content")
        text_list = content.find_all("p", class_="")
        read_more = [
            p.get_text(strip=True) 
            for p in content.find_all("p", class_="c-read-more__title")
        ]
        clean_text = [
            self._remove_html_tags(str(t))
            for t in text_list
        ]
        clean_text = [ 
            t for t in clean_text 
            if t and t not in read_more
        ]
        return " ".join(clean_text)
    
    def find_keywords(self, soup):
        tag_list = soup.find("ul", class_="c-tags__list")
        if not tag_list:
            return []
        keywords = [
            k.get_text(strip=True) 
            for i, k in enumerate(
                tag_list.find_all("li"))
            if i > 0  # the first in the list is the word "keywords"
        ]
        return keywords
    
    def find_genre(self, soup):
        # TODO
        '''
        Hro doesn't have a genre tag, however, they do have "news", "texts" (analytics) 
        and "opinions" parts of the website. These genres are not stated in the links either.
        (There are also interviews)
        So for now, I just return "news" as a genre.
        It can be improved but not the main priority.
        '''
        genre = 'news'
        return genre
    
    def find_author(self, soup):
        author = None
        if author_tag := soup.find("a", class_="c-post-author__name"):
            author = author_tag.get_text(strip=True)
        return author


class NvExtractor(BaseExtractor):
    def __init__(self):
        super().__init__()
        self.date_str_format = '%d %B %Y'
        self.article_body_re = re.compile(r"^article_content_replace_\d+$")
    

    def find_title(self, soup) -> str:
        '''
        There are some "special" articles which don't have a text title (the title is an image)
        '''
        if header := soup.find('h1'):
            return (
                header
                .get_text(strip=True)
                .replace('\xa0', ' ')
                .replace("<0xa0>", " ")
            )
        return None
    
    def find_date(self, soup) -> str:
        # 11 червня 2019, 11:02
        date_tag = soup.find('div', class_="article__head__additional_published")
        if not date_tag:
            date_tag = soup.find('span', class_="pub-date")
        if not date_tag:
            return None
        date = (
            date_tag
            .get_text(strip=True)
            .split(', ')[0]
        )
        month = date.split()[1]
        return date.replace(month, UKR2ENG[month.capitalize()])
    
    def find_abstract(self, soup) -> str:
        return (
            soup.find('div', class_="subtitle")
            .get_text(strip=True)
            .replace('\xa0', ' ')
            .replace("<0xa0>", " ")
        )
    
    def find_article_body(self, soup) -> str:
        if text_div := soup.find("div", id=self.article_body_re):
            text_div = text_div.find_all('p')
        else:
            text_div = soup.find("div", class_="content_wrapper").find_all("p")
        article_text = [
            self._remove_html_tags(str(t))
            for t in text_div
            if t.get_text(strip=True)
        ]
        return ' '.join(article_text).replace('Реклама', '')

    def find_keywords(self, soup) -> list:
        tags = soup.find_all('a', class_="tag")
        if not tags:
            return []
        return [
            tag.get_text(strip=True).lower().replace("<0xa0>", " ") 
            for tag in tags
        ]
    
    def find_genre(self, soup) -> str:
        if self._is_opinion(soup):
            return 'opinion'
        if keywords := self.find_keywords(soup):
            if "інтерв'ю nv" in keywords:
                return 'interview'
        return 'news'
    
    def find_author(self, soup) -> str:
        if author_tag := soup.find('p', class_='opinion_author_name'):
            return author_tag.get_text(strip=True)
        if author_tag := soup.find('a', class_='opinion_author_name'):
            return author_tag.get_text(strip=True)
        return None
    
    def _is_opinion(self, soup) -> bool:
        return bool(soup.find('p', class_='opinion_author_name'))


class UkrinformExtractor(BaseExtractor):
    def __init__(self):
        super().__init__()
        self.date_str_format = '%d.%m.%Y %H:%M'
    
    def find_title(self, soup) -> str:
        if title_h := soup.find("h1", class_="newsTitle"):
            return title_h.get_text(strip=True)
        # different if it's interview
        if title_h := soup.find('div', class_="firstTitle"):
            return title_h.get_text(strip=True)
        return None
    
    def find_date(self, soup) -> str:
        if date := soup.find("time"):
            return date.get_text(strip=True)
        
        # interview
        date_block = soup.find('div', class_="firstDate")
        # this is for a case when a class continues several <spans> some of them are not a date
        dates = [span.get_text(strip=True) for span in date_block.find_all('span')]
        for date in dates:
            try:
                # kinda call parse_date twice in the end...
                parsed_date = self.parse_date(date)
                return date
            except ValueError:
                continue
        else:
            return None
    
    def find_abstract(self, soup) -> str:
        if heading := soup.find("div", class_="newsHeading"):
            return heading.get_text(strip=True)
        if p_heading := soup.find("p", class_="newsHeading"):
            return p_heading.get_text(strip=True)
        return None
        
    def find_article_body(self, soup) -> str:
        if article_body := soup.find('div', class_="newsText"):
            article_body_list = [
                t.get_text(strip=True) 
                for t in article_body.find_all('p') 
                if t.get_text()
            ]
        # for interview
        if article_body := soup.find_all('div', class_="interviewText"):
            article_body_list = [
                t.get_text(strip=True) 
                for t in article_body if t.get_text()
            ]
        if article_body_list:
            return ' '.join(article_body_list)
        return None     
        
    def find_keywords(self, soup) -> list:
        return [
            kw.get_text(strip=True) 
            for kw in soup.find_all("a", class_="tag")
        ]
    
    def find_genre(self, soup) -> str:
        if soup.find('article', class_="interviewBlock"):
            return 'interview'
        return 'news'
    
    def find_author(self, soup) -> str:
        if author_div := soup.find("div", class_="newsAuthor"):
            return author_div.get_text(strip=True)
        if publ := soup.find("div", class_="newsPublisher"):
            return publ.get_text(strip=True)
        # TODO: if it's an interviewer, their name is in the very last piece of text,
        # like Євген Матюшенко -- without any class or anything (low priority)
        return "укрінформ"
        


class KyivPostExtractor(BaseExtractor):
    def __init__(self):
        super().__init__()
        self.date_str_format = "%b. %d, %Y"
    
    def find_title(self, soup) -> str:
        return soup.find("h1").get_text(strip=True)
    
    def find_date(self, soup) -> str:
        if div_info := soup.find("div", class_="post-info"):
            # date and author are enmeshed together
            date_orig = div_info.get_text(strip=True).split('\n')[-1].strip()
            # 'Oct. 29, 2022, 10:37 am' => 'Oct. 29, 2022'
            date =  ' '.join(date_orig.split()[:-2])[:-1]
            return date
        if date := soup.find("div", class_="time"):
            return date.get_text(strip=True)
        return None

    def find_abstract(self, soup) -> str:
        if section := soup.find("section", id="section_0").find('p'):
            return section.get_text(strip=True)
        elif section := soup.find("section", id="section_1").find("p"):
            return section.get_text(strip=True)
        
    def find_article_body(self, soup) -> str:
        text_tags = soup.find("section", id="section_0").find_all('p')
        text = [
            self._remove_html_tags(str(t))
            for t in text_tags
        ]
        text = [t for t in text if not t.startswith('Follow our') and t.strip()]
        return ' '.join(text)
    
    def find_keywords(self, soup) -> list:
        labels = soup.find_all("a", class_="label mainlabel")
        if labels:
            return [label.get_text(strip=True) for label in labels]
        return []
    
    def find_genre(self, soup) -> str:
        title = self.find_title(soup)
        if "interview" in title.lower():
            return "interview"
        if "opinion" in title.lower():
            return "opinion"
        return "news"
    
    def find_author(self, soup) -> str:
        return soup.find("a", class_="post-author-name").get_text(strip=True)


class KyivPostArchiveExtractor(KyivPostExtractor):
    def __init__(self):
        super().__init__()
        self.date_str_format = "%Y-%m-%d"
    
    def find_date(self, soup) -> str:
        return soup.find('time')['datetime'].split('T')[0]
    
    def find_abstract(self, soup) -> str:
        # TODO: very lazy implementation
        if article_body := soup.find('div', class_='entry-content'):
            return (
                article_body.find_all('p')[0]
                .get_text(strip=True)
                .replace('\xa0', ' ').replace('<0xa0>', ' ').replace('\n', ' ')
            )
        
    def find_article_body(self, soup) -> str:
        '''
        KyivPostArchive has a lot of javascript, 
        so here, I get the body of an article using BeautifulSoup methods,
        otherwise it gets too messy.
        '''
        if article_body := soup.find('div', class_='entry-content'):
            text_list = [
                p.get_text(strip=True).replace('\xa0', ' ').replace('<0xa0>', ' ').replace('\n', ' ') 
                for p in article_body.find_all('p') 
                if p.get_text(strip=True)
            ]
            # sometimes the first sentence is wrapped into double <p> and then it's 
            # parsed as two sentences -- avoid repetition
            if text_list[1].startswith(text_list[0][:10]):
                text_list = text_list[1:]
            return ' '.join(text_list)
        
    def find_keywords(self, soup) -> list:
        # archive articles don't have keywords
        return []
    
    def find_genre(self, soup) -> str:
        return 'news'
    
    def find_author(self, soup) -> str:
        return soup.find('div', class_='pm-item').find('a').get_text(strip=True)


class TyzhdenExtractor(BaseExtractor):
    def __init__(self):
        super().__init__()
        self.date_str_format = "%d %B %Y"
        self.kw_re = re.compile(r'<a .*?>.*?</a>')
        self.tag_ = re.compile(r'<.*?>')
    
    def find_title(self, soup) -> str:
        return soup.find('h1').get_text(strip=True)
    
    def find_date(self, soup) -> str:
        date = soup.find("div", class_="dt").get_text(strip=True)  # '9 Грудня 2011, 10:16'
        date = date.split(", ")[0]
        month = date.split()[1]
        return date.replace(month, UKR2ENG[month.capitalize()])
    
    def find_abstract(self, soup) -> str:
        # Tyzhden really doesn't have an abstract
        return ''
    
    def find_article_body(self, soup) -> str:
        if text_raw := soup.find("div", class_="entry-content"):
            text_list = []
            for p_tag in text_raw.find_all("p"):
                sentence = p_tag.get_text(strip=True)
                if sentence.lower().startswith("читайте"):
                    continue
                text_list.append(sentence.replace('\n', '').replace('\t', '').replace('\xa0', ' '))
            return ' '.join(text_list)
    
    def find_keywords(self, soup) -> list:
        # process tags since they are not a list but a string and get_text() returns them as a single string
        tag_string = str(soup.find("div", class_="tags").find("div", class_="all-tags"))
        tags = re.findall(self.kw_re, tag_string)
        return [
            re.sub(self.tag_, '', tag) 
            for tag in tags
        ]
    
    def find_genre(self, soup) -> str:
        # TODO: 
        return 'news'
    
    def find_author(self, soup) -> str:
        if author_tag := soup.find("span", class_="a-name"):
            return author_tag.get_text(strip=True)


class EuractivExtractor(BaseExtractor):
    def __init__(self):
        super().__init__()
        self.date_str_format = '%b %d, %Y'

    def find_title(self, soup) -> str:
        return soup.find('h1').get_text(strip=True)
    
    def find_date(self, soup) -> str:
        return soup.find('span', class_='tw-border-grey').get_text(strip=True)        
    
    def find_article_body_and_abstract(self, soup) -> tuple[str, str]:
        # div for paywall
        if soup.find('div', class_='fp-pro'):
            return None, None
        if text_div := soup.find('div', id='metered-article'):
            text_list = text_div.find_all('p')
        if text_div := soup.find('div', class_='ea-article-body-content'):
            text_list = text_div.find_all('p')
        if text_list:
            text = [
                self._remove_html_tags(str(t))
                for t in text_list
            ]
            text = [t for t in text if t.strip()]
            abstract = text[0]
            article_body = ' '.join(text)
            # check repetition in the body: find the last 3 words, look for them in the text.
            # if they are present more than once, cut the text
            article_words = article_body.split()
            united_words = ' '.join(article_words[-3:])
            ind_1 = article_body.find(united_words)
            ind_2 = article_body.find(united_words, ind_1+1)
            if ind_2 != -1:
                article_body = article_body[:ind_1+len(united_words)]

        return article_body, abstract
    
    def find_keywords(self, soup) -> list:
        topics = soup.find('ul', class_='clearfix').find_all('li')
        if topics:
            return [topic.get_text(strip=True) for topic in topics]
        return []
    
    def find_genre(self, file_path) -> str:
        '''
        Since links were scraped from httrack,
        every article is in destination with the name of the genre.
        '''
        return file_path.split('/')[-3]

    def find_author(self, soup) -> str:
        if author_span := soup.find('span', class_='tw-font-bold'):
            return author_span.get_text(strip=True)
        return None

    def find_abstract(self, soup) -> str:
        raise NotImplementedError("Use find_article_body_and_abstract instead")

    def find_article_body(self, soup) -> str:
        raise NotImplementedError("Use find_article_body_and_abstract instead")

    def extract(self, file_path) -> dict:
        soup = self.make_soup(file_path)
        article_body, abstract = self.find_article_body_and_abstract(soup)
        if not article_body:
            return None

        genre = self.find_genre(file_path)
               
        return {
            "title": self.find_title(soup),
            "date_published": self.parse_date(self.find_date(soup)),
            "abstract": abstract,
            "article_body": article_body,
            "keywords": self.find_keywords(soup),
            "genre": genre,
            "author": self.find_author(soup),
            "file_path": self.normalize_path(file_path),
        }  
