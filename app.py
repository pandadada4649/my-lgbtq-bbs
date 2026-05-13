import json
import os
import urllib.parse
import datetime
from flask import Flask, render_template_string, request, redirect, url_for, flash
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
        <div class="row row-cols-1 row-cols-md-2 row-cols-lg-3 g-4 text-start">
            {% for event in events %}
            <div class="col">
                <div class="card h-100 shadow-sm">
                    <a href="/event/{{ event.id }}"><img src="{{ event.image_url }}" class="card-img-top event-image"></a>
                    <div class="card-body p-4">
                        <h5 class="card-title fw-bold"><a href="/event/{{ event.id }}" class="text-decoration-none text-dark">{{ event.title }}</a></h5>
                        <p class="small text-muted mb-3"><i class="bi bi-geo-alt"></i> {{ event.location }}</p>
                        
                        {# 本人の投稿なら編集・削除ボタンを出す #}
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

# --- 新規登録・ログインは同じなので省略（そよかぜさんの完全版を流用してください） ---
SIGNUP_TEMPLATE = '''...'''
LOGIN_TEMPLATE = '''...'''

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
                <div class="mb-3"><label class="form-label">内容説明</label><textarea name="description" class="form-control" rows="4"></textarea></div>
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
            <form method="POST">
                <div class="mb-3"><label class="form-label">タイトル</label><input type="text" name="title" class="form-control" value="{{ event.title }}" required></div>
                <div class="mb-3"><label class="form-label">場所</label><input type="text" name="location" class="form-control" value="{{ event.location }}"></div>
                <div class="mb-3"><label class="form-label">内容説明</label><textarea name="description" class="form-control" rows="4">{{ event.description }}</textarea></div>
                <button type="submit" class="btn btn-pink w-100 py-2 fw-bold">更新する</button>
                <a href="/" class="btn btn-link w-100 mt-2 text-decoration-none text-muted">キャンセル</a>
            </form>
        </div>
    </div>
</body>
</html>
'''

# --- ルート設定 ---

@app.route('/')
def index():
    return render_template_string(INDEX_TEMPLATE, events=load_events(), categories=categories, current_user=current_user)

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
        
        new_event = {
            "id": int(os.urandom(4).hex(), 16),
            "user_id": int(current_user.id), # 🌟 ここで投稿主のIDを保存！
            "title": request.form.get('title'),
            "category": request.form.get('category'),
            "location": request.form.get('location'),
            "description": request.form.get('description'),
            "image_url": image_url
        }
        events.append(new_event)
        save_events(events)
        return redirect(url_for('index'))
    return render_template_string(POST_TEMPLATE, categories=categories)

@app.route('/edit/<int:event_id>', methods=['GET', 'POST'])
@login_required
def edit_event(event_id):
    events = load_events()
    event = next((e for e in events if e.get('id') == event_id), None)
    
    # 🌟 持ち主チェック：本人じゃない場合は追い返す！
    if not event or event.get('user_id') != int(current_user.id):
        return "編集権限がありません", 403
    
    if request.method == 'POST':
        event['title'] = request.form.get('title')
        event['location'] = request.form.get('location')
        event['description'] = request.form.get('description')
        save_events(events)
        return redirect(url_for('index'))
        
    return render_template_string(EDIT_TEMPLATE, event=event)

@app.route('/delete/<int:event_id>', methods=['POST'])
@login_required
def delete_event(event_id):
    events = load_events()
    event = next((e for e in events if e.get('id') == event_id), None)
    
    # 🌟 持ち主チェック：本人じゃない場合は追い返す！
    if not event or event.get('user_id') != int(current_user.id):
        return "削除権限がありません", 403
        
    new_events = [e for e in events if e.get('id') != event_id]
    save_events(new_events)
    return redirect(url_for('index'))

# --- (以下、login/signup/logout等はそのまま継続) ---
# --- ユーザー登録画面 (Signup) ---
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        users = load_users_data()
        
        # 同じ名前のユーザーがいないかチェック
        if any(u['username'] == username for u in users):
            return "この名前は既に使われています", 400
        
        # パスワードを安全にハッシュ化して保存
        hashed_pw = generate_password_hash(password)
        new_user = {
            "id": len(users) + 1,
            "username": username,
            "password": hashed_pw
        }
        users.append(new_user)
        save_users_data(users)
        return redirect(url_for('login'))
    
    return render_template_string(SIGNUP_TEMPLATE)

# --- ログイン画面 (Login) ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        users = load_users_data()
        user_data = next((u for u in users if u['username'] == username), None)
        
        # パスワードが合っているかチェック
        if user_data and check_password_hash(user_data['password'], password):
            user_obj = User(user_data['id'], user_data['username'])
            login_user(user_obj)
            return redirect(url_for('index'))
        else:
            return "ユーザー名またはパスワードが違います", 401
            
    return render_template_string(LOGIN_TEMPLATE)

# --- ログアウト ---
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# --- 実行 ---
if __name__ == '__main__':
    # Render環境に合わせてポート番号を取得
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)