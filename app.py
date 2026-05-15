import os
from flask import Flask, render_template_string, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'lgbtq-event-board-secret'

# --- DB設定 ---
database_url = os.environ.get('DATABASE_URL')
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///local_test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- モデル ---
class User(db.Model, UserMixin):
    id       = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email    = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Event(db.Model):
    id              = db.Column(db.Integer, primary_key=True)
    user_id         = db.Column(db.Integer, nullable=False)
    title           = db.Column(db.String(100), nullable=False)
    category        = db.Column(db.String(50))
    area            = db.Column(db.String(50))
    location_detail = db.Column(db.String(200))
    date            = db.Column(db.String(50))
    time            = db.Column(db.String(10))
    event_type      = db.Column(db.String(50))   # パレード / 交流会 / etc
    mode            = db.Column(db.String(20))    # オンライン / オフライン
    description     = db.Column(db.Text)
    emoji           = db.Column(db.String(10), default='🌈')
    image_url       = db.Column(db.String(500))
    is_pickup       = db.Column(db.Boolean, default=False)

class Favorite(db.Model):
    id       = db.Column(db.Integer, primary_key=True)
    user_id  = db.Column(db.Integer, nullable=False)
    event_id = db.Column(db.Integer, nullable=False)

with app.app_context():
    db.create_all()

# --- ログイン管理 ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- 定数 ---
CATEGORIES = [
    {'id': 'Lesbian',    'ja': 'レズビアン',       'color': '#db2777', 'bg': '#fdf2f8', 'border': '#f9a8d4', 'ibg': '#fce7f3', 'sub': '#f472b6',
     'svg': '<svg width="18" height="18" viewBox="0 0 24 24" fill="#f472b6" stroke="#ec4899" stroke-width="1.5"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg>'},
    {'id': 'Gay',        'ja': 'ゲイ',             'color': '#c2410c', 'bg': '#fff7ed', 'border': '#fed7aa', 'ibg': '#ffedd5', 'sub': '#fb923c',
     'svg': '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#ea580c" stroke-width="2"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>'},
    {'id': 'Bisexual',   'ja': 'バイセクシュアル',  'color': '#7e22ce', 'bg': '#faf5ff', 'border': '#d8b4fe', 'ibg': '#f3e8ff', 'sub': '#a855f7',
     'svg': '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#9333ea" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>'},
    {'id': 'Transgender','ja': 'トランスジェンダー', 'color': '#1d4ed8', 'bg': '#eff6ff', 'border': '#bfdbfe', 'ibg': '#dbeafe', 'sub': '#60a5fa',
     'svg': '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2"><path d="M12 2a10 10 0 1 0 0 20A10 10 0 0 0 12 2z"/><path d="M12 8v4l3 3"/></svg>'},
    {'id': 'Queer',      'ja': 'クィア',           'color': '#15803d', 'bg': '#f0fdf4', 'border': '#bbf7d0', 'ibg': '#dcfce7', 'sub': '#4ade80',
     'svg': '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#16a34a" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M8 14s1.5 2 4 2 4-2 4-2"/><line x1="9" y1="9" x2="9.01" y2="9"/><line x1="15" y1="9" x2="15.01" y2="9"/></svg>'},
    {'id': 'Ally',       'ja': 'アライ',           'color': '#a16207', 'bg': '#fefce8', 'border': '#fde68a', 'ibg': '#fef9c3', 'sub': '#facc15',
     'svg': '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#ca8a04" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>'},
    {'id': 'All / Mix',  'ja': '誰でもOK',         'color': '#a21caf', 'bg': '#fdf4ff', 'border': '#f0abfc', 'ibg': '#fae8ff', 'sub': '#e879f9',
     'svg': '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#c026d3" stroke-width="2"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>'},
]
EVENT_TYPES = ['パレード', '交流会', 'サポート', 'パーティー', '講演']
AREAS       = ['東京', '大阪', '名古屋', '福岡', 'オンライン', 'その他']

