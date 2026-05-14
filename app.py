import os
from flask import Flask, render_template_string, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'soyoka-secret-key'

# --- 🌟 インフラ設定：DBの接続先 ---
database_url = os.environ.get('DATABASE_URL')
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///local_test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- 🌟 データモデル（データベースの設計図） ---
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50))
    area = db.Column(db.String(50)) # 関西・関東など
    location_detail = db.Column(db.String(200)) # 詳細な場所
    date = db.Column(db.String(50))
    image_url = db.Column(db.String(500))

# データベースの初期化
with app.app_context():
    db.create_all()

# --- ログイン管理 ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- カテゴリ・エリア定義 ---
categories = [
    {'id': 'all', 'name': 'All / Mix', 'jp': '誰でもOK', 'icon': 'icon_all.png', 'color': '#f8f9fa'},
    {'id': 'lesbian', 'name': 'Lesbian', 'jp': 'レズビアン', 'icon': 'icon_les.png', 'color': '#fff0f3'},
    {'id': 'gay', 'name': 'Gay', 'jp': 'ゲイ', 'icon': 'icon_gay.png', 'color': '#fff4ec'},
    {'id': 'bisexual', 'name': 'Bisexual', 'jp': 'バイセクシュアル', 'icon': 'icon_bi.png', 'color': '#f3f0ff'},
    {'id': 'transgender', 'name': 'Transgender', 'jp': 'トランスジェンダー', 'icon': 'icon_trans.png', 'color': '#eef9ff'},
    {'id': 'queer', 'name': 'Queer', 'jp': 'クィア', 'icon': 'icon_queer.png', 'color': '#f0fff4'},
    {'id': 'ally', 'name': 'Ally', 'jp': 'アライ', 'icon': 'icon_all.png', 'color': '#fffbeb'},
]

COMMON_STYLE = '''
<style>
    :root { --pink: #ff6b81; }
    body { background-color: #fafbfc; font-family: sans-serif; color: #333; }
    .nav-bar { background: #fff; border-bottom: 1px solid #eee; padding: 15px 0; }
    .cat-card { border: none; border-radius: 16px; padding: 10px; text-decoration: none; color: #333; transition: 0.2s; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 110px; border: 2px solid transparent; width: 100%; }
    .cat-card:hover { transform: translateY(-3px); box-shadow: 0 5px 15px rgba(0,0,0,0.05); }
    .cat-card.active { border-color: var(--pink); background-color: #fff !important; }
    .cat-icon-img { width: 45px; height: 45px; object-fit: contain; margin-bottom: 8px; }
    .event-card { border: none; border-radius: 20px; overflow: hidden; background: #fff; transition: 0.3s; height: 100%; display: flex; flex-direction: column; }
    .event-card:hover { transform: translateY(-5px); box-shadow: 0 10px 25px rgba(0,0,0,0.08); }
    .pickup-badge { position: absolute; top: 15px; left: 15px; background: var(--pink); color: #fff; padding: 4px 10px; border-radius: 8px; font-size: 11px; font-weight: bold; }
    .btn-pink { background: var(--pink); color: #fff; border-radius: 50px; border: none; padding: 10px 20px; font-weight: bold; }
</style>
'''

