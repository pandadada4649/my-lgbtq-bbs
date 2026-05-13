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

# --- ログイン管理の設定 ---
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
    if user_data:
        return User(user_data['id'], user_data['username'])
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

categories = [
    {'id': 'all', 'name': 'All / Mix', 'icon': 'all.png'},
    {'id': 'lesbian', 'name': 'Lesbian', 'icon': 'les.png'},
    {'id': 'gay', 'name': 'Gay', 'icon': 'gay.png'},
    {'id': 'bisexual', 'name': 'Bisexual', 'icon': 'bi.png'},
    {'id': 'transgender', 'name': 'Transgender', 'icon': 'trans.png'},
    {'id': 'queer', 'name': 'Queer', 'icon': 'queer.png'},
]

COMMON_STYLE = '''
<style>
    body { background: linear-gradient(135deg, #fef1f2 0%, #fff5f7 100%); font-family: sans-serif; color: #444; }
    .card { border: none; border-radius: 24px; background: #fff; transition: 0.3s; }
    .card:hover { transform: translateY(-8px); box-shadow: 0 15px 30px rgba(255,107,129,0.1) !important; }
    .event-image { height: 220px; object-fit: cover; border-radius: 24px 24px 0 0; }
    .post-button { position: fixed; bottom: 30px; right: 30px; width: 65px; height: 65px; background: #ff6b81; color: #fff; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 30px; box-shadow: 0 8px 20px rgba(255,107,129,0.4); text-decoration: none; transition: 0.3s; }
    .post-button:hover { transform: scale(1.1) rotate(90deg); color: #fff; }
</style>
'''

# --- 各テンプレート ---
SIGNUP_TEMPLATE = '''...（省略：そよかぜさんのコードと同じ）...''' # 実際はここに以前のHTMLを入れます
LOGIN_TEMPLATE = '''...（省略：そよかぜさんのコードと同じ）...'''

INDEX_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8"><title>LGBTQ+ イベント掲示板</title>
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
            <a href="/login" class="btn btn-outline-pink btn-sm rounded-pill me-2" style="color: #ff6b81; border-color: #ff6b81;">ログイン</a>
            <a href="/signup" class="btn btn-sm rounded-pill text-white" style="background-color: #ff6b81;">新規登録</a>
        {% endif %}
    </div>
    <div class="container py-5">
        <h1 class="text-center fw-bold mb-5" style="color: #ff6b81;">🌈 LGBTQ+ Events</h1>
        <ul class="nav nav-pills justify-content-center mb-5">
            {% for cat in categories %}
            <li class="nav-item">
                <a class="nav-link {% if active_cat == cat.id %}active{% endif %}" href="/?category={{ cat.id }}">
                    <img src="/static/images/icon_{{ cat.icon }}" style="width:20px;"> {{ cat.name }}
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
                        <h5 class="card-title fw-bold"><a href="/event/{{ event.id }}" class="text-decoration-none text-dark">{{ event.title }}</a></h5>
                        <p class="small text-muted"><i class="bi bi-geo-alt"></i> {{ event.location }}</p>
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

# --- (上部は省略：importからcategoriesの定義まではそのままでOK) ---

# --- ルート設定（ここが命！） ---

@app.route('/')
def index():
    all_events = load_events()
    active_cat = request.args.get('category', 'all')
    events = all_events if active_cat == 'all' else [e for e in all_events if e['category'] == active_cat]
    return render_template_string(INDEX_TEMPLATE, events=events, categories=categories, active_cat=active_cat, current_user=current_user)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        users = load_users_data()
        if any(u['username'] == username for u in users): return "この名前は既に使われています", 400
        hashed_pw = generate_password_hash(password)
        users.append({"id": len(users) + 1, "username": username, "password": hashed_pw})
        save_users_data(users)
        return redirect(url_for('login'))
    return render_template_string(SIGNUP_TEMPLATE)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        users = load_users_data()
        user_data = next((u for u in users if u['username'] == username), None)
        if user_data and check_password_hash(user_data['password'], password):
            login_user(User(user_data['id'], user_data['username']))
            return redirect(url_for('index'))
        return "ログイン失敗", 401
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/event/<int:event_id>')
def event_detail(event_id):
    events = load_events()
    event = next((e for e in events if e.get('id') == event_id), None)
    if event is None: return "NotFound", 404
    share_text = urllib.parse.quote(f"🌈 LGBTQ+ イベント：{event['title']}")
    share_url = urllib.parse.quote(request.url)
    return render_template_string(DETAIL_TEMPLATE, event=event, share_text=share_text, share_url=share_url)

@app.route('/comment/<int:event_id>', methods=['POST'])
def add_comment(event_id):
    events = load_events()
    comment_text = request.form.get('comment')
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    for e in events:
        if e.get('id') == event_id:
            if 'comments' not in e: e['comments'] = []
            e['comments'].append({"text": comment_text, "date": now})
            break
    save_events(events)
    return redirect(url_for('event_detail', event_id=event_id))

@app.route('/post', methods=['GET', 'POST'])
@login_required # ログインしていないと投稿できない
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
            "tags": [t.strip() for t in request.form.get('tags').split(',')] if request.form.get('tags') else [],
            "comments": []
        }
        events.append(new_event)
        save_events(events)
        return redirect(url_for('index'))
    return render_template_string(POST_TEMPLATE, categories=categories)

@app.route('/delete/<int:event_id>', methods=['POST'])
def delete_event(event_id):
    # ここは管理者パスワードのままでも、ログインユーザー判定に変えてもOKです
    if request.form.get('password') == "soyoka_admin":
        events = load_events()
        save_events([e for e in events if e.get('id') != event_id])
    return redirect(url_for('index'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)