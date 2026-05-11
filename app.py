import json
from flask import Flask, render_template_string, request

app = Flask(__name__)

# 1. JSONファイルを読み込む関数
def load_events():
    try:
        with open('events.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

# 2. カテゴリの定義（デザイン案に合わせてAllyなどを追加）
categories = [
    {'id': 'all', 'name': 'All / Mix', 'icon': 'all.png'},
    {'id': 'lesbian', 'name': 'Lesbian', 'icon': 'les.png'},
    {'id': 'gay', 'name': 'Gay', 'icon': 'gay.png'},
    {'id': 'bisexual', 'name': 'Bisexual', 'icon': 'bi.png'},
    {'id': 'transgender', 'name': 'Transgender', 'icon': 'trans.png'},
    {'id': 'queer', 'name': 'Queer', 'icon': 'queer.png'},
]

# 3. HTMLテンプレート（カード型デザイン）
# 3. HTMLテンプレート（デザイン調整版）
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
        /* 全体の背景は薄いグレー、アクセントはピンク */
        body { background-color: #fef1f2; font-family: 'Helvetica Neue', Arial, sans-serif; color: #444; }
        
        /* カテゴリナビゲーション */
        .nav-pills { background-color: #fff; border-radius: 50px; padding: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }
        .filter-icon { width: 24px; height: 24px; margin-bottom: 3px; }
        .nav-link { color: #888; font-size: 0.85rem; border-radius: 30px !important; padding: 10px 20px; text-align: center; }
        
        /* アクティブなタブはピンク背景に白文字 */
        .nav-link.active { background-color: #ff6b81 !important; color: #fff !important; box-shadow: 0 4px 10px rgba(255,107,129,0.3); }
        .nav-link.active .filter-icon { filter: brightness(0) invert(1); } /* アイコンを白くする */

        /* イベントカード（白） */
        .card { border: none; border-radius: 20px; background-color: #fff; transition: transform 0.2s; overflow: hidden; }
        .card:hover { transform: translateY(-5px); box-shadow: 0 10px 20px rgba(0,0,0,0.1) !important; }
        .event-image { height: 200px; object-fit: cover; }
        .card-title { color: #333; font-size: 1.1rem; }
        
        /* タグ */
        .badge-tag { background-color: #fce7f3; color: #db2777; border: none; font-size: 0.75rem; font-weight: normal; }
        
        /* 固定投稿ボタン（ピンク） */
        .post-button {
            position: fixed; bottom: 30px; right: 30px;
            width: 60px; height: 60px;
            background-color: #ff6b81; color: #fff;
            border-radius: 50%; display: flex; align-items: center; justify-content: center;
            font-size: 30px; text-decoration: none;
            box-shadow: 0 5px 15px rgba(255,107,129,0.4);
            transition: all 0.2s; z-index: 1000;
        }
        .post-button:hover { background-color: #ff4757; transform: scale(1.1); color: #fff; }
    </style>
</head>
<body>
    <div class="container py-5">
        <h1 class="text-center fw-bold mb-5" style="color: #333;">LGBTQ+ イベント掲示板</h1>

        <ul class="nav nav-pills justify-content-center mb-5 shadow-sm">
            {% for cat in categories %}
            <li class="nav-item">
                <a class="nav-link {% if active_cat == cat.id %}active{% endif %}" href="/?category={{ cat.id }}">
                    <img src="/static/images/icon_{{ cat.icon }}" class="filter-icon d-block mx-auto">
                    {{ cat.name }}
                </a>
            </li>
            {% endfor %}
        </ul>

        <div class="row row-cols-1 row-cols-md-2 row-cols-lg-3 g-4">
            {% for event in events %}
            <div class="col">
                <div class="card h-100 shadow-sm">
                    <img src="{{ event.image_url }}" class="card-img-top event-image" alt="{{ event.title }}">
                    <div class="card-body p-4">
                        <div class="mb-3">
                            <span class="badge bg-secondary-subtle text-secondary rounded-pill px-3 py-1 small">{{ event.category.capitalize() }}</span>
                        </div>
                        <h5 class="card-title fw-bold mb-3">{{ event.title }}</h5>
                        <p class="card-text text-muted mb-2 small"><i class="bi bi-calendar3 me-2"></i> {{ event.date }}</p>
                        <p class="card-text text-muted mb-4 small"><i class="bi bi-geo-alt me-2"></i> {{ event.location }}</p>
                        
                        <div class="d-flex flex-wrap gap-2">
                            {% for tag in event.tags %}
                            <span class="badge badge-tag rounded-pill px-3 py-1">{{ tag }}</span>
                            {% endfor %}
                        </div>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
    </div>

    <a href="/post" class="post-button shadow">
        <i class="bi bi-plus-lg"></i>
    </a>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
'''