# --- 共通CSS ---
STYLE = '''
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Helvetica Neue',Arial,sans-serif;background:#f7f8fc;color:#333;min-height:100vh}
a{text-decoration:none;color:inherit}
header{background:#fff;border-bottom:1px solid #eee;padding:0 20px;height:60px;display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;z-index:100;box-shadow:0 1px 4px rgba(0,0,0,.04)}
.logo{display:flex;align-items:center;gap:10px;text-decoration:none}
.logo-icon{width:38px;height:38px;border-radius:10px;background:#fce7f3;border:0.5px solid #f9a8d4;display:flex;align-items:center;justify-content:center;font-size:1.2rem;flex-shrink:0}
.logo-text{font-size:1rem;font-weight:500;color:var(--color-text-primary,#333)}
.logo-bar{display:flex;gap:4px;margin-top:3px}
.logo-bar span{width:12px;height:3px;border-radius:2px;display:inline-block}
nav{display:flex;gap:16px;align-items:center}
nav a.nav-link{color:#555;font-size:.9rem;padding:4px 0;border-bottom:2px solid transparent;transition:.2s}
nav a.nav-link.active,nav a.nav-link:hover{color:#7c3aed;border-bottom-color:#7c3aed}
/* ハンバーガー */
.hamburger{display:none;flex-direction:column;gap:5px;cursor:pointer;background:none;border:none;padding:4px}
.hamburger span{display:block;width:24px;height:2px;background:#555;border-radius:2px;transition:.3s}
.mobile-menu{display:none;position:fixed;top:60px;left:0;right:0;background:#fff;border-bottom:1px solid #eee;padding:16px 20px;flex-direction:column;gap:12px;z-index:99;box-shadow:0 4px 12px rgba(0,0,0,.08)}
.mobile-menu.open{display:flex}
.mobile-menu a{color:#555;font-size:1rem;padding:8px 0;border-bottom:1px solid #f0f0f0}
.mobile-menu a:last-child{border-bottom:none}
.btn{padding:8px 18px;border-radius:20px;border:none;cursor:pointer;font-size:.85rem;font-weight:600;transition:.2s;display:inline-block}
.btn-primary{background:#7c3aed;color:#fff}.btn-primary:hover{background:#6d28d9}
.btn-outline{background:#fff;color:#7c3aed;border:2px solid #7c3aed}.btn-outline:hover{background:#f5f3ff}
.btn-sm{padding:5px 14px;font-size:.8rem}
.btn-danger{background:#ef4444;color:#fff}.btn-danger:hover{background:#dc2626}
.btn-warn{background:#f59e0b;color:#fff}.btn-warn:hover{background:#d97706}
main{max-width:1200px;margin:0 auto;padding:24px 16px}
h2{font-size:1.3rem;font-weight:700;margin-bottom:16px}
/* cats — 横スクロール */
.cats{display:flex;gap:10px;margin-bottom:16px;overflow-x:auto;padding-bottom:6px;-webkit-overflow-scrolling:touch;scrollbar-width:none}
.cats::-webkit-scrollbar{display:none}
.cat{display:flex;flex-direction:column;align-items:center;gap:5px;padding:12px 14px;border-radius:14px;border:1.5px solid #eee;background:#fff;cursor:pointer;min-width:76px;flex-shrink:0;transition:.2s;text-decoration:none;color:inherit}
.cat:hover,.cat.active{border-color:var(--border);background:var(--bg)}
.cat-icon-wrap{width:36px;height:36px;border-radius:50%;background:var(--ibg);display:flex;align-items:center;justify-content:center;transition:.2s}
.cat-en{font-size:.72rem;font-weight:600;color:var(--c)}
.cat-ja{font-size:.62rem;color:var(--sub)}
/* filters */
.filters{display:flex;gap:8px;margin-bottom:12px;flex-wrap:wrap;align-items:center}
.filter-select{padding:8px 12px;border:1px solid #ddd;border-radius:20px;background:#fff;font-size:.82rem;cursor:pointer;outline:none}
.filter-select:focus{border-color:#7c3aed}
.search-box{padding:8px 14px;border:1px solid #ddd;border-radius:20px;font-size:.85rem;width:100%;outline:none;box-sizing:border-box}
.search-box:focus{border-color:#7c3aed}
.search-wrap{width:100%}
/* cards */
.sort-row{display:flex;justify-content:flex-end;margin-bottom:12px}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:16px}
.card{background:#fff;border-radius:16px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,.06);transition:.2s;position:relative}
.card:hover{transform:translateY(-3px);box-shadow:0 6px 20px rgba(0,0,0,.1)}
.card-thumb{width:100%;height:160px;object-fit:cover;background:#eee;display:flex;align-items:center;justify-content:center;font-size:4rem}
.card-body{padding:14px}
.card-title{font-weight:700;font-size:.95rem;margin-bottom:6px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.card-meta{font-size:.78rem;color:#666;display:flex;flex-direction:column;gap:3px;margin-bottom:8px}
.tag{display:inline-block;padding:2px 10px;border-radius:10px;font-size:.72rem;font-weight:600;background:#f3e8ff;color:#7c3aed}
.pick{position:absolute;top:10px;left:10px;background:#ef4444;color:#fff;font-size:.7rem;font-weight:700;padding:2px 8px;border-radius:6px}
.fav-form{position:absolute;top:8px;right:8px}
.fav-btn{background:#ffffffcc;border:none;border-radius:50%;width:32px;height:32px;font-size:1rem;cursor:pointer;display:flex;align-items:center;justify-content:center}
.fav-btn:hover{background:#fff}
.owner-btns{display:flex;gap:6px;margin-top:8px}
/* fab */
.fab{position:fixed;bottom:24px;right:20px;width:52px;height:52px;background:#7c3aed;color:#fff;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:1.6rem;box-shadow:0 5px 15px rgba(124,58,237,.4);transition:.2s;z-index:50}
.fab:hover{background:#6d28d9;transform:scale(1.08)}
/* form pages */
.form-wrap{max-width:520px;margin:32px auto;background:#fff;border-radius:20px;padding:28px 20px;box-shadow:0 4px 20px rgba(0,0,0,.06)}
.form-wrap h2{margin-bottom:20px}
.field{margin-bottom:14px}
.field label{display:block;font-size:.85rem;font-weight:600;margin-bottom:4px;color:#555}
.field input,.field select,.field textarea{width:100%;padding:10px 14px;border:1px solid #ddd;border-radius:10px;font-size:.9rem;outline:none;transition:.2s;background:#fff}
.field input:focus,.field select:focus,.field textarea:focus{border-color:#7c3aed}
.field textarea{resize:vertical;min-height:80px}
.field-row{display:flex;gap:10px}.field-row .field{flex:1}
.form-link{text-align:center;margin-top:16px;font-size:.85rem;color:#888}
.form-link a{color:#7c3aed;font-weight:600}
.error{background:#fef2f2;border:1px solid #fecaca;color:#b91c1c;padding:10px 14px;border-radius:10px;font-size:.85rem;margin-bottom:12px}
/* user badge */
.avatar{width:30px;height:30px;border-radius:50%;background:linear-gradient(135deg,#7c3aed,#ec4899);color:#fff;font-weight:700;font-size:.8rem;display:flex;align-items:center;justify-content:center}
.user-badge{display:flex;align-items:center;gap:8px;font-size:.85rem}
.empty{text-align:center;padding:60px 20px;color:#aaa;grid-column:1/-1}
.empty .ei{font-size:3rem;margin-bottom:8px}
/* スマホ対応 */
@media(max-width:640px){
  nav .nav-link, nav .user-badge, nav .btn-outline{display:none}
  .hamburger{display:flex}
  .cards{grid-template-columns:repeat(2,1fr)}
  .field-row{flex-direction:column;gap:0}
  .filters{gap:6px}
  .filter-select{font-size:.78rem;padding:7px 10px}
}
</style>
'''