# --- テンプレート (INDEX, POST, EDIT, LOGIN, SIGNUP) ---
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
    <nav class="nav-bar shadow-sm mb-4">
        <div class="container d-flex justify-content-between align-items-center">
            <a class="fw-bold fs-4 text-decoration-none" href="/"><span style="color:var(--pink)">LGBTQ+</span> Event Board 🌈</a>
            <div class="d-flex align-items-center">
                <a href="/" class="nav-link text-decoration-none me-3" style="color:var(--pink)">イベントを探す</a>
                <a href="/post" class="nav-link text-decoration-none me-3 text-dark">イベントを投稿</a>
                {% if current_user.is_authenticated %}
                    <a href="/logout" class="btn btn-outline-secondary btn-sm rounded-pill small">Logout ({{ current_user.username }})</a>
                {% else %}
                    <a href="/login" class="btn btn-outline-pink btn-sm me-2">ログイン</a>
                    <a href="/signup" class="btn btn-pink btn-sm">新規登録</a>
                {% endif %}
            </div>
        </div>
    </nav>

    <div class="container pb-5">
        <h2 class="fw-bold mb-4">イベントを探す</h2>

        <div class="row row-cols-2 row-cols-md-4 row-cols-lg-7 g-3 mb-5">
            {% for cat in categories %}
            <div class="col">
                <a href="/?category={{ cat.id }}" class="cat-card {% if active_cat == cat.id %}active{% endif %}" style="background-color: {{ cat.color }};">
                    <img src="{{ url_for('static', filename='images/' + cat.icon) }}" class="cat-icon-img" onerror="this.src='https://via.placeholder.com/45?text=Icon'">
                    <div class="fw-bold" style="font-size: 13px;">{{ cat.name }}</div>
                    <div class="text-muted" style="font-size: 10px;">({{ cat.jp }})</div>
                </a>
            </div>
            {% endfor %}
        </div>

        <form action="/" method="GET" class="row g-3 mb-5 align-items-center">
            <input type="hidden" name="category" value="{{ active_cat }}">
            <div class="col-6 col-md-2">
                <select name="area" class="form-select border-0 shadow-sm" onchange="this.form.submit()">
                    <option value="">エリア</option>
                    {% for a in ['関西', '関東', 'オンライン', 'その他'] %}
                    <option value="{{ a }}" {% if request.args.get('area') == a %}selected{% endif %}>{{ a }}</option>
                    {% endfor %}
                </select>
            </div>
            <div class="col-12 col-md-6">
                <div class="position-relative">
                    <input type="text" name="q" class="form-control border-0 shadow-sm" style="border-radius:10px; height:45px;" placeholder="キーワードで検索" value="{{ request.args.get('q', '') }}">
                    <i class="bi bi-search position-absolute" style="right:15px; top:12px; color:#999"></i>
                </div>
            </div>
            <div class="col-6 col-md-2 ms-auto">
                <select name="sort" class="form-select border-0 shadow-sm" onchange="this.form.submit()">
                    <option value="new" {% if request.args.get('sort') == 'new' %}selected{% endif %}>新着順</option>
                    <option value="old" {% if request.args.get('sort') == 'old' %}selected{% endif %}>古い順</option>
                </select>
            </div>
        </form>

        <div class="row row-cols-1 row-cols-sm-2 row-cols-lg-4 g-4">
            {% for event in events %}
            <div class="col">
                <div class="event-card shadow-sm border position-relative">
                    <img src="{{ event.image_url }}" class="w-100" style="height:200px; object-fit:cover;">
                    <div class="pickup-badge">PICK UP</div>
                    <div class="p-3">
                        <h6 class="fw-bold mb-2 text-truncate">{{ event.title }}</h6>
                        <div class="small text-muted mb-1"><i class="bi bi-calendar"></i> {{ event.date or '日付未設定' }}</div>
                        <div class="small text-muted mb-3"><i class="bi bi-geo-alt"></i> [{{ event.area or '未設定' }}] {{ event.location_detail }}</div>
                        <div class="d-flex justify-content-between align-items-center mt-auto">
                            <span class="badge rounded-pill bg-light text-primary border px-3 small">{{ event.category }}</span>
                            {% if current_user.is_authenticated and event.user_id == current_user.id %}
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

