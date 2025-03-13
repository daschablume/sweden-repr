import time

from extractors import (
    SputnikExtractor, HromadskeExtractor, NvExtractor,
    KyivPostExtractor, UkrinformExtractor
)

def test_SputnikExtractor():
    link = '../data/sputnik/20120618/174104542.html'
    extractor = SputnikExtractor()
    data = extractor.extract(link)
    print(data)

def test_SputnikExtractor_2():
    link = '../data/sputnik/20190927/church-of-sweden-to-ring-bells-for-greta-thunbergs-global-climate-strike-1076901289.html'
    extractor = SputnikExtractor()
    data = extractor.extract(link)
    print(data)


def test_HromadskeExtractor():
    extractor = HromadskeExtractor()
    links = [
        '/Users/macuser/Documents/UPPSALA/thesis/data/hromadske/223738-shvetsiia-vydilyt-eur28-mln-na-viyskovu-pidtrymku-ukrayiny-kudy-spriamuiut-hroshi.html',
        '/Users/macuser/Documents/UPPSALA/thesis/data/hromadske/224858-shvetsiia-nadast-ukrayini-novyy-paket-dopomohy-dlia-enerhosystemy.html',
        '/Users/macuser/Documents/UPPSALA/thesis/data/hromadske/227159-hretsiia-zaprovadzuye-shestydennyy-robochyy-tyzden.html',
        '/Users/macuser/Documents/UPPSALA/thesis/data/hromadske/greciya-peredast-ukrayini-radyanske-ozbroyennya-natomist-nimechchina-nadast-afinam-svoyi-bmp.html',
        '/Users/macuser/Documents/UPPSALA/thesis/data/hromadske/holovne-pytannia-v-perehovorakh-trampa-i-putina-bude-syriia-eks-holova-mzs-shvetsii.html',
    ]
    for link in links:
        data = extractor.extract(link)
        print(data)
        time.sleep(5)

def test_HromadskeExtractor_2():
    link = '../data/hromadske/parlament-ugorshini-znovu-vidklav-ratifikaciyu-zayavok-shveciyi-ta-finlyandiyi-na-vstup-do-nato.html'
    extractor = HromadskeExtractor()
    body = extractor.find_article_body(extractor.make_soup(link))
    print(body)

def test_NvExtractor():
    link = '../data/nv/techno/-50026416.html'
    extractor = NvExtractor()
    soup = extractor.make_soup(link)
    assert extractor.find_keywords((soup)) == ['сибір', 'палеонтологія', 'розкопки', 'якутія', 'волки']
    assert extractor.parse_date(extractor.find_date(soup)) == '2019-06-11'
    assert extractor.find_article_body(soup).split('. ')[0] == 'За оцінками вчених, пройшло 40 тис'
    assert extractor.find_author(soup) == "Антон Ходоренко"

    link = '../data/nv/azart/dzhekpot-v-onlayn-kazino-50183710.html'
    soup = extractor.make_soup(link)
    assert extractor.find_author(soup) == 'Андрiй Сорока'
    assert extractor.find_genre(soup) == 'news'
    assert extractor.find_article_body(soup).split(' ')[-2] == 'липня'
    
    link = '../data/nv/nv.ua/5-lipnja-tramp-zagubivsja-i-makron-007-1435177.html'
    soup = extractor.make_soup(link)
    assert extractor.find_author(soup) == 'Іван Яковина'
    assert extractor.find_genre(soup) == 'opinion'


def test_KyivPostExtractor():
    extractor = KyivPostExtractor()
    link = '../data/kyivpost/www.kyivpost.com/post/449.html'
    extractor.extract(link)
    soup = extractor.make_soup(link)
    assert extractor.find_author(soup) == 'Kyiv Post'
    assert extractor.find_title(soup) ==  'Ukrainian Component Identified in Disassembled Iranian Drone'

    link2 = '../data/kyivpost/www.kyivpost.com/videos/1310.html'
    extractor.extract(link2)
    soup2 = extractor.make_soup(link2)
    assert extractor.find_keywords(soup2) ==  ['War in Ukraine', 'US', 'Kasparov']
    assert extractor.find_author(soup2) == 'Jason Jay Smart'
    assert extractor.find_title(soup2) == 'Exclusive Interview with Chess Champ and Russian Opposition Leader Garry Kasparov'

    link3 = '../data/kyivpost/www.kyivpost.com/opinion/1330.html'
    extractor.extract(link3)
    soup3 = extractor.make_soup(link3)
    assert extractor.find_genre(soup3) == 'opinion'

    print(extractor.extract(link3))


def test_Ukrinform():
    extractor = UkrinformExtractor()
    link = '../data/ukrinform/eurovision/2227459-veduci-evrobacenna-2017-rozpovili-ak-vcili-anglijsku-ta-hto-ih-gotuvav-do-konkursu.html'

if __name__ == "__main__":
    #test_SputnikExtractor_2()
    test_KyivPostExtractor()