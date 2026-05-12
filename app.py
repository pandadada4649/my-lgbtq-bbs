import json
import os
from flask import Flask, render_template_string, request, redirect, url_for
from werkzeug.utils import secure_filename

app = Flask(__name__)

# --- 設定 ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_PATH = os.path.join(BASE_DIR, 'events.json')
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static/uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 管理用パスワード（必要に応じてここを好きな文字列に変えてください）
ADMIN_PASSWORD = "soyoka_admin" 

def load_events():
    if not os.path.exists(JSON_PATH): return []
    with open(JSON_PATH, 'r', encoding='utf-8') as f: return json.load(f)

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

# --- INDEX_TEMPLATE（削除ボタンをパスワード入力式に変更） ---
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
        .btn-delete { color: #ff6b81; font-size: 0.8rem; border: none; background: none; padding: 0; cursor: pointer; }
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
                    <a href="/event/{{ event.id }}"><img src="{{ event.image_url }}" class="card-img-top event-image"></a>
                    <div class="card-body p-4">
                        <span class="badge bg-light text-secondary rounded-pill mb-2">{{ event.category }}</span>
                        <h5 class="card-title fw-bold"><a href="/event/{{ event.id }}" class="text-decoration-none text-dark">{{ event.title }}</a></h5>
                        <p class="small text-muted mb-1"><i class="bi bi-calendar3"></i> {{ event.date }}</p>
                        <p class="small text-muted mb-3"><i class="bi bi-geo-alt"></i> {{ event.location }}</p>
                        
                        <div class="d-flex justify-content-between align-items-center">
                            <div class="d-flex flex-wrap gap-1">
                                {% for tag in event.tags %}<span class="badge badge-tag rounded-pill">{{ tag }}</span>{% endfor %}
                            </div>
                            <!-- 削除用フォーム（パスワードをプロンプトで受け取る） -->
                            <form action="/delete/{{ event.id }}" method="POST" style="display: inline;" 
                                  onsubmit="const pw = prompt('管理用パスワードを入力してください'); if(pw){ this.password.value = pw; return true; } return false;">
                                <input type="hidden" name="password" value="">
                                <button type="submit" class="btn-delete">
                                    <i class="bi bi-trash"></i> 削除
                                </button>
                            </form>
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

# --- DETAIL_TEMPLATE（詳細ページ） ---
DETAIL_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ event.title }}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
    <style>body { background-color: #fef1f2; color: #444; }</style>
</head>
<body>
    <div class="container py-5" style="max-width: 800px;">
        <div class="card shadow border-0 overflow-hidden" style="border-radius: 25px;">
            <img src="{{ event.image_url }}" class="img-fluid w-100" style="max-height: 450px; object-fit: cover;">
            <div class="card-body p-5">
                <h1 class="fw-bold mb-4">{{ event.title }}</h1>
                <p class="text-muted mb-4"><i class="bi bi-calendar3"></i> {{ event.date }} / <i class="bi bi-geo-alt"></i> {{ event.location }}</p>
                <hr>
                <p style="white-space: pre-wrap; line-height: 1.8;">{{ event.description or "詳細な説明はありません。" }}</p>
                <div class="mt-5 pt-3 border-top d-grid">
                    <a href="/" class="btn btn-outline-secondary btn-lg rounded-pill">戻る</a>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
'''

# --- POST_TEMPLATE ---
POST_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8"><title>イベント投稿</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
    <div class="container py-5" style="max-width: 600px;">
        <div class="card p-4 shadow-sm" style="border-radius: 20px;">
            <h2 class="mb-4 fw-bold">新しいイベントを投稿</h2>
            <form method="POST" enctype="multipart/form-data">
                <div class="mb-3"><label class="form-label">タイトル</label><input type="text" name="title" class="form-control" required></div>
                <div class="mb-3"><label class="form-label">カテゴリ</label>
                    <select name="category" class="form-select">
                        <option value="lesbian">Lesbian</option><option value="gay">Gay</option>
                        <option value="bisexual">Bisexual</option><option value="transgender">Transgender</option>
                        <option value="queer">Queer</option>
                    </select>
                </div>
                <div class="mb-3"><label class="form-label">日付</label><input type="text" name="date" class="form-control"></div>
                <div class="mb-3"><label class="form-label">場所</label><input type="text" name="location" class="form-control"></div>
                <div class="mb-3"><label class="form-label">詳細な説明</label><textarea name="description" class="form-control" rows="5"></textarea></div>
                <div class="mb-3"><label class="form-label">イベント画像</label><input type="file" name="image" class="form-control" accept="image/*"></div>
                <div class="mb-3"><label class="form-label">タグ（カンマ区切り）</label><input type="text" name="tags" class="form-control"></div>
                <button type="submit" class="btn btn-primary w-100 py-3 rounded-pill fw-bold" style="background:#ff6b81; border:none;">投稿する</button>
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
        image_file = request.files.get('image')
        image_url = "https://via.placeholder.com/500x300"
        if image_file and image_file.filename != '':
            filename = secure_filename(image_file.filename)
            if not os.path.exists(app.config['UPLOAD_FOLDER']): os.makedirs(app.config['UPLOAD_FOLDER'])
            image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_url = '/static/uploads/' + filename

        new_event = {
            "id": int(os.urandom(4).hex(), 16),
            "category": request.form.get('category'),
            "title": request.form.get('title'),
            "description": request.form.get('description'),
            "date": request.form.get('date'),
            "location": request.form.get('location'),
            "image_url": image_url,
            "tags": [t.strip() for t in request.form.get('tags').split(',')] if request.form.get('tags') else []
        }
        events.append(new_event)
        save_events(events)
        return redirect(url_for('index'))
    return render_template_string(POST_TEMPLATE)

@app.route('/event/<int:event_id>')
def event_detail(event_id):
    events = load_events()
    event = next((e for e in events if e.get('id') == event_id), None)
    if event is None: return "Event Not Found", 404
    return render_template_string(DETAIL_TEMPLATE, event=event)

# --- 削除ルート（パスワード認証付き） ---
@app.route('/delete/<int:event_id>', methods=['POST'])
def delete_event(event_id):
    input_password = request.form.get('password')
    
    if input_password == ADMIN_PASSWORD:
        events = load_events()
        filtered_events = [e for e in events if e.get('id') != event_id]
        save_events(filtered_events)
        return redirect(url_for('index'))
    else:
        return "パスワードが正しくありません。", 403

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)