POST_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ja">
<head><meta charset="UTF-8"><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">''' + COMMON_STYLE + '''</head>
<body>
    <div class="container py-5" style="max-width:600px;">
        <div class="card p-5 shadow border-0" style="border-radius:20px;">
            <h2 class="fw-bold mb-4">イベントを投稿</h2>
            <form method="POST" enctype="multipart/form-data">
                <div class="mb-3"><label class="form-label small fw-bold">タイトル</label><input type="text" name="title" class="form-control" required></div>
                <div class="mb-3"><label class="form-label small fw-bold">カテゴリ</label>
                    <select name="category" class="form-select">
                        {% for cat in categories if cat.id != 'all' %}<option value="{{ cat.id }}">{{ cat.name }}</option>{% endfor %}
                    </select>
                </div>
                <div class="mb-3">
                    <label class="form-label small fw-bold">エリア</label>
                    <select name="area" class="form-select" required>
                        <option value="">選択してください</option>
                        <option value="関西">関西</option><option value="関東">関東</option>
                        <option value="オンライン">オンライン</option><option value="その他">その他</option>
                    </select>
                </div>
                <div class="mb-3"><label class="form-label small fw-bold">詳細な場所</label><input type="text" name="location_detail" class="form-control" placeholder="例: 大阪市北区 / Zoomなど"></div>
                <div class="mb-3"><label class="form-label small fw-bold">日付</label><input type="date" name="date" class="form-control"></div>
                <div class="mb-3"><label class="form-label small fw-bold">画像</label><input type="file" name="image" class="form-control"></div>
                <button type="submit" class="btn btn-pink w-100 py-3 mt-3">投稿する</button>
            </form>
            <a href="/" class="d-block text-center mt-3 text-muted small text-decoration-none">キャンセル</a>
        </div>
    </div>
</body>
</html>
'''

SIGNUP_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ja">
<head><meta charset="UTF-8"><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">''' + COMMON_STYLE + '''</head>
<body>
    <div class="container py-5" style="max-width:400px;">
        <div class="card p-4 shadow border-0" style="border-radius:20px;">
            <h2 class="fw-bold mb-4">Signup</h2>
            <form method="POST">
                <div class="mb-3"><input type="text" name="username" class="form-control" placeholder="ユーザー名" required></div>
                <div class="mb-3"><input type="password" name="password" class="form-control" placeholder="パスワード" required></div>
                <button type="submit" class="btn btn-pink w-100 py-2">登録して始める</button>
            </form>
            <div class="text-center mt-3"><a href="/login" class="text-muted small text-decoration-none">ログインはこちら</a></div>
        </div>
    </div>
</body>
</html>
'''

LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ja">
<head><meta charset="UTF-8"><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">''' + COMMON_STYLE + '''</head>
<body>
    <div class="container py-5" style="max-width:400px;">
        <div class="card p-4 shadow border-0" style="border-radius:20px;">
            <h2 class="fw-bold mb-4">Login</h2>
            <form method="POST">
                <div class="mb-3"><input type="text" name="username" class="form-control" placeholder="ユーザー名" required></div>
                <div class="mb-3"><input type="password" name="password" class="form-control" placeholder="パスワード" required></div>
                <button type="submit" class="btn btn-pink w-100 py-2">ログイン</button>
            </form>
            <div class="text-center mt-3"><a href="/signup" class="text-muted small text-decoration-none">新規登録はこちら</a></div>
        </div>
    </div>
</body>
</html>
'''

EDIT_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ja">
<head><meta charset="UTF-8"><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">''' + COMMON_STYLE + '''</head>
<body>
    <div class="container py-5" style="max-width:600px;">
        <div class="card p-5 shadow border-0" style="border-radius:20px;">
            <h2 class="fw-bold mb-4">編集する</h2>
            <form method="POST" enctype="multipart/form-data">
                <div class="mb-3"><label class="form-label small fw-bold">タイトル</label><input type="text" name="title" class="form-control" value="{{ event.title }}" required></div>
                <div class="mb-3">
                    <label class="form-label small fw-bold">エリア</label>
                    <select name="area" class="form-select">
                        {% for a in ['関西', '関東', 'オンライン', 'その他'] %}
                        <option value="{{ a }}" {% if event.area == a %}selected{% endif %}>{{ a }}</option>
                        {% endfor %}
                    </select>
                </div>
                <div class="mb-3"><label class="form-label small fw-bold">詳細な場所</label><input type="text" name="location_detail" class="form-control" value="{{ event.location_detail }}"></div>
                <div class="mb-3"><label class="form-label small fw-bold">画像を変更</label><input type="file" name="image" class="form-control"></div>
                <button type="submit" class="btn btn-pink w-100 py-3 mt-3 shadow-sm">更新する</button>
            </form>
            <form action="/delete/{{ event.id }}" method="POST" class="mt-3" onsubmit="return confirm('本当に削除しますか？')">
                <button type="submit" class="btn btn-link w-100 text-danger text-decoration-none small">この投稿を削除する</button>
            </form>
        </div>
    </div>
</body>
</html>
'''

