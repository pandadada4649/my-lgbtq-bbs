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
        body { background-color: #f8f9fa; font-family: 'Helvetica Neue', Arial, sans-serif; }
        .card { transition: transform 0.2s; border: none; border-radius: 15px; overflow: hidden; }
        .card:hover { transform: translateY(-5px); }
        .filter-icon { width: 30px; height: 30px; margin-bottom: 5px; }
        .nav-link { color: #6c757d; font-size: 0.8rem; text-align: center; border-radius: 10px; margin: 0 2px; }
        .nav-link.active { background-color: #fff !important; color: #ff6b6b !important; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        .event-image { height: 200px; object-fit: cover; }
        .badge-tag { background-color: #e0f7fa; color: #00838f; border: none; }
    </style>
</head>
<body>
    <div class="container py-4">
        <h1 class="text-center fw-bold mb-4">LGBTQ+ イベント掲示板</h1>

        <ul class="nav nav-pills justify-content-center mb-5 bg-light p-2 rounded-4 shadow-sm">
            {% for cat in categories %}
            <li class="nav-item">
                <a class="nav-link {% if active_cat == cat.id %}active{% endif %}" href="/?category={{ cat.id }}">
                    <img src="/static/images/icon_{{ cat.icon }}" class="filter-icon d-block mx-auto {% if active_cat == cat.id %}filter-invert{% endif %}">
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
                    <div class="card-body">
                        <div class="mb-2">
                            <span class="badge bg-secondary-subtle text-secondary small">{{ event.category.capitalize() }}</span>
                        </div>
                        <h5 class="card-title fw-bold">{{ event.title }}</h5>
                        <p class="card-text text-muted mb-1 small"><i class="bi bi-calendar3"></i> {{ event.date }}</p>
                        <p class="card-text text-muted mb-3 small"><i class="bi bi-geo-alt"></i> {{ event.location }}</p>
                        
                        <div class="d-flex flex-wrap gap-1">
                            {% for tag in event.tags %}
                            <span class="badge badge-tag rounded-pill">{{ tag }}</span>
                            {% endfor %}
                        </div>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
    </div>
</body>
</html>
'''

@app.route('/')
def index():
    all_events = load_events()
    active_cat = request.args.get('category', 'all')
    
    if active_cat == 'all':
        events = all_events
    else:
        events = [e for e in all_events if e['category'] == active_cat]
        
    return render_template_string(INDEX_TEMPLATE, events=events, categories=categories, active_cat=active_cat)

if __name__ == '__main__':
    import os
    # Renderが指定するポート番号を読み取る設定
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)