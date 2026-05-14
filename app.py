import json
import os
import datetime
from flask import Flask, render_template_string, request, redirect, url_for
from werkzeug.utils import secure_filename
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'soyoka-secret-key'

# --- 🌟 パス設定 ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_PATH = os.path.join(BASE_DIR, 'events.json')
USER_PATH = os.path.join(BASE_DIR, 'users.json')
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'images', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# --- ログイン管理 ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    users = load_users_data()
    user_data = next((u for u in users if str(u['id']) == str(user_id)), None)
    if user_data: return User(user_data['id'], user_data['username'])
    return None

# --- データ処理関数 ---
def load_events():
    if not os.path.exists(JSON_PATH): return []
    with open(JSON_PATH, 'r', encoding='utf-8') as f: return json.load(f)

def save_events(events):
    with open(JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(events, f, ensure_ascii=False, indent=2)

def load_users_data():
    if not os.path.exists(USER_PATH): return []
    with open(USER_PATH, 'r', encoding='utf-8') as f: return json.load(f)

def save_users_data(users):
    with open(USER_PATH, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

# --- 🌟 カテゴリ定義 ---
categories = [
    {'id': 'lesbian', 'name': 'Lesbian', 'jp': 'レズビアン', 'icon': 'icon_les.png', 'color': '#fff0f3'},
    {'id': 'gay', 'name': 'Gay', 'jp': 'ゲイ', 'icon': 'icon_gay.png', 'color': '#fff4ec'},
    {'id': 'bisexual', 'name': 'Bisexual', 'jp': 'バイセクシュアル', 'icon': 'icon_bi.png', 'color': '#f3f0ff'},
    {'id': 'transgender', 'name': 'Transgender', 'jp': 'トランスジェンダー', 'icon': 'icon_trans.png', 'color': '#eef9ff'},
    {'id': 'queer', 'name': 'Queer', 'jp': 'クィア', 'icon': 'icon_queer.png', 'color': '#f0fff4'},
    {'id': 'ally', 'name': 'Ally', 'jp': 'アライ', 'icon': 'icon_all.png', 'color': '#fffbeb'},
    {'id': 'all', 'name': 'All / Mix', 'jp': '誰でもOK', 'icon': 'icon_all.png', 'color': '#f8f9fa'},
]

COMMON_STYLE = '''
<style>
    :root { --pink: #ff6b81; }
    body { background-color: #fafbfc; font-family: sans-serif; color: #333; }
    .nav-bar { background: #fff; border-bottom: 1px solid #eee; padding: 15px 0; }
    .nav-link { color: #555; font-weight: 500; text-decoration: none; margin-left: 20px; }
    /* カテゴリボタンの調整 */
    .cat-card { border: none; border-radius: 16px; padding: 10px; text-decoration: none; color: #333; transition: 0.2s; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100px; border: 2px solid transparent; width: 100%; }
    .cat-card:hover { transform: translateY(-3px); box-shadow: 0 5px 15px rgba(0,0,0,0.05); }
    .cat-card.active { border-color: var(--pink); background-color: #fff !important; }
    .cat-icon-img { width: 32px; height: 32px; margin-bottom: 8px; }
    /* 検索バーの調整 */
    .search-input { border-radius: 10px; border: 1px solid #ddd; padding: 10px 15px; width: 100%; height: 45px; }
    /* 投稿カードの調整 */
    .event-card { border: none; border-radius: 20px; overflow: hidden; background: #fff; transition: 0.3s; height: 100%; display: flex; flex-direction: column; }
    .event-card:hover { transform: translateY(-5px); box-shadow: 0 10px 25px rgba(0,0,0,0.08); }
    .card-img-wrapper { position: relative; width: 100%; height: 200px; }
    .card-img-top { width: 100%; height: 100%; object-fit: cover; }
    .pickup-badge { position: absolute; top: 15px; left: 15px; background: var(--pink); color: #fff; padding: 4px 10px; border-radius: 8px; font-size: 11px; font-weight: bold; }
    .btn-pink { background: var(--pink); color: #fff; border-radius: 50px; border: none; padding: 10px 20px; font-weight: bold; }
</style>
'''

INDEX_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1">
    <title>LGBTQ+ Event Board</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
    ''' + COMMON_STYLE + '''
</head>
<body>
    <nav class="nav-bar shadow-sm">
        <div class="container d-flex justify-content-between align-items-center">
            <a class="fw-bold fs-4 text-decoration-none" href="/"><span style="color:var(--pink)">LGBTQ+</span> Event Board 🌈</a>
            <div class="d-flex align-items-center">
                <a href="/" class="nav-link" style="color:var(--pink)">イベントを探す</a>
                <a href="/post" class="nav-link">イベントを投稿</a>
                {% if current_user.is_authenticated %}
                    <a href="/logout" class="nav-link text-muted small">ログアウト ({{ current_user.username }})</a>
                {% else %}
                    <a href="/login" class="nav-link">ログイン</a>
                    <a href="/signup" class="nav-link">新規登録</a>
                {% endif %}
            </div>
        </div>
    </nav>

    <div class="container py-5">
        <h2 class="fw-bold mb-4">イベントを探す</h2>

        <!-- 🌟 カテゴリボタン：PCで横一列に並ぶように修正 -->
        <div class="row row-cols-2 row-cols-md-4 row-cols-lg-7 g-3 mb-5 flex-nowrap overflow-auto pb-2" style="scrollbar-width: none;">
            {% for cat in categories %}
            <div class="col" style="min-width: 120px;">
                <a href="/?category={{ cat.id }}" class="cat-card {% if active_cat == cat.id %}active{% endif %}" style="background-color: {{ cat.color }};">
                    <img src="{{ url_for('static', filename='images/uploads/' + cat.icon) }}" class="cat-icon-img" onerror="this.src='https://via.placeholder.com/32'">
                    <div class="fw-bold" style="font-size: 13px;">{{ cat.name }}</div>
                    <div class="text-muted" style="font-size: 10px;">({{ cat.jp }})</div>
                </a>
            </div>
            {% endfor %}
        </div>

        <!-- 検索・フィルター -->
        <form action="/" method="GET" class="row g-3 mb-5 align-items-center">
            <input type="hidden" name="category" value="{{ active_cat }}">
            <div class="col-6 col-md-2">
                <select name="area" class="form-select border-0 shadow-sm py-2" onchange="this.form.submit()">
                    <option value="">エリア</option>
                    <option value="東京" {% if request.args.get('area') == '東京' %}selected{% endif %}>東京</option>
                    <option value="大阪" {% if request.args.get('area') == '大阪' %}selected{% endif %}>大阪</option>
                    <option value="オンライン" {% if request.args.get('area') == 'オンライン' %}selected{% endif %}>オンライン</option>
                </select>
            </div>
            <div class="col-12 col-md-6">
                <div class="position-relative">
                    <input type="text" name="q" class="search-input border-0 shadow-sm" placeholder="キーワードで検索" value="{{ request.args.get('q', '') }}">
                    <i class="bi bi-search position-absolute" style="right:15px; top:12px; color:#999"></i>
                </div>
            </div>
            <div class="col-6 col-md-2 ms-auto">
                <select name="sort" class="form-select border-0 shadow-sm py-2" onchange="this.form.submit()">
                    <option value="new" {% if request.args.get('sort') == 'new' %}selected{% endif %}>新着順</option>
                    <option value="old" {% if request.args.get('sort') == 'old' %}selected{% endif %}>古い順</option>
                </select>
            </div>
        </form>

        <!-- 🌟 イベント一覧：細長さを解消して綺麗に並べる -->
        <div class="row row-cols-1 row-cols-sm-2 row-cols-lg-4 g-4">
            {% for event in events %}
            <div class="col">
                <div class="event-card shadow-sm border">
                    <div class="card-img-wrapper">
                        <img src="{{ event.image_url }}" class="card-img-top">
                        <div class="pickup-badge">PICK UP</div>
                    </div>
                    <div class="p-3">
                        <h6 class="fw-bold mb-2 text-truncate">{{ event.title }}</h6>
                        <div class="small text-muted mb-1"><i class="bi bi-calendar"></i> {{ event.date or '2024.06.01' }}</div>
                        <div class="small text-muted mb-3"><i class="bi bi-geo-alt"></i> {{ event.location }}</div>
                        <div class="d-flex justify-content-between align-items-center mt-auto">
                            <span class="badge rounded-pill bg-light text-primary border px-3 small">{{ event.category }}</span>
                            {% if current_user.is_authenticated and event.user_id == current_user.id|int %}
                                <a href="/edit/{{ event.id }}" class="text-muted"><i class="bi bi-pencil-square"></i></a>
                            {% endif %}
                        </div>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
    </div>
    <a href="/post" style="position:fixed; bottom:30px; right:30px; width:60px; height:60px; background:var(--pink); color:#fff; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:30px; box-shadow:0 5px 15px rgba(255,107,129,0.4); text-decoration:none;"><i class="bi bi-plus-lg"></i></a>
</body>
</html>
'''

SIGNUP_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ja">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1"><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">''' + COMMON_STYLE + '''</head>
<body>
    <div class="container py-5" style="max-width:400px;">
        <div class="card p-4 shadow border-0" style="border-radius:20px;">
            <h2 class="fw-bold mb-4">Signup</h2>
            <form method="POST">
                <div class="mb-3"><input type="text" name="username" class="form-control" placeholder="ユーザー名" required></div>
                <div class="mb-3"><input type="password" name="password" class="form-control" placeholder="パスワード" required></div>
                <button type="submit" class="btn btn-pink w-100 py-2">登録して始める</button>
            </form>
            <div class="text-center mt-3"><a href="/login" class="text-muted small">ログインはこちら</a></div>
        </div>
    </div>
</body>
</html>
'''

LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ja">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1"><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">''' + COMMON_STYLE + '''</head>
<body>
    <div class="container py-5" style="max-width:400px;">
        <div class="card p-4 shadow border-0" style="border-radius:20px;">
            <h2 class="fw-bold mb-4">Login</h2>
            <form method="POST">
                <div class="mb-3"><input type="text" name="username" class="form-control" placeholder="ユーザー名" required></div>
                <div class="mb-3"><input type="password" name="password" class="form-control" placeholder="パスワード" required></div>
                <button type="submit" class="btn btn-pink w-100 py-2">ログイン</button>
            </form>
            <div class="text-center mt-3"><a href="/signup" class="text-muted small">新規登録はこちら</a></div>
        </div>
    </div>
</body>
</html>
'''

POST_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ja">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1"><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">''' + COMMON_STYLE + '''</head>
<body>
    <div class="container py-5" style="max-width:600px;">
        <div class="card p-5 shadow border-0" style="border-radius:20px;">
            <h2 class="fw-bold mb-4">イベントを投稿</h2>
            <form method="POST" enctype="multipart/form-data">
                <div class="mb-3"><label class="form-label">タイトル</label><input type="text" name="title" class="form-control" required></div>
                <div class="mb-3"><label class="form-label">カテゴリ</label>
                    <select name="category" class="form-select">
                        {% for cat in categories if cat.id != 'all' %}<option value="{{ cat.id }}">{{ cat.name }}</option>{% endfor %}
                    </select>
                </div>
                <div class="mb-3"><label class="form-label">場所</label><input type="text" name="location" class="form-control" placeholder="例: 大阪・梅田"></div>
                <div class="mb-3"><label class="form-label">日付</label><input type="date" name="date" class="form-control"></div>
                <div class="mb-3"><label class="form-label">画像</label><input type="file" name="image" class="form-control"></div>
                <button type="submit" class="btn btn-pink w-100 py-3 mt-3">投稿する</button>
            </form>
        </div>
    </div>
</body>
</html>
'''

EDIT_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ja">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1"><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">''' + COMMON_STYLE + '''</head>
<body>
    <div class="container py-5" style="max-width:600px;">
        <div class="card p-5 shadow border-0" style="border-radius:20px;">
            <h2 class="fw-bold mb-4">編集する</h2>
            <form method="POST" enctype="multipart/form-data">
                <div class="mb-3"><label class="form-label">タイトル</label><input type="text" name="title" class="form-control" value="{{ event.title }}" required></div>
                <div class="mb-3"><label class="form-label">カテゴリ</label>
                    <select name="category" class="form-select">
                        {% for cat in categories if cat.id != 'all' %}
                        <option value="{{ cat.id }}" {% if event.category == cat.id %}selected{% endif %}>{{ cat.name }}</option>
                        {% endfor %}
                    </select>
                </div>
                <div class="mb-3"><label class="form-label">場所</label><input type="text" name="location" class="form-control" value="{{ event.location }}"></div>
                <div class="mb-3"><label class="form-label">画像を変更</label><input type="file" name="image" class="form-control"></div>
                <button type="submit" class="btn btn-pink w-100 py-3 mt-3">更新する</button>
            </form>
            <form action="/delete/{{ event.id }}" method="POST" class="mt-3" onsubmit="return confirm('本当に削除しますか？')">
                <button type="submit" class="btn btn-link w-100 text-danger text-decoration-none">削除する</button>
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
    cat = request.args.get('category', 'all')
    area = request.args.get('area', '')
    query = request.args.get('q', '').lower()
    sort = request.args.get('sort', 'new')
    filtered = all_events
    if cat != 'all': filtered = [e for e in filtered if e.get('category') == cat]
    if area: filtered = [e for e in filtered if area in e.get('location', '')]
    if query: filtered = [e for e in filtered if query in e.get('title', '').lower()]
    if sort == 'new': filtered.reverse()
    return render_template_string(INDEX_TEMPLATE, events=filtered, categories=categories, active_cat=cat, current_user=current_user)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username, password = request.form.get('username'), request.form.get('password')
        users = load_users_data()
        if any(u['username'] == username for u in users): return "重複", 400
        new_id = len(users)+1
        users.append({"id": new_id, "username": username, "password": generate_password_hash(password)})
        save_users_data(users)
        login_user(User(new_id, username))
        return redirect(url_for('index'))
    return render_template_string(SIGNUP_TEMPLATE)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username, password = request.form.get('username'), request.form.get('password')
        user_data = next((u for u in load_users_data() if u['username'] == username), None)
        if user_data and check_password_hash(user_data['password'], password):
            login_user(User(user_data['id'], user_data['username']))
            return redirect(url_for('index'))
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/logout')
def logout():
    logout_user(); return redirect(url_for('index'))

@app.route('/post', methods=['GET', 'POST'])
@login_required
def post():
    if request.method == 'POST':
        events = load_events()
        image_file = request.files.get('image')
        image_url = "https://via.placeholder.com/500"
        if image_file and image_file.filename != '':
            filename = secure_filename(image_file.filename)
            if not os.path.exists(UPLOAD_FOLDER): os.makedirs(UPLOAD_FOLDER)
            image_file.save(os.path.join(UPLOAD_FOLDER, filename))
            image_url = '/static/images/uploads/' + filename
        events.append({"id": int(os.urandom(4).hex(), 16), "user_id": int(current_user.id), "title": request.form.get('title'), "category": request.form.get('category'), "location": request.form.get('location'), "date": request.form.get('date'), "image_url": image_url})
        save_events(events)
        return redirect(url_for('index'))
    return render_template_string(POST_TEMPLATE, categories=categories)

@app.route('/edit/<int:event_id>', methods=['GET', 'POST'])
@login_required
def edit_event(event_id):
    events = load_events()
    event = next((e for e in events if e.get('id') == event_id), None)
    if not event or event.get('user_id') != int(current_user.id): return "権限なし", 403
    if request.method == 'POST':
        event['title'], event['location'], event['category'] = request.form.get('title'), request.form.get('location'), request.form.get('category')
        image_file = request.files.get('image')
        if image_file and image_file.filename != '':
            filename = secure_filename(image_file.filename)
            image_file.save(os.path.join(UPLOAD_FOLDER, filename))
            event['image_url'] = '/static/images/uploads/' + filename
        save_events(events); return redirect(url_for('index'))
    return render_template_string(EDIT_TEMPLATE, event=event, categories=categories)

@app.route('/delete/<int:event_id>', methods=['POST'])
@login_required
def delete_event(event_id):
    events = load_events()
    save_events([e for e in events if e.get('id') != event_id])
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))