# --- ルート設定 (データベース版) ---
@app.route('/')
def index():
    cat = request.args.get('category', 'all')
    area = request.args.get('area', '')
    query = request.args.get('q', '').lower()
    sort = request.args.get('sort', 'new')

    q = Event.query
    if cat != 'all': q = q.filter_by(category=cat)
    if area: q = q.filter_by(area=area)
    if query: q = q.filter(Event.title.ilike(f'%{query}%') | Event.location_detail.ilike(f'%{query}%'))
    
    events = q.all()
    if sort == 'new': events.reverse()
    
    return render_template_string(INDEX_TEMPLATE, events=events, categories=categories, active_cat=cat, current_user=current_user)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if User.query.filter_by(username=username).first(): return "ユーザー名が既に存在します", 400
        user = User(username=username, password=generate_password_hash(password))
        db.session.add(user); db.session.commit()
        login_user(user); return redirect(url_for('index'))
    return render_template_string(SIGNUP_TEMPLATE)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form.get('username')).first()
        if user and check_password_hash(user.password, request.form.get('password')):
            login_user(user); return redirect(url_for('index'))
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/logout')
def logout():
    logout_user(); return redirect(url_for('index'))

@app.route('/post', methods=['GET', 'POST'])
@login_required
def post():
    if request.method == 'POST':
        image_file = request.files.get('image')
        image_url = "https://via.placeholder.com/500"
        if image_file and image_file.filename != '':
            filename = secure_filename(image_file.filename)
            upload_dir = os.path.join(app.root_path, 'static', 'images', 'uploads')
            if not os.path.exists(upload_dir): os.makedirs(upload_dir)
            image_file.save(os.path.join(upload_dir, filename))
            image_url = '/static/images/uploads/' + filename
        
        event = Event(
            user_id=current_user.id, title=request.form.get('title'),
            category=request.form.get('category'), area=request.form.get('area'),
            location_detail=request.form.get('location_detail'),
            date=request.form.get('date'), image_url=image_url
        )
        db.session.add(event); db.session.commit()
        return redirect(url_for('index'))
    return render_template_string(POST_TEMPLATE, categories=categories)

@app.route('/edit/<int:event_id>', methods=['GET', 'POST'])
@login_required
def edit_event(event_id):
    event = Event.query.get_or_404(event_id)
    if event.user_id != current_user.id: return "権限なし", 403
    if request.method == 'POST':
        event.title = request.form.get('title')
        event.area = request.form.get('area')
        event.location_detail = request.form.get('location_detail')
        event.category = request.form.get('category')
        image_file = request.files.get('image')
        if image_file and image_file.filename != '':
            filename = secure_filename(image_file.filename)
            image_file.save(os.path.join(app.root_path, 'static', 'images', 'uploads', filename))
            event.image_url = '/static/images/uploads/' + filename
        db.session.commit(); return redirect(url_for('index'))
    return render_template_string(EDIT_TEMPLATE, event=event, categories=categories)

@app.route('/delete/<int:event_id>', methods=['POST'])
@login_required
def delete_event(event_id):
    event = Event.query.get_or_404(event_id)
    if event.user_id == current_user.id:
        db.session.delete(event); db.session.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))