# --- テンプレート: INDEX ---
INDEX_TMPL = '''<!DOCTYPE html>
<html lang="ja">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>LGBTQ+ Event Board 🌈</title>''' + STYLE + '''</head>
<body>
<header>
  <a class="logo" href="/">
    <div class="logo-icon">🏳️‍🌈</div>
    <div>
      <div class="logo-text">LGBTQ+ Event Board</div>
      <div class="logo-bar">
        <span style="background:#f472b6"></span><span style="background:#fb923c"></span>
        <span style="background:#facc15"></span><span style="background:#4ade80"></span>
        <span style="background:#60a5fa"></span><span style="background:#a78bfa"></span>
      </div>
    </div>
  </a>
  <nav>
    <a href="/" class="nav-link active">イベントを探す</a>
    <a href="{{ url_for('post') }}" class="nav-link">イベントを投稿</a>
    {% if current_user.is_authenticated %}
      <a href="{{ url_for('favorites') }}" class="nav-link">お気に入り</a>
      <div class="user-badge">
        <div class="avatar">{{ current_user.username[0] }}</div>
        <span>{{ current_user.username }}</span>
        <a href="{{ url_for('logout') }}" class="btn btn-outline btn-sm">ログアウト</a>
      </div>
    {% else %}
      <a href="{{ url_for('login') }}" class="btn btn-outline btn-sm">ログイン</a>
      <a href="{{ url_for('signup') }}" class="btn btn-primary btn-sm">新規登録</a>
    {% endif %}
    <!-- ハンバーガー -->
    <button class="hamburger" onclick="toggleMenu()" aria-label="メニュー">
      <span></span><span></span><span></span>
    </button>
  </nav>
</header>
<!-- モバイルメニュー -->
<div class="mobile-menu" id="mobileMenu">
  <a href="/">🔍 イベントを探す</a>
  <a href="{{ url_for('post') }}">➕ イベントを投稿</a>
  {% if current_user.is_authenticated %}
    <a href="{{ url_for('favorites') }}">❤️ お気に入り</a>
    <a href="{{ url_for('logout') }}">👋 ログアウト ({{ current_user.username }})</a>
  {% else %}
    <a href="{{ url_for('login') }}">🔑 ログイン</a>
    <a href="{{ url_for('signup') }}">✨ 新規登録</a>
  {% endif %}
</div>
<script>
function toggleMenu(){
  document.getElementById('mobileMenu').classList.toggle('open');
}
document.addEventListener('click', function(e){
  const menu = document.getElementById('mobileMenu');
  const btn = document.querySelector('.hamburger');
  if(!menu.contains(e.target) && !btn.contains(e.target)){
    menu.classList.remove('open');
  }
});
</script>
<main>
  <h2>イベントを探す</h2>
  <!-- カテゴリ -->
  <div class="cats">
    <a href="/" class="cat {% if not active_cat %}active{% endif %}"
       style="--c:#7c3aed;--bg:#f5f3ff;--border:#c4b5fd;--ibg:#ede9fe;--sub:#a78bfa">
      <div class="cat-icon-wrap">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#7c3aed" stroke-width="2"><path d="M12 2l3 7h7l-5.5 4 2 7L12 16l-6.5 4 2-7L2 9h7z"/></svg>
      </div>
      <span class="cat-en">All</span>
      <span class="cat-ja">すべて</span>
    </a>
    {% for c in categories %}
    <a href="/?cat={{ c.id }}&area={{ area }}&mode={{ mode }}&type={{ etype }}&q={{ q }}&sort={{ sort }}"
       class="cat {% if active_cat == c.id %}active{% endif %}"
       style="--c:{{ c.color }};--bg:{{ c.bg }};--border:{{ c.border }};--ibg:{{ c.ibg }};--sub:{{ c.sub }}">
      <div class="cat-icon-wrap">{{ c.svg | safe }}</div>
      <span class="cat-en">{{ c.id }}</span>
      <span class="cat-ja">{{ c.ja }}</span>
    </a>
    {% endfor %}
  </div>
  <!-- フィルター -->
  <form method="GET" action="/" class="filters">
    <input type="hidden" name="cat" value="{{ active_cat }}">
    <select name="area" class="filter-select" onchange="this.form.submit()">
      <option value="">エリア 全て</option>
      {% for a in areas %}<option value="{{ a }}" {% if area==a %}selected{% endif %}>{{ a }}</option>{% endfor %}
    </select>
    <select name="type" class="filter-select" onchange="this.form.submit()">
      <option value="">イベント種類 全て</option>
      {% for t in event_types %}<option value="{{ t }}" {% if etype==t %}selected{% endif %}>{{ t }}</option>{% endfor %}
    </select>
    <select name="mode" class="filter-select" onchange="this.form.submit()">
      <option value="">オンライン/オフライン</option>
      <option value="オンライン" {% if mode=='オンライン' %}selected{% endif %}>オンライン</option>
      <option value="オフライン" {% if mode=='オフライン' %}selected{% endif %}>オフライン</option>
    </select>
    <div class="search-wrap"><input name="q" class="search-box" placeholder="キーワードで検索" value="{{ q }}"></div>
    <div class="sort-row" style="margin-left:auto;margin-bottom:0">
      <select name="sort" class="filter-select" onchange="this.form.submit()">
        <option value="new" {% if sort=='new' %}selected{% endif %}>新着順</option>
        <option value="date" {% if sort=='date' %}selected{% endif %}>日付順</option>
      </select>
    </div>
  </form>
  <!-- カード -->
  <div class="cards">
    {% if events %}
      {% for e in events %}
      <div class="card">
        {% if e.image_url and not e.image_url.startswith('emoji:') %}
          <img class="card-thumb" src="{{ e.image_url }}" alt="{{ e.title }}">
        {% else %}
          <div class="card-thumb">{{ e.emoji or '🌈' }}</div>
        {% endif %}
        {% if e.is_pickup %}<div class="pick">PICK UP</div>{% endif %}
        <!-- お気に入りボタン -->
        {% if current_user.is_authenticated %}
        <form class="fav-form" method="POST" action="{{ url_for('toggle_fav', event_id=e.id) }}">
          <button class="fav-btn" title="お気に入り">{{ '❤️' if e.id in fav_ids else '🤍' }}</button>
        </form>
        {% endif %}
        <div class="card-body">
          <div class="card-title">{{ e.title }}</div>
          <div class="card-meta">
            <span>📅 {{ e.date or '日付未定' }}{% if e.time %} {{ e.time }}〜{% endif %}</span>
            <span>📍 {{ e.area or '未定' }}{% if e.location_detail %} · {{ e.location_detail }}{% endif %} · {{ e.mode or '' }}</span>
          </div>
          <span class="tag">{{ e.event_type or e.category }}</span>
          {% if current_user.is_authenticated and e.user_id == current_user.id %}
          <div class="owner-btns">
            <a href="{{ url_for('edit_event', event_id=e.id) }}" class="btn btn-warn btn-sm">✏️ 編集</a>
            <form method="POST" action="{{ url_for('delete_event', event_id=e.id) }}" style="display:inline" onsubmit="return confirm('削除しますか？')">
              <button class="btn btn-danger btn-sm">🗑 削除</button>
            </form>
          </div>
          {% endif %}
        </div>
      </div>
      {% endfor %}
    {% else %}
      <div class="empty"><div class="ei">🌈</div><p>イベントが見つかりませんでした</p></div>
    {% endif %}
  </div>
</main>
<a href="{{ url_for('post') }}" class="fab">＋</a>
</body></html>'''

