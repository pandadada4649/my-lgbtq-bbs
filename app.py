import json
import os
import urllib.parse
import datetime
from flask import Flask, render_template_string, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
# --- ログイン・セキュリティ用の道具を追加 ---
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'soyoka-secret-key' # セッション管理用の秘密鍵

# --- パス設定 ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_PATH = os.path.join(BASE_DIR, 'events.json')
USER_PATH = os.path.join(BASE_DIR, 'users.json')
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static/uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# --- ログイン管理の設定 ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' # 未ログイン時に飛ばすページ

# ユーザー情報を扱うクラス（エンジニアの仕事：クラス設計）
class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

# IDからユーザーを探す（ログイン維持に必要）
@login_manager.user_loader
def load_user(user_id):
    users = load_users_data()
    user_data = next((u for u in users if str(u['id']) == str(user_id)), None)
    if user_data:
        return User(user_data['id'], user_data['username'])
    return None

# データ読み書き用関数（バックエンドの仕事）
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

# カテゴリ定義
categories = [
    {'id': 'all', 'name': 'All / Mix', 'icon': 'all.png'},
    {'id': 'lesbian', 'name': 'Lesbian', 'icon': 'les.png'},
    {'id': 'gay', 'name': 'Gay', 'icon': 'gay.png'},
    {'id': 'bisexual', 'name': 'Bisexual', 'icon': 'bi.png'},
    {'id': 'transgender', 'name': 'Transgender', 'icon': 'trans.png'},
    {'id': 'queer', 'name': 'Queer', 'icon': 'queer.png'},
]

# --- 共通スタイル（ログイン状態による表示切替用） ---
COMMON_STYLE = '''
<style>
    body { background: linear-gradient(135deg, #fef1f2 0%, #fff5f7 100%); font-family: sans-serif; color: #444; }
    .card { border: none; border-radius: 24px; background: #fff; transition: 0.3s; }
    .card:hover { transform: translateY(-8px); box-shadow: 0 15px 30px rgba(255,107,129,0.1) !important; }
    .post-button { position: fixed; bottom: 30px; right: 30px; width: 65px; height: 65px; background: #ff6b81; color: #fff; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 30px; box-shadow: 0 8px 20px rgba(255,107,129,0.4); text-decoration: none; }
</style>
'''

# --- 1. ユーザー登録画面 (Signup) ---
SIGNUP_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8"><title>ユーザー登録</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    ''' + COMMON_STYLE + '''
</head>
<body>
    <div class="container py-5" style="max-width: 400px;">
        <div class="card p-4 shadow-sm">
            <h2 class="mb-4 fw-bold">Signup</h2>
            <form method="POST">
                <div class="mb-3"><label class="form-label">ユーザー名</label><input type="text" name="username" class="form-control" required></div>
                <div class="mb-3"><label class="form-label">パスワード</label><input type="password" name="password" class="form-control" required></div>
                <button type="submit" class="btn btn-primary w-100 rounded-pill" style="background:#ff6b81; border:none;">登録する</button>
            </form>
            <div class="mt-3 text-center"><a href="/login">ログインはこちら</a></div>
        </div>
    </div>
</body>
</html>
'''

# --- 2. ログイン画面 (Login) ---
LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8"><title>ログイン</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    ''' + COMMON_STYLE + '''
</head>
<body>
    <div class="container py-5" style="max-width: 400px;">
        <div class="card p-4 shadow-sm">
            <h2 class="mb-4 fw-bold">Login</h2>
            <form method="POST">
                <div class="mb-3"><label class="form-label">ユーザー名</label><input type="text" name="username" class="form-control" required></div>
                <div class="mb-3"><label class="form-label">パスワード</label><input type="password" name="password" class="form-control" required></div>
                <button type="submit" class="btn btn-primary w-100 rounded-pill" style="background:#ff6b81; border:none;">ログイン</button>
            </form>
            <div class="mt-3 text-center"><a href="/signup">新規登録はこちら</a></div>
        </div>
    </div>
</body>
</html>
'''

# 既存の INDEX_TEMPLATE や DETAIL_TEMPLATE は、current_user を使えるように調整する必要がありますが、
# まずは登録・ログインが動くことを確認するための最小構成で進めます。

# --- 登録ルート ---
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        users = load_users_data()
        
        # すでに同じ名前のユーザーがいないかチェック
        if any(u['username'] == username for u in users):
            return "この名前は既に使われています", 400
        
        # エンジニアの仕事：パスワードを「ハッシュ化」して安全に保存
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

# --- ログインルート ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        users = load_users_data()
        user_data = next((u for u in users if u['username'] == username), None)
        
        # 暗号化されたパスワードと一致するかチェック
        if user_data and check_password_hash(user_data['password'], password):
            user_obj = User(user_data['id'], user_data['username'])
            login_user(user_obj)
            return redirect(url_for('index'))
        else:
            return "ログイン失敗。ユーザー名かパスワードが違います。", 401
    return render_template_string(LOGIN_TEMPLATE)

# --- ログアウトルート ---
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# index ルートなどは以前のものを流用し、@login_required などを付けていきますが
# 長くなりすぎるので一旦ここまでで動作確認しましょう！

@app.route('/')
def index():
    all_events = load_events()
    active_cat = request.args.get('category', 'all')
    events = all_events if active_cat == 'all' else [e for e in all_events if e['category'] == active_cat]
    # ログインしているかどうかの情報を渡す
    return render_template_string(f"""
        <h1>LGBTQ+ 掲示板</h1>
        <p>こんにちは、{{{{ current_user.username if current_user.is_authenticated else 'ゲスト' }}}}さん</p>
        <nav>
            <a href="/signup">新規登録</a> | <a href="/login">ログイン</a> | <a href="/logout">ログアウト</a>
        </nav>
        <hr>
        <a href="/post">＋投稿する</a>
        <ul>
            {{% for event in events %}}
            <li>{{{{ event.title }}}} ({{{{ event.category }}}})</li>
            {{% endfor %}}
        </ul>
    """, events=events, current_user=current_user)

@app.route('/post', methods=['GET', 'POST'])
@login_required # ログインしていないと投稿できないようにする
def post():
    # 以前の投稿ロジックをここに書きます（※長くなるので省略していますが、そよかぜさんの元のコードを合体させてOKです）
    return "投稿画面（ここに以前のフォームを入れます）"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)