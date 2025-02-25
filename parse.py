from datetime import datetime

from bs4 import BeautifulSoup

def extract_article_info(html):
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

    # might be an error here
    date_published = meta.find(itemprop="datePublished").text if meta.find(itemprop="datePublished") else None
    date_published = datetime.strptime(date_published, '%Y-%m-%dT%H:%M%z').strftime('%Y-%m-%d')

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
    }
    
    return article_info