# --- テンプレート: POST/EDIT ---
def post_edit_tmpl(title, action, event=None):
    v = lambda f, d='': getattr(event, f, d) or d if event else d
    cats_opts = ''.join(
        f'<option value="{c["id"]}" {"selected" if v("category")==c["id"] else ""}>{c["id"]} {c["icon"]}</option>'
        for c in CATEGORIES
    )
    area_opts = ''.join(
        f'<option value="{a}" {"selected" if v("area")==a else ""}>{a}</option>'
        for a in AREAS
    )
    type_opts = ''.join(
        f'<option value="{t}" {"selected" if v("event_type")==t else ""}>{t}</option>'
        for t in EVENT_TYPES
    )
    delete_btn = f'''
    <form method="POST" action="/delete/{event.id}" style="margin-top:12px" onsubmit="return confirm('削除しますか？')">
      <button class="btn btn-danger" style="width:100%">🗑 この投稿を削除する</button>
    </form>''' if event else ''

    return f'''<!DOCTYPE html>
<html lang="ja"><head><meta charset="UTF-8"><title>{title}</title>{STYLE}</head>
<body>
<header>
  <a class="logo" href="/">LGBTQ+ Event Board 🌈</a>
  <nav><a href="/">← トップに戻る</a></nav>
</header>
<div class="form-wrap">
  <h2>{title}</h2>
  {{% if error %}}<div class="error">{{{{ error }}}}</div>{{% endif %}}
  <form method="POST" enctype="multipart/form-data" action="{action}">
    <div class="field"><label>イベント名 *</label>
      <input type="text" name="title" value="{v('title')}" required placeholder="例: Tokyo Pride Parade 2025">
    </div>
    <div class="field-row">
      <div class="field"><label>カテゴリ *</label>
        <select name="category" required><option value="">選択</option>{cats_opts}</select>
      </div>
      <div class="field"><label>イベント種類</label>
        <select name="event_type"><option value="">選択</option>{type_opts}</select>
      </div>
    </div>
    <div class="field-row">
      <div class="field"><label>日付</label>
        <input type="date" name="date" value="{v('date')}">
      </div>
      <div class="field"><label>時間</label>
        <input type="time" name="time" value="{v('time')}">
      </div>
    </div>
    <div class="field-row">
      <div class="field"><label>エリア</label>
        <select name="area"><option value="">選択</option>{area_opts}</select>
      </div>
      <div class="field"><label>形式</label>
        <select name="mode">
          <option value="オフライン" {"selected" if v("mode")=="オフライン" else ""}>オフライン</option>
          <option value="オンライン" {"selected" if v("mode")=="オンライン" else ""}>オンライン</option>
        </select>
      </div>
    </div>
    <div class="field"><label>詳細な場所</label>
      <input type="text" name="location_detail" value="{v('location_detail')}" placeholder="例: 渋谷区 / Zoom">
    </div>
    <div class="field"><label>説明</label>
      <textarea name="description">{v('description')}</textarea>
    </div>
    <div class="field-row">
      <div class="field"><label>絵文字アイコン</label>
        <input type="text" name="emoji" value="{v('emoji','🌈')}" maxlength="4" placeholder="🌈">
      </div>
      <div class="field"><label>画像ファイル</label>
        <input type="file" name="image" accept="image/*">
      </div>
    </div>
    <button type="submit" class="btn btn-primary" style="width:100%;padding:14px;font-size:1rem;border-radius:12px;margin-top:8px">
      {"更新する" if event else "投稿する"}
    </button>
  </form>
  {delete_btn}
</div>
</body></html>'''

