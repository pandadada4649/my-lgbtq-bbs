import json
import os
from flask import Flask, render_template_string, request, redirect, url_for
from werkzeug.utils import secure_filename
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'soyoka-secret-key'

# --- パス設定 ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_PATH = os.path.join(BASE_DIR, 'events.json')
USER_PATH = os.path.join(BASE_DIR, 'users.json')
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static/uploads')
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

# --- データ処理 ---
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

# --- 🌟 カテゴリ定義（ここが消えていました！） ---
categories = [
    {'id': 'all', 'name': 'All / Mix'},
    {'id': 'lesbian', 'name': 'Lesbian'},
    {'id': 'gay', 'name': 'Gay'},
    {'id': 'bisexual', 'name': 'Bisexual'},
    {'id': 'transgender', 'name': 'Transgender'},
    {'id': 'queer', 'name': 'Queer'},
]

COMMON_STYLE = '''
<style>
    body { background: linear-gradient(135deg, #fef1f2 0%, #fff5f7 100%); font-family: sans-serif; color: #444; min-height: 100vh; }
    .card { border: none; border-radius: 24px; background: #fff; transition: 0.3s; }
    .card:hover { transform: translateY(-8px); box-shadow: 0 15px 30px rgba(255,107,129,0.1) !important; }
    .event-image { height: 220px; object-fit: cover; border-radius: 24px 24px 0 0; }
    .post-button { position: fixed; bottom: 30px; right: 30px; width: 65px; height: 65px; background: #ff6b81; color: #fff !important; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 30px; box-shadow: 0 8px 20px rgba(255,107,129,0.4); text-decoration: none; }
    .btn-pink { background-color: #ff6b81; color: white !important; border-radius: 50px; border: none; }
    .btn-outline-pink { border-color: #ff6b81; color: #ff6b81; border-radius: 50px; }
    .nav-pills .nav-link { color: #ff6b81; border-radius: 50px; margin: 0 5px; }
    .nav-pills .nav-link.active { background-color: #ff6b81 !important; color: white !important; }
</style>
'''

# --- テンプレート ---

INDEX_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8"><title>LGBTQ+ Events</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
    ''' + COMMON_STYLE + '''
