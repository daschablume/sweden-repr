from datetime import datetime

from bs4 import BeautifulSoup

UNIFIED_PARSE_DATE = '%Y-%m-%d'


def extract_from_sputnik(file_path):
    with open(file_path, encoding='utf-8') as fp:
        html = fp.read()
    soup = BeautifulSoup(html, "html.parser")
    
    meta = soup.find("div", class_="article__meta")
    body = soup.find("div", class_="article__body")
    footer = soup.find("div", class_="article__footer")

    if not meta or not body:
        return

    header = soup.find("div", class_="article__header")
    title = header.find("h1", class_="article__title").get_text(strip=True) if header else None

    keywords = meta.find(itemprop="keywords").text if meta.find(itemprop="keywords") else None
    keywords = [kw.strip().lower() for kw in keywords.split(',')]
    footer_keywords = [
        tag.get_text(strip=True).lower() for tag in footer.find_all("li", class_="tag")
    ]
    keywords = list(set(footer_keywords + keywords))

    date_published = meta.find(itemprop="datePublished").text if meta.find(itemprop="datePublished") else None
    date_published = datetime.strptime(
        date_published, '%Y-%m-%dT%H:%M%z'
        ).strftime(UNIFIED_PARSE_DATE)

    article_info = {
        "date_published": date_published,
        #"dateCreated": meta.find(itemprop="dateCreated").text if meta.find(itemprop="dateCreated") else None,
        #"dateModified": meta.find(itemprop="dateModified").text if meta.find(itemprop="dateModified") else None,
        "genre": meta.find(itemprop="genre").text if meta.find(itemprop="genre") else None,
        "author": meta.find(itemprop="author").find(itemprop="name").text if meta.find(itemprop="author") else None,
        "keywords": keywords,
        "title": title,
        "abstract": soup.find("div", class_="article__announce-text").text if soup.find("div", class_="article__announce-text") else None,
        "article_body": " ".join(block.get_text(strip=True) for block in body.find_all("div", class_="article__block")),
        "file_path": file_path,
    }
    
    return article_info


def extract_from_ukrinform(file_path):
    with open(file_path, encoding='utf-8') as fp:
        html = fp.read()
    soup = BeautifulSoup(html, "html.parser")
    
    article_body = soup.find('div', class_="newsText")
    if not article_body:
        if soup.find('article', class_="interviewBlock"):
            return extract_from_ukrinform_interview(file_path)
        return
    article_text = [t.get_text(strip=True) for t in article_body.find_all('p') if t.get_text()]
    # for Ukrinform, abstract is basically the beginning of the article, so I
    # extract it both to "abstract" but also attach to the body
    abstract = soup.find(
        "div", class_="newsHeading").text if soup.find("div", class_="newsHeading") else None
    if abstract:
        article_text = [abstract] + article_text
    else:
        abstract = soup.find(
            "p", class_="newsHeading").text if soup.find("p", class_="newsHeading") else None

    title = soup.find("h1", class_="newsTitle").get_text(strip=True)
    date = soup.find("time").get_text(strip=True)
    parsed_date = datetime.strptime(date, '%d.%m.%Y %H:%M').strftime(UNIFIED_PARSE_DATE)

    author = soup.find("div", class_="newsAuthor")
    if author:
        author = author.get_text(strip=True)
    else:
        author = soup.find("div", class_="newsPublisher").get_text(strip=True) if soup.find("div", class_="newsPublisher") else None

    keywords = [kw.get_text(strip=True) for kw in soup.find_all("a", class_="tag")]

    # TODO1:
    # sometimes, the author will be in the very end of the text, like "Дмитро Редько, Київ"

    article_info = {
        "date_published": parsed_date,
        "genre": 'news',  # hardcoded for now, since for now there only 2 genres; TODO2
        "author": author,
        "keywords": keywords,
        "title": title,
        "abstract": abstract,
        "article_body": ' '.join(article_text),
        "file_path": file_path,
    }

    return article_info


def extract_from_ukrinform_interview(file_path):
    with open(file_path, encoding='utf-8') as fp:
        html = fp.read()
    soup = BeautifulSoup(html, "html.parser")
    
    article_body = soup.find_all('div', class_="interviewText")
    if not article_body:
        return 
 
    article_text = [t.get_text(strip=True) for t in article_body if t.get_text()]
    # in an interview, the "header" of the text is usually the very first <div>
    abstract = article_text[0]
    # TODO3: if it's an interviewer, their name is in the very last piece of text, like
    # Євген Матюшенко -- without any class or anything
    author = "укрінформ"  # hardcoded for now

    date_block = soup.find('div', class_="firstDate")
    # this is for a case when a class continues several <spans> some of them are not a date
    dates = [span.get_text(strip=True) for span in date_block.find_all('span')]
    for date in dates:
        try:
            parsed_date = datetime.strptime(date, '%d.%m.%Y %H:%M').strftime(UNIFIED_PARSE_DATE)
            break
        except ValueError:
            continue
    keywords = [kw.get_text(strip=True) for kw in soup.find_all("a", class_="tag")]
    title = soup.find('div', class_="firstTitle").get_text(strip=True)

    article_info = {
        "date_published": parsed_date,
        "genre": "interview",  # hardcoded for now, since for now there only 2 genres
        "author": author,
        "keywords": keywords,
        "title": title,
        "abstract": abstract,
        "article_body": article_text,
        "file_path": file_path,
    }
    
    return article_info


#extract_from_ukrinform(path)