# --- テンプレート: AUTH ---
AUTH_TMPL = '''<!DOCTYPE html>
<html lang="ja"><head><meta charset="UTF-8"><title>{{ page_title }}</title>''' + STYLE + '''</head>
<body>
<header>
  <a class="logo" href="/">LGBTQ+ Event Board 🌈</a>
</header>
<div class="form-wrap">
  <h2>{{ page_title }}</h2>
  {% if error %}<div class="error">{{ error }}</div>{% endif %}
  <form method="POST">
    {% if is_signup %}
    <div class="field"><label>ユーザー名</label>
      <input type="text" name="username" required placeholder="ニックネーム">
    </div>
    {% endif %}
    <div class="field"><label>メールアドレス</label>
      <input type="email" name="email" required placeholder="example@email.com">
    </div>
    <div class="field"><label>パスワード{% if is_signup %}（8文字以上）{% endif %}</label>
      <input type="password" name="password" required placeholder="パスワード">
    </div>
    <button type="submit" class="btn btn-primary" style="width:100%;padding:14px;font-size:1rem;border-radius:12px;margin-top:8px">
      {{ '登録して始める' if is_signup else 'ログイン' }}
    </button>
  </form>
  <div class="form-link">
    {% if is_signup %}
      アカウントをお持ちの方は <a href="{{ url_for('login') }}">ログイン</a>
    {% else %}
      アカウントをお持ちでない方は <a href="{{ url_for('signup') }}">新規登録</a>
    {% endif %}
  </div>
</div>
</body></html>'''

