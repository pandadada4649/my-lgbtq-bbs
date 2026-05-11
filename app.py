import json
import os
from flask import Flask, render_template_string, request, redirect, url_for

app = Flask(__name__)

# JSONファイルのパス設定
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_PATH = os.path.join(BASE_DIR, 'events.json')

# 1. データを読み込む
def load_events():
    if not os.path.exists(JSON_PATH):
        return []
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

# 2. データを保存する
def save_events(events):
    with open(JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(events, f, ensure_ascii=False, indent=2)

categories = [
    {'id': 'all', 'name': 'All / Mix', 'icon': 'all.png'},
    {'id': 'lesbian', 'name': 'Lesbian', 'icon': 'les.png'},
    {'id': 'gay', 'name': 'Gay', 'icon': 'gay.png'},
    {'id': 'bisexual', 'name': 'Bisexual', 'icon': 'bi.png'},
    {'id': 'transgender', 'name': 'Transgender', 'icon': 'trans.png'},
    {'id': 'queer', 'name': 'Queer', 'icon': 'queer.png'},
]

# --- デザイン（HTML） ---
INDEX_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LGBTQ+ イベント掲示板</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
    <style>
        body { background-color: #fef1f2; font-family: sans-serif; color: #444; }
        .nav-pills { background: #fff; border-radius: 50px; padding: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }
        .nav-link { color: #888; border-radius: 30px !important; text-align: center; font-size: 0.8rem; }
        .nav-link.active { background-color: #ff6b81 !important; color: #fff !important; }
        .filter-icon { width: 24px; height: 24px; display: block; margin: 0 auto 3px; }
        .nav-link.active .filter-icon { filter: brightness(0) invert(1); }
        .card { border: none; border-radius: 20px; overflow: hidden; transition: 0.2s; background: #fff; }
        .card:hover { transform: translateY(-5px); box-shadow: 0 10px 20px rgba(0,0,0,0.1) !important; }
        .event-image { height: 200px; object-fit: cover; }
        .badge-tag { background-color: #fce7f3; color: #db2777; border: none; }
        .post-button {
            position: fixed; bottom: 30px; right: 30px; width: 65px; height: 65px;
            background: #ff6b81; color: #fff; border-radius: 50%;
            display: flex; align-items: center; justify-content: center;
            font-size: 30px; box-shadow: 0 5px 15px rgba(255,107,129,0.4); z-index: 1000; text-decoration: none;
        }
    </style>
</head>
<body>
    <div class="container py-5">
        <h1 class="text-center fw-bold mb-5">LGBTQ+ イベント掲示板</h1>
        
        <ul class="nav nav-pills justify-content-center mb-5">
            {% for cat in categories %}
            <li class="nav-item">
                <a class="nav-link {% if active_cat == cat.id %}active{% endif %}" href="/?category={{ cat.id }}">
                    <img src="/static/images/icon_{{ cat.icon }}" class="filter-icon">
                    {{ cat.name }}
                </a>
            </li>
            {% endfor %}
        </ul>

        <div class="row row-cols-1 row-cols-md-2 row-cols-lg-3 g-4">
            {% for event in events %}
            <div class="col">
                <div class="card h-100 shadow-sm">
                    <img src="{{ event.image_url }}" class="card-img-top event-image">
                    <div class="card-body p-4">
                        <span class="badge bg-light text-secondary rounded-pill mb-2">{{ event.category }}</span>
                        <h5 class="card-title fw-bold">{{ event.title }}</h5>
                        <p class="small text-muted mb-1"><i class="bi bi-calendar3"></i> {{ event.date }}</p>
                        <p class="small text-muted mb-3"><i class="bi bi-geo-alt"></i> {{ event.location }}</p>
                        <div class="d-flex flex-wrap gap-1">
                            {% for tag in event.tags %}<span class="badge badge-tag rounded-pill">{{ tag }}</span>{% endfor %}
                        </div>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
    </div>

    <a href="/post" class="post-button"><i class="bi bi-plus-lg"></i></a>
</body>
</html>
'''

POST_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8"><title>イベント投稿</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
    <div class="container py-5" style="max-width: 600px;">
        <div class="card p-4 shadow-sm">
            <h2 class="mb-4">新しいイベントを投稿</h2>
            <form method="POST">
                <div class="mb-3"><label class="form-label">タイトル</label><input type="text" name="title" class="form-control" required></div>
                <div class="mb-3"><label class="form-label">カテゴリ</label>
                    <select name="category" class="form-select">
                        <option value="lesbian">Lesbian</option><option value="gay">Gay</option>
                        <option value="bisexual">Bisexual</option><option value="transgender">Transgender</option>
                    </select>
                </div>
                <div class="mb-3"><label class="form-label">日付</label><input type="text" name="date" class="form-control" placeholder="2026.05.25 (土) 19:00〜"></div>
                <div class="mb-3"><label class="form-label">場所</label><input type="text" name="location" class="form-control"></div>
                <div class="mb-3"><label class="form-label">画像URL</label><input type="text" name="image_url" class="form-control"></div>
                <div class="mb-3"><label class="form-label">タグ（カンマ区切り）</label><input type="text" name="tags" class="form-control" placeholder="交流会, パレード"></div>
                <button type="submit" class="btn btn-primary w-100" style="background:#ff6b81; border:none;">投稿する</button>
            </form>
        </div>
    </div>
</body>
</html>
'''

# --- ルート設定 ---
@app.route('/')
def index():
    all_events = load_events()
    active_cat = request.args.get('category', 'all')
    events = all_events if active_cat == 'all' else [e for e in all_events if e['category'] == active_cat]
    return render_template_string(INDEX_TEMPLATE, events=events, categories=categories, active_cat=active_cat)

@app.route('/post', methods=['GET', 'POST'])
def post():
    if request.method == 'POST':
        events = load_events()
        new_event = {
            "id": len(events) + 1,
            "category": request.form.get('category'),
            "title": request.form.get('title'),
            "date": request.form.get('date'),
            "location": request.form.get('location'),
            "image_url": request.form.get('image_url') or "https://via.placeholder.com/500x300",
            "tags": [t.strip() for t in request.form.get('tags').split(',')] if request.form.get('tags') else []
        }
        events.append(new_event)
        save_events(events)
        return redirect(url_for('index'))
    return render_template_string(POST_TEMPLATE)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)