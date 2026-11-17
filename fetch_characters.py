import json
import time
from pathlib import Path
import requests
import re
import html
import os

query = '''
query ($page: Int, $perPage: Int) {
    Page (page: $page, perPage: $perPage) {
            pageInfo {
                currentPage
                hasNextPage
                perPage
            }
            characters (sort: FAVOURITES_DESC) {
                id
                siteUrl
                image {
                    large
                }
                name {
                    full
                }
                media(perPage: 1) {
                    nodes {
                        title {
                            romaji
                        }
                        isAdult
                    }

                }
                description
                gender
            }
        }
    }
'''

def clean_description(text):
    if not text:
        return None
    spoilerpattern = r'~!.*?!~'
    htmlpattern = r'</?(?:a|i|b|br)\b[^>]*>'
    cleanspoiler = re.sub(spoilerpattern, '', text, flags=re.DOTALL)
    cleanhref = re.sub(htmlpattern, '', cleanspoiler, flags=re.IGNORECASE)
    paragraphs = cleanhref.split('\n\n')
    pattern = r'\[(.*?)\]\((.*?)\)'
    for p in paragraphs:
        p = p.strip()
        p = html.unescape(p)
        if p.startswith(('__', '**')):
            continue
        pretexted = re.sub(pattern, r'\1', p)
        cleaned = pretexted.replace('__', '').replace('\n', ' ').replace('**', '').replace('_', '').strip()
        cleaned = ' '.join(cleaned.split())
        if len(cleaned) < 40:
            continue
        return cleaned
    return None

def fetch_page(page):
    variables = {
        'page': page,
        'perPage': 50
    }

    url = 'https://graphql.anilist.co'

    MAX_RETRIES = 5
    for retry in range(MAX_RETRIES):
        response = requests.post(url, json={'query': query, 'variables': variables}, timeout=10)
        if response.status_code == 429:
            timetosleep = int(response.headers.get("Retry-After", 5))
            time.sleep(timetosleep)
            continue
        response.raise_for_status()
        result = response.json()
        if 'errors' in result:
            raise RuntimeError(result['errors'])
        return result['data']['Page']
    raise RuntimeError(f"Failed to fetch page {page} after {MAX_RETRIES} retries")

BASE_DIR = Path(__file__).parent
TMP_PATH = BASE_DIR / 'characters.json.tmp'
OUT_PATH = BASE_DIR / 'characters.json'

def main():
    results = []
    page = 1
    while len(results) < 400:
        data = fetch_page(page)
        for c in data['characters']:
            if c['gender'] == 'Female' and c['media']['nodes'] and c['image'] and c['description'] and not c['media']['nodes'][0]['isAdult']:
                desc = clean_description(c['description'])
                if desc:
                    results.append({
                        'name': c['name']['full'],
                        'series': c['media']['nodes'][0]['title']['romaji'],
                        'image': c['image']['large'],
                        'description': desc,
                        'siteUrl': c['siteUrl'],
                    })
        if not data['pageInfo']['hasNextPage']:
            break
        print(f"page {page}: {len(results)} so far")
        page += 1
        time.sleep(1)
    with open(TMP_PATH, 'w', encoding='utf-8') as f:
        json.dump(results[:400], f, ensure_ascii=False, indent=2)
    os.replace(TMP_PATH, OUT_PATH)

if __name__ == "__main__": main()