# --- テンプレート: FAVORITES ---
FAVS_TMPL = '''<!DOCTYPE html>
<html lang="ja"><head><meta charset="UTF-8"><title>お気に入り</title>''' + STYLE + '''</head>
<body>
<header>
  <a class="logo" href="/">LGBTQ+ Event Board 🌈</a>
  <nav>
    <a href="/">イベントを探す</a>
    <a href="{{ url_for('favorites') }}" class="active">お気に入り</a>
    <a href="{{ url_for('logout') }}" class="btn btn-outline btn-sm">ログアウト</a>
  </nav>
</header>
<main>
  <h2>❤️ お気に入り</h2>
  <div class="cards">
    {% if events %}
      {% for e in events %}
      <div class="card">
        {% if e.image_url %}<img class="card-thumb" src="{{ e.image_url }}">
        {% else %}<div class="card-thumb">{{ e.emoji or '🌈' }}</div>{% endif %}
        <form class="fav-form" method="POST" action="{{ url_for('toggle_fav', event_id=e.id) }}">
          <button class="fav-btn">❤️</button>
        </form>
        <div class="card-body">
          <div class="card-title">{{ e.title }}</div>
          <div class="card-meta">
            <span>📅 {{ e.date or '日付未定' }}{% if e.time %} {{ e.time }}〜{% endif %}</span>
            <span>📍 {{ e.area or '未定' }} · {{ e.mode or '' }}</span>
          </div>
          <span class="tag">{{ e.event_type or e.category }}</span>
        </div>
      </div>
      {% endfor %}
    {% else %}
      <div class="empty"><div class="ei">💝</div><p>お気に入りはまだありません</p></div>
    {% endif %}
  </div>
</main>
</body></html>'''

