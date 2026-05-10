import json
import os
from from flask import Flask, render_template_string, request, redirect, url_for

app = Flask(__name__)

DATA_FILE = 'events.json'

def load_events():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def save_events(events):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(events, f, ensure_ascii=False, indent=4)

CATEGORIES = [
    {"id": "lgbtq", "name": "LGBTQ（誰でもOK）", "icon_path": "icon_all.png"},
    {"id": "lesbian", "name": "レズビアン", "icon_path": "icon_les.png"},
    {"id": "gay", "name": "ゲイ", "icon_path": "icon_gay.png"},
    {"id": "bi", "name": "バイセクシャル", "icon_path": "icon_bi.png"},
    {"id": "trans", "name": "トランスジェンダー", "icon_path": "icon_trans.png"},
    {"id": "queer", "name": "クィア", "icon_path": "icon_queer.png"}
]

# --- 共通のスタイル ---
COMMON_STYLE = """
<style>
    body { font-family: 'Noto Sans JP', sans-serif; background-color: #f5f5f5; color: #333; margin: 0; }
    .navbar { background: linear-gradient(135deg, #ff9a9e 0%, #fad0c4 99%, #fad0c4 100%); padding: 15px 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
    .navbar-brand { font-weight: 700; font-size: 1.5rem; color: #fff !important; text-decoration: none; }
    
    /* カテゴリボタン */
    .filter-section { background-color: #fff; padding: 20px; border-bottom: 1px solid #eee; display: flex; justify-content: center; flex-wrap: wrap; gap: 10px; sticky; top: 0; z-index: 100; }
    @media (max-width: 768px) { .filter-section { justify-content: flex-start; overflow-x: auto; white-space: nowrap; flex-wrap: nowrap; padding: 15px; } }
    
    .btn-filter { border-radius: 25px; border: 2px solid #ff9a9e; background: white; color: #ff6b81; padding: 8px 18px; font-weight: 700; transition: 0.3s; text-decoration: none; font-size: 0.85rem; display: flex; align-items: center; gap: 8px; flex-shrink: 0; }
    .btn-filter:hover, .btn-filter.active { background: #ff9a9e; color: white; }
    .filter-icon { width: 20px; height: 20px; object-fit: contain; }
    .btn-filter.active .filter-icon { filter: brightness(0) invert(1); }

    /* カード */
    .container { max-width: 800px; margin: 30px auto; padding: 0 20px; }
    .event-card { background: #fff; border-radius: 15px; padding: 25px; margin-bottom: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); display: flex; border: 1px solid #eee; }
    .date-badge { background-color: #ffe0e6; color: #ff6b81; font-weight: 700; padding: 10px; border-radius: 10px; margin-right: 25px; min-width: 90px; text-align: center; height: fit-content; }
    .genre-tag { font-size: 0.75rem; padding: 4px 12px; border-radius: 20px; background: #fff0f3; color: #ff6b81; font-weight: 700; margin-bottom: 12px; display: inline-block; border: 1px solid #ffe0e6; }

    /* 浮いている投稿ボタン */
    .floating-btn {
        position: fixed; bottom: 30px; right: 30px; width: 60px; height: 60px;
        background: linear-gradient(135deg, #ff6b81 0%, #ff879c 100%);
        color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center;
        font-size: 30px; text-decoration: none; box-shadow: 0 4px 15px rgba(255,107,129,0.4);
        z-index: 1000; transition: 0.3s;
    }
    .floating-btn:hover { transform: scale(1.1); color: white; }

    /* フォーム用 */
    .form-box { background: white; padding: 30px; border-radius: 20px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); }
    .btn-submit { background: linear-gradient(135deg, #ff6b81 0%, #ff879c 100%); color: white; border: none; padding: 12px; border-radius: 25px; width: 100%; font-weight: 700; margin-top: 10px; }
</style>
"""

# --- メイン一覧ページのテンプレート ---
INDEX_TEMPLATE = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>LGBTQ+ Event Hub</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700&display=swap" rel="stylesheet">
    """ + COMMON_STYLE + """
