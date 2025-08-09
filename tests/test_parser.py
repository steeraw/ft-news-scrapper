from app.parsers.article import parse_article

def test_parse_article_sample():
    html = open('tests/sample_article.html', 'r', encoding='utf-8').read()
    data = parse_article('https://www.ft.com/content/xyz', html)
    assert data.title
    assert data.content
    assert data.is_paywalled is False
    assert data.word_count and data.word_count > 0