# ===== ROUTES =====

@app.route('/')
def index():
    cat   = request.args.get('cat', '')
    area  = request.args.get('area', '')
    mode  = request.args.get('mode', '')
    etype = request.args.get('type', '')
    q     = request.args.get('q', '')
    sort  = request.args.get('sort', 'new')

    query = Event.query
    if cat:   query = query.filter_by(category=cat)
    if area:  query = query.filter_by(area=area)
    if mode:  query = query.filter_by(mode=mode)
    if etype: query = query.filter_by(event_type=etype)
    if q:     query = query.filter(
        Event.title.ilike(f'%{q}%') | Event.description.ilike(f'%{q}%')
    )

    events = query.all()
    if sort == 'new':  events = list(reversed(events))
    elif sort == 'date': events.sort(key=lambda e: e.date or '')

    fav_ids = set()
    if current_user.is_authenticated:
        fav_ids = {f.event_id for f in Favorite.query.filter_by(user_id=current_user.id).all()}

    return render_template_string(
        INDEX_TMPL,
        events=events, categories=CATEGORIES, areas=AREAS, event_types=EVENT_TYPES,
        active_cat=cat, area=area, mode=mode, etype=etype, q=q, sort=sort,
        fav_ids=fav_ids, current_user=current_user
    )

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email    = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        if not username or not email or not password:
            error = '全て入力してください'
        elif len(password) < 8:
            error = 'パスワードは8文字以上にしてください'
        elif User.query.filter_by(email=email).first():
            error = 'このメールアドレスは既に登録されています'
        elif User.query.filter_by(username=username).first():
            error = 'このユーザー名は既に使われています'
        else:
            user = User(username=username, email=email,
                        password=generate_password_hash(password))
            db.session.add(user)
            db.session.commit()
            login_user(user)
            return redirect(url_for('index'))
    return render_template_string(AUTH_TMPL, page_title='新規登録', is_signup=True, error=error)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        email    = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        error = 'メールアドレスまたはパスワードが間違っています'
    return render_template_string(AUTH_TMPL, page_title='ログイン', is_signup=False, error=error)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/post', methods=['GET', 'POST'])