</head>
<body>
    <nav class="navbar">
        <div class="container-fluid"><a class="navbar-brand" href="/">LGBTQ+ Event Hub</a></div>
    </nav>

    <div class="filter-section">
        <a href="/" class="btn-filter {% if current_genre == 'all' %}active{% endif %}">すべて</a>
        {% for cat in categories %}
        <a href="/?genre={{ cat.name }}" class="btn-filter {% if current_genre == cat.name %}active{% endif %}">
            <img src="{{ url_for('static', filename='images/' + cat.icon_path) }}" class="filter-icon" alt="">
            {{ cat.name }}
        </a>
        {% endfor %}
    </div>

    <div class="container">
        {% if not events %}
            <p class="text-center text-muted" style="margin-top: 50px;">該当するイベントはまだありません。</p>
        {% endif %}
        {% for ev in events %}
            <div class="event-card">
                <div class="date-badge">{{ ev.date }}</div>
                <div style="flex:1;">
                    <span class="genre-tag">#{{ ev.genre }}</span>
                    <div style="font-weight:700; font-size:1.2rem; margin-bottom: 5px;">{{ ev.title }}</div>
                    <div style="color:#888; font-size:0.9rem; margin-bottom: 10px;">📍 {{ ev.place }}</div>
                    <div style="font-size:0.95rem; white-space:pre-wrap; color: #555;">{{ ev.detail }}</div>
                </div>
            </div>
        {% endfor %}
    </div>

    <a href="/post_page" class="floating-btn">＋</a>
</body>
</html>
"""

# --- 投稿ページのテンプレート ---
POST_PAGE_TEMPLATE = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>イベントを投稿する</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    """ + COMMON_STYLE + """
</head>
<body>
    <nav class="navbar">
        <div class="container-fluid"><a class="navbar-brand" href="/">← 戻る</a></div>
    </nav>

    <div class="container" style="max-width: 600px;">
        <div class="form-box">
            <h3 style="color:#ff6b81; font-weight:700; margin-bottom:25px;">新しくイベントを投稿する</h3>
            <form method="POST" action="/post">
                <div class="mb-3">
                    <label class="form-label">カテゴリ</label>
                    <select name="genre" class="form-select">
                        {% for cat in categories %}
                        <option value="{{ cat.name }}">{{ cat.name }}</option>
                        {% endfor %}
                    </select>
                </div>
                <div class="mb-3">
                    <label class="form-label">開催日</label>
                    <input type="text" name="date" class="form-control" placeholder="6月1日 (土)" required>
                </div>
                <div class="mb-3">
                    <label class="form-label">イベント名</label>
                    <input type="text" name="title" class="form-control" required>
                </div>
                <div class="mb-3">
                    <label class="form-label">場所</label>
                    <input type="text" name="place" class="form-control" required>
                </div>
                <div class="mb-3">
                    <label class="form-label">詳細</label>
                    <textarea name="detail" class="form-control" rows="6" placeholder="イベントの内容、参加方法など"></textarea>
                </div>
                <button type="submit" class="btn btn-submit">イベントを公開する</button>
            </form>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    genre_filter = request.args.get('genre', 'all')
    all_events = load_events()
    if genre_filter != 'all':
        filtered_events = [e for e in all_events if e.get('genre') == genre_filter]
    else:
        filtered_events = all_events
    return render_template_string(INDEX_TEMPLATE, events=filtered_events, current_genre=genre_filter, categories=CATEGORIES)

@app.route('/post_page')
def post_page():
    return render_template_string(POST_PAGE_TEMPLATE, categories=CATEGORIES)

@app.route('/post', methods=['POST'])
def post():
    events = load_events()
    new_event = {
        "genre": request.form.get('genre'),
        "title": request.form.get('title'),
        "date": request.form.get('date'),
        "place": request.form.get('place'),
        "detail": request.form.get('detail')
    }
    events.insert(0, new_event)
    save_events(events)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)