</head>
<body>
    <div class="container mt-3 d-flex justify-content-end align-items-center">
        {% if current_user.is_authenticated %}
            <span class="me-3 small text-muted">こんにちは、{{ current_user.username }}さん</span>
            <a href="/logout" class="btn btn-outline-secondary btn-sm rounded-pill">ログアウト</a>
        {% else %}
            <a href="/login" class="btn btn-outline-pink btn-sm me-2">ログイン</a>
            <a href="/signup" class="btn btn-pink btn-sm">新規登録</a>
        {% endif %}
    </div>
    <div class="container py-5 text-center">
        <h1 class="fw-bold mb-5" style="color: #ff6b81;">🌈 LGBTQ+ Events</h1>
        
        {# 🌟 カテゴリボタン復活！ #}
        <ul class="nav nav-pills justify-content-center mb-5">
            {% for cat in categories %}
            <li class="nav-item">
                <a class="nav-link {% if active_cat == cat.id %}active{% endif %}" href="/?category={{ cat.id }}">
                    {{ cat.name }}
                </a>
            </li>
            {% endfor %}
        </ul>

        <div class="row row-cols-1 row-cols-md-2 row-cols-lg-3 g-4 text-start">
            {% for event in events %}
            <div class="col">
                <div class="card h-100 shadow-sm">
                    <a href="/event/{{ event.id }}"><img src="{{ event.image_url }}" class="card-img-top event-image"></a>
                    <div class="card-body p-4">
                        <h5 class="card-title fw-bold"><a href="/event/{{ event.id }}" class="text-decoration-none text-dark">{{ event.title }}</a></h5>
                        <p class="small text-muted mb-3"><i class="bi bi-geo-alt"></i> {{ event.location }}</p>
                        {% if current_user.is_authenticated and event.user_id == current_user.id|int %}
                        <div class="d-flex gap-2 border-top pt-3 mt-2">
                            <a href="/edit/{{ event.id }}" class="btn btn-sm btn-outline-secondary rounded-pill">編集</a>
                            <form action="/delete/{{ event.id }}" method="POST" onsubmit="return confirm('本当に削除しますか？');">
                                <button type="submit" class="btn btn-sm btn-outline-danger rounded-pill">削除</button>
                            </form>
                        </div>
                        {% endif %}
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

# --- (以下、SIGNUP, LOGIN, POST, EDIT, DETAIL 等のテンプレートは前回同様) ---
SIGNUP_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ja">
<head><meta charset="UTF-8"><title>新規登録</title><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">''' + COMMON_STYLE + '''</head>
<body>
    <div class="container py-5" style="max-width: 400px;">
        <div class="card p-4 shadow-sm">
            <h2 class="mb-4 fw-bold">Signup</h2>
            <form method="POST">
                <div class="mb-3"><label class="form-label">ユーザー名</label><input type="text" name="username" class="form-control" required></div>
                <div class="mb-3"><label class="form-label">パスワード</label><input type="password" name="password" class="form-control" required></div>
                <button type="submit" class="btn btn-pink w-100 py-2 fw-bold">登録する</button>
            </form>
            <div class="mt-4 text-center">
                <p class="small text-muted mb-0">すでにアカウントをお持ちですか？</p>
                <a href="/login" class="text-decoration-none" style="color: #ff6b81;">ログインはこちら</a>
            </div>
        </div>
    </div>
</body>
</html>
'''

LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ja">
<head><meta charset="UTF-8"><title>ログイン</title><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">''' + COMMON_STYLE + '''</head>
<body>
    <div class="container py-5" style="max-width: 400px;">
        <div class="card p-4 shadow-sm">
            <h2 class="mb-4 fw-bold">Login</h2>
            <form method="POST">
                <div class="mb-3"><label class="form-label">ユーザー名</label><input type="text" name="username" class="form-control" required></div>
                <div class="mb-3"><label class="form-label">パスワード</label><input type="password" name="password" class="form-control" required></div>
                <button type="submit" class="btn btn-pink w-100 py-2 fw-bold">ログイン</button>
            </form>
            <div class="mt-4 text-center">
                <p class="small text-muted mb-0">初めてご利用ですか？</p>
                <a href="/signup" class="text-decoration-none" style="color: #ff6b81;">新規登録はこちら</a>
            </div>
        </div>
    </div>
</body>
</html>
'''

POST_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ja">
<head><meta charset="UTF-8"><title>新規投稿</title><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">''' + COMMON_STYLE + '''</head>
<body>
    <div class="container py-5" style="max-width: 600px;">
        <div class="card p-5 shadow">
            <h2 class="mb-4 fw-bold">イベントを投稿</h2>
            <form method="POST" enctype="multipart/form-data">
                <div class="mb-3"><label class="form-label">タイトル</label><input type="text" name="title" class="form-control" required></div>
                <div class="mb-3"><label class="form-label">カテゴリ</label>
                    <select name="category" class="form-select">
                        {% for cat in categories if cat.id != 'all' %}<option value="{{ cat.id }}">{{ cat.name }}</option>{% endfor %}
                    </select>
                </div>
                <div class="mb-3"><label class="form-label">場所</label><input type="text" name="location" class="form-control"></div>
                <div class="mb-3"><label class="form-label">画像</label><input type="file" name="image" class="form-control"></div>
                <button type="submit" class="btn btn-pink w-100 py-2 fw-bold">投稿する</button>
            </form>
        </div>
    </div>
</body>
</html>
'''

EDIT_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ja">
<head><meta charset="UTF-8"><title>編集</title><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">''' + COMMON_STYLE + '''</head>
<body>
    <div class="container py-5" style="max-width: 600px;">
        <div class="card p-5 shadow">
            <h2 class="mb-4 fw-bold">投稿を編集</h2>
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
                <div class="mb-3">
                    <label class="form-label">現在の画像</label><br>
                    <img src="{{ event.image_url }}" style="width: 100px; border-radius: 8px; margin-bottom: 10px;">
                    <input type="file" name="image" class="form-control">
                </div>
                <button type="submit" class="btn btn-pink w-100 py-2 fw-bold">更新する</button>
            </form>
        </div>
    </div>
</body>
</html>
'''

DETAIL_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ja">
<head><meta charset="UTF-8"><title>{{ event.title }}</title><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">''' + COMMON_STYLE + '''</head>
<body>
    <div class="container py-5" style="max-width: 800px;">
        <div class="card overflow-hidden shadow">
            <img src="{{ event.image_url }}" class="w-100" style="height:400px; object-fit:cover;">
            <div class="p-5">
                <h1 class="fw-bold mb-3">{{ event.title }}</h1>
                <p class="text-muted"><i class="bi bi-geo-alt"></i> {{ event.location }}</p>
                <hr class="my-5">
                <a href="/" class="btn btn-outline-secondary rounded-pill">戻る</a>
            </div>
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
    # 🌟 カテゴリで絞り込み
    events = all_events if active_cat == 'all' else [e for e in all_events if e.get('category') == active_cat]
    return render_template_string(INDEX_TEMPLATE, events=events, categories=categories, active_cat=active_cat, current_user=current_user)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username, password = request.form.get('username'), request.form.get('password')
        users = load_users_data()
        if any(u['username'] == username for u in users): return "名前重複", 400
        
        new_user_id = len(users)+1
        users.append({"id": new_user_id, "username": username, "password": generate_password_hash(password)})
        save_users_data(users)

        # 🌟 登録即ログイン機能！
        user_obj = User(new_user_id, username)
        login_user(user_obj)
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
        return "失敗", 401
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/logout')
@login_required
def logout():
    logout_user(); return redirect(url_for('index'))

@app.route('/event/<int:event_id>')
def event_detail(event_id):
    event = next((e for e in load_events() if e.get('id') == event_id), None)
    if not event: return "NotFound", 404
    return render_template_string(DETAIL_TEMPLATE, event=event)

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
            image_url = '/static/uploads/' + filename
        events.append({"id": int(os.urandom(4).hex(), 16), "user_id": int(current_user.id), "title": request.form.get('title'), "category": request.form.get('category'), "location": request.form.get('location'), "image_url": image_url})
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
        event['title'] = request.form.get('title')
        event['location'] = request.form.get('location')
        event['category'] = request.form.get('category')
        
        image_file = request.files.get('image')
        if image_file and image_file.filename != '':
            filename = secure_filename(image_file.filename)
            image_file.save(os.path.join(UPLOAD_FOLDER, filename))
            event['image_url'] = '/static/uploads/' + filename

        save_events(events); return redirect(url_for('index'))
    return render_template_string(EDIT_TEMPLATE, event=event, categories=categories)

@app.route('/delete/<int:event_id>', methods=['POST'])
@login_required
def delete_event(event_id):
    events = load_events()
    event = next((e for e in events if e.get('id') == event_id), None)
    if not event or event.get('user_id') != int(current_user.id): return "権限なし", 403
    save_events([e for e in events if e.get('id') != event_id])
    return redirect(url_for('index'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)