@login_required
def post():
    error = None
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        cat   = request.form.get('category', '')
        if not title or not cat:
            error = 'イベント名とカテゴリは必須です'
        else:
            image_url = None
            image_file = request.files.get('image')
            if image_file and image_file.filename:
                filename  = secure_filename(image_file.filename)
                upload_dir = os.path.join(app.root_path, 'static', 'images', 'uploads')
                os.makedirs(upload_dir, exist_ok=True)
                image_file.save(os.path.join(upload_dir, filename))
                image_url = '/static/images/uploads/' + filename

            event = Event(
                user_id         = current_user.id,
                title           = title,
                category        = cat,
                area            = request.form.get('area'),
                location_detail = request.form.get('location_detail'),
                date            = request.form.get('date'),
                time            = request.form.get('time'),
                event_type      = request.form.get('event_type'),
                mode            = request.form.get('mode', 'オフライン'),
                description     = request.form.get('description'),
                emoji           = request.form.get('emoji') or '🌈',
                image_url       = image_url,
            )
            db.session.add(event)
            db.session.commit()
            return redirect(url_for('index'))

    tmpl = post_edit_tmpl('イベントを投稿', url_for('post'))
    return render_template_string(tmpl, error=error)

@app.route('/edit/<int:event_id>', methods=['GET', 'POST'])
@login_required
def edit_event(event_id):
    event = Event.query.get_or_404(event_id)
    if event.user_id != current_user.id:
        return '権限がありません', 403

    error = None
    if request.method == 'POST':
        event.title           = request.form.get('title', event.title).strip()
        event.category        = request.form.get('category', event.category)
        event.area            = request.form.get('area', event.area)
        event.location_detail = request.form.get('location_detail', event.location_detail)
        event.date            = request.form.get('date', event.date)
        event.time            = request.form.get('time', event.time)
        event.event_type      = request.form.get('event_type', event.event_type)
        event.mode            = request.form.get('mode', event.mode)
        event.description     = request.form.get('description', event.description)
        event.emoji           = request.form.get('emoji') or event.emoji

        image_file = request.files.get('image')
        if image_file and image_file.filename:
            filename = secure_filename(image_file.filename)
            upload_dir = os.path.join(app.root_path, 'static', 'images', 'uploads')
            os.makedirs(upload_dir, exist_ok=True)
            image_file.save(os.path.join(upload_dir, filename))
            event.image_url = '/static/images/uploads/' + filename

        db.session.commit()
        return redirect(url_for('index'))

    tmpl = post_edit_tmpl('イベントを編集', url_for('edit_event', event_id=event_id), event)
    return render_template_string(tmpl, error=error)

@app.route('/delete/<int:event_id>', methods=['POST'])
@login_required
def delete_event(event_id):
    event = Event.query.get_or_404(event_id)
    if event.user_id == current_user.id:
        Favorite.query.filter_by(event_id=event_id).delete()
        db.session.delete(event)
        db.session.commit()
    return redirect(url_for('index'))

@app.route('/fav/<int:event_id>', methods=['POST'])
@login_required
def toggle_fav(event_id):
    fav = Favorite.query.filter_by(user_id=current_user.id, event_id=event_id).first()
    if fav:
        db.session.delete(fav)
    else:
        db.session.add(Favorite(user_id=current_user.id, event_id=event_id))
    db.session.commit()
    return redirect(request.referrer or url_for('index'))

@app.route('/favorites')
@login_required
def favorites():
    fav_ids = {f.event_id for f in Favorite.query.filter_by(user_id=current_user.id).all()}
    events  = Event.query.filter(Event.id.in_(fav_ids)).all()
    return render_template_string(FAVS_TMPL, events=events, current_user=current_user)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)