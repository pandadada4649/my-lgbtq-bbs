import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# app.py と同じDB設定を読み込む
from app import app, db, Event

# ===== 検索キーワード =====
KEYWORDS = ['lgbtq', 'LGBT', 'プライド', 'クィア', 'レズビアン', 'ゲイ', 'トランスジェンダー']

# ===== カテゴリの自動判定 =====
def detect_category(title, desc):
    text = (title + desc).lower()
    if 'lesbian' in text or 'レズビアン' in text:
        return 'Lesbian'
    elif 'gay' in text or 'ゲイ' in text:
        return 'Gay'
    elif 'bisexual' in text or 'バイセクシュアル' in text:
        return 'Bisexual'
    elif 'transgender' in text or 'トランス' in text:
        return 'Transgender'
    elif 'queer' in text or 'クィア' in text:
        return 'Queer'
    elif 'ally' in text or 'アライ' in text:
        return 'Ally'
    else:
        return 'All / Mix'

# ===== エリアの自動判定 =====
def detect_area(text):
    if '東京' in text or '渋谷' in text or '新宿' in text:
        return '東京'
    elif '大阪' in text or '梅田' in text:
        return '大阪'
    elif '名古屋' in text:
        return '名古屋'
    elif '福岡' in text or '博多' in text:
        return '福岡'
    elif 'オンライン' in text or 'online' in text.lower():
        return 'オンライン'
    else:
        return 'その他'

# ===== Peatixからイベントを取得 =====
def fetch_peatix(keyword):
    url = f'https://peatix.com/search?q={keyword}&country=JP'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')

        events = []
        # Peatixのイベントカードを取得
        cards = soup.select('li.event-card, div.event-card, article.event')

        if not cards:
            # セレクタが変わっている場合の代替
            cards = soup.select('[class*="event"]')

        for card in cards[:10]:
            title_el = card.select_one('h2, h3, [class*="title"], [class*="name"]')
            title = title_el.get_text(strip=True) if title_el else ''

            date_el = card.select_one('time, [class*="date"], [class*="time"]')
            date_text = date_el.get_text(strip=True) if date_el else ''

            place_el = card.select_one('[class*="location"], [class*="place"], [class*="venue"]')
            place = place_el.get_text(strip=True) if place_el else ''

            link_el = card.select_one('a[href]')
            link = 'https://peatix.com' + link_el['href'] if link_el and link_el['href'].startswith('/') else (link_el['href'] if link_el else '')

            if title:
                events.append({
                    'title': title,
                    'date_text': date_text,
                    'place': place,
                    'link': link,
                })

        return events

    except Exception as e:
        print(f'  ⚠️ 取得失敗 ({keyword}): {e}')
        return []

# ===== メイン処理 =====
def auto_post():
    with app.app_context():
        print(f'\n🌈 自動投稿開始: {datetime.now().strftime("%Y-%m-%d %H:%M")}')

        AUTO_USER_ID = 1
        added = 0
        skipped = 0

        for keyword in KEYWORDS:
            print(f'\n🔍 検索: {keyword}')
            events = fetch_peatix(keyword)

            if not events:
                print(f'  結果なし')
                continue

            for e in events:
                title = e['title']
                place = e['place']
                link  = e['link']

                if len(title) < 3:
                    continue

                # 重複チェック
                if Event.query.filter_by(title=title).first():
                    skipped += 1
                    print(f'  スキップ（重複）: {title[:30]}')
                    continue

                category = detect_category(title, place)
                area     = detect_area(title + place)
                mode     = 'オンライン' if area == 'オンライン' else 'オフライン'
                desc     = f'🔗 詳細・申込: {link}' if link else ''

                event = Event(
                    user_id         = AUTO_USER_ID,
                    title           = title,
                    category        = category,
                    area            = area,
                    location_detail = place[:200],
                    date            = '',
                    time            = '',
                    event_type      = '交流会',
                    mode            = mode,
                    description     = desc,
                    emoji           = '🌈',
                    image_url       = None,
                    is_pickup       = False,
                )
                db.session.add(event)
                added += 1
                print(f'  ✅ 追加: {title[:40]}')

        db.session.commit()
        print(f'\n🎉 完了！ 追加: {added}件 / スキップ: {skipped}件')

if __name__ == '__main__':
    auto_post()