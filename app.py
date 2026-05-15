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
    is_admin = db.Column(db.Boolean, default=False)

class Event(db.Model):
    id              = db.Column(db.Integer, primary_key=True)
    user_id         = db.Column(db.Integer, nullable=False)
    title           = db.Column(db.String(100), nullable=False)
    category        = db.Column(db.String(50))
    area            = db.Column(db.String(50))
    location_detail = db.Column(db.String(200))
    date            = db.Column(db.String(50))
    time            = db.Column(db.String(10))
    event_type      = db.Column(db.String(50))
    mode            = db.Column(db.String(20))
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
    {'id': 'Lesbian',    'ja': 'レズビアン',       'color': '#e84393', 'bg': '#fce7f3',
     'svg': '<svg viewBox="0 0 28 28" fill="none"><path d="M14 7C14 7 7 11.5 7 16.5C7 20.09 10.13 23 14 23C17.87 23 21 20.09 21 16.5C21 11.5 14 7 14 7Z" fill="#f472b6"/><path d="M14 23V26M11 24.5H17" stroke="#e84393" stroke-width="2" stroke-linecap="round"/></svg>'},
    {'id': 'Gay',        'ja': 'ゲイ',             'color': '#f97316', 'bg': '#fff7ed',
     'svg': '<svg viewBox="0 0 28 28" fill="none"><circle cx="12" cy="14" r="7" stroke="#f97316" stroke-width="2"/><path d="M17 9L24 2M24 2H19M24 2V7" stroke="#f97316" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>'},
    {'id': 'Bisexual',   'ja': 'バイセクシュアル',  'color': '#a855f7', 'bg': '#faf5ff',
     'svg': '<svg viewBox="0 0 28 28" fill="none"><circle cx="11" cy="14" r="7" fill="#ec4899" fill-opacity=".55"/><circle cx="17" cy="14" r="7" fill="#7c3aed" fill-opacity=".55"/></svg>'},
    {'id': 'Transgender','ja': 'トランスジェンダー','color': '#3b82f6', 'bg': '#eff6ff',
     'svg': '<svg viewBox="0 0 28 28" fill="none"><circle cx="14" cy="14" r="6" stroke="#3b82f6" stroke-width="2"/><path d="M14 8V5M11 5H17" stroke="#60a5fa" stroke-width="2" stroke-linecap="round"/><path d="M14 20V23M11 23H17" stroke="#f9a8d4" stroke-width="2" stroke-linecap="round"/><path d="M20 8L22 6M22 6H20M22 6V8" stroke="#60a5fa" stroke-width="1.5" stroke-linecap="round"/><path d="M8 8L6 6M6 6H8M6 6V8" stroke="#f9a8d4" stroke-width="1.5" stroke-linecap="round"/></svg>'},
    {'id': 'Queer',      'ja': 'クィア',           'color': '#22c55e', 'bg': '#f0fdf4',
     'svg': '<svg viewBox="0 0 28 28" fill="none"><path d="M14 4C14 4 8 9 8 15C8 18.31 10.69 21 14 21C17.31 21 20 18.31 20 15C20 9 14 4 14 4Z" fill="#86efac" stroke="#22c55e" stroke-width="1.5"/><path d="M14 21V25" stroke="#22c55e" stroke-width="2" stroke-linecap="round"/><path d="M11 13C11 13 12.5 15 14 15C15.5 15 17 13 17 13" stroke="#fff" stroke-width="1.5" stroke-linecap="round"/></svg>'},
    {'id': 'Ally',       'ja': 'アライ',           'color': '#eab308', 'bg': '#fefce8',
     'svg': '<svg viewBox="0 0 28 28" fill="none"><path d="M14 3L16.8 9.8L24 10.4L18.7 15.1L20.4 22L14 18.3L7.6 22L9.3 15.1L4 10.4L11.2 9.8L14 3Z" fill="#fde68a" stroke="#f59e0b" stroke-width="1.5" stroke-linejoin="round"/></svg>'},
    {'id': 'All / Mix',  'ja': '誰でもOK',         'color': '#7c3aed', 'bg': '#f5f3ff',
     'svg': '<svg viewBox="0 0 28 28" fill="none"><path d="M14 4C8.48 4 4 8.48 4 14C4 19.52 8.48 24 14 24C19.52 24 24 19.52 24 14C24 8.48 19.52 4 14 4Z" stroke="#7c3aed" stroke-width="1.5"/><path d="M4 14H24" stroke="#7c3aed" stroke-width="1.5" stroke-dasharray="2 2"/><path d="M14 4C14 4 10 9 10 14C10 19 14 24 14 24" stroke="#ec4899" stroke-width="1.5"/><path d="M14 4C14 4 18 9 18 14C18 19 14 24 14 24" stroke="#60a5fa" stroke-width="1.5"/></svg>'},
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
.logo-icon{width:40px;height:40px;background:linear-gradient(135deg,#fda4af,#c084fc,#7dd3fc);border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:1.3rem;box-shadow:0 3px 10px rgba(192,132,252,.35);flex-shrink:0}
.logo-text{display:flex;flex-direction:column;line-height:1.2}
.logo-main{font-size:1rem;font-weight:800;background:linear-gradient(90deg,#f472b6,#a78bfa,#60a5fa);-webkit-background-clip:text;-webkit-text-fill-color:transparent;white-space:nowrap}
.logo-sub{font-size:.6rem;color:#c4b5d5;font-weight:500;letter-spacing:.08em}
nav{display:flex;gap:16px;align-items:center}
nav a.nav-link{color:#555;font-size:.9rem;padding:4px 0;border-bottom:2px solid transparent;transition:.2s}
nav a.nav-link.active,nav a.nav-link:hover{color:#7c3aed;border-bottom-color:#7c3aed}
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
.cats{display:flex;gap:10px;margin-bottom:16px;overflow-x:auto;padding-bottom:6px;-webkit-overflow-scrolling:touch;scrollbar-width:none}
.cats::-webkit-scrollbar{display:none}
.cat{display:flex;flex-direction:column;align-items:center;gap:6px;padding:14px 16px;border-radius:16px;border:2px solid #eee;background:#fff;cursor:pointer;min-width:88px;flex-shrink:0;transition:.2s;text-decoration:none;color:inherit}
.cat:hover,.cat.active{border-color:var(--c);background:var(--bg)}
.cat-icon-wrap{width:48px;height:48px;border-radius:14px;display:flex;align-items:center;justify-content:center;margin-bottom:2px}
.cat-en{font-size:.78rem;font-weight:700;color:var(--c)}
.cat-ja{font-size:.68rem;color:#888}
.filters{display:flex;gap:8px;margin-bottom:12px;flex-wrap:wrap;align-items:center}
.filter-select{padding:8px 12px;border:1px solid #ddd;border-radius:20px;background:#fff;font-size:.82rem;cursor:pointer;outline:none}
.filter-select:focus{border-color:#7c3aed}
.search-box{padding:8px 14px;border:1px solid #ddd;border-radius:20px;font-size:.85rem;width:100%;outline:none;box-sizing:border-box}
.search-box:focus{border-color:#7c3aed}
.search-wrap{width:100%}
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
.fab{position:fixed;bottom:24px;right:20px;width:52px;height:52px;background:#7c3aed;color:#fff;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:1.6rem;box-shadow:0 5px 15px rgba(124,58,237,.4);transition:.2s;z-index:50}
.fab:hover{background:#6d28d9;transform:scale(1.08)}
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
.avatar{width:30px;height:30px;border-radius:50%;background:linear-gradient(135deg,#7c3aed,#ec4899);color:#fff;font-weight:700;font-size:.8rem;display:flex;align-items:center;justify-content:center}
.user-badge{display:flex;align-items:center;gap:8px;font-size:.85rem}
.empty{text-align:center;padding:60px 20px;color:#aaa;grid-column:1/-1}
.empty .ei{font-size:3rem;margin-bottom:8px}
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
    <div class="logo-icon">🌈</div>
    <div class="logo-text">
      <span class="logo-main">LGBTQ+ Event Board</span>
      <span class="logo-sub">COMMUNITY EVENTS</span>
    </div>
  </a>
  <nav>
    <a href="/" class="nav-link active">イベントを探す</a>
    <a href="{{ url_for('post') }}" class="nav-link">イベントを投稿</a>
    {% if current_user.is_authenticated %}
      <a href="{{ url_for('favorites') }}" class="nav-link">お気に入り</a>
      {% if current_user.is_admin %}
        <a href="{{ url_for('admin') }}" class="nav-link" style="color:#ef4444">🔧 管理</a>
      {% endif %}
      <div class="user-badge">
        <div class="avatar">{{ current_user.username[0] }}</div>
        <span>{{ current_user.username }}</span>
        <a href="{{ url_for('logout') }}" class="btn btn-outline btn-sm">ログアウト</a>
      </div>
    {% else %}
      <a href="{{ url_for('login') }}" class="btn btn-outline btn-sm">ログイン</a>
      <a href="{{ url_for('signup') }}" class="btn btn-primary btn-sm">新規登録</a>
    {% endif %}
    <button class="hamburger" onclick="toggleMenu()" aria-label="メニュー">
      <span></span><span></span><span></span>
    </button>
  </nav>
</header>
<div class="mobile-menu" id="mobileMenu">
  <a href="/">🔍 イベントを探す</a>
  <a href="{{ url_for('post') }}">➕ イベントを投稿</a>
  {% if current_user.is_authenticated %}
    <a href="{{ url_for('favorites') }}">❤️ お気に入り</a>
    {% if current_user.is_admin %}<a href="{{ url_for('admin') }}">🔧 管理者ページ</a>{% endif %}
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
  <div class="cats">
    <a href="/" class="cat {% if not active_cat %}active{% endif %}" style="--c:#7c3aed;--bg:#f5f3ff">
      <div class="cat-icon-wrap" style="background:#f5f3ff">
        <svg viewBox="0 0 28 28" width="28" height="28" fill="none">
          <path d="M14 3L16.8 9.8L24 10.4L18.7 15.1L20.4 22L14 18.3L7.6 22L9.3 15.1L4 10.4L11.2 9.8L14 3Z" fill="#ddd6fe" stroke="#7c3aed" stroke-width="1.5" stroke-linejoin="round"/>
        </svg>
      </div>
      <span class="cat-en" style="color:#7c3aed">All</span>
      <span class="cat-ja">すべて</span>
    </a>
    {% for c in categories %}
    <a href="/?cat={{ c.id }}&area={{ area }}&mode={{ mode }}&type={{ etype }}&q={{ q }}&sort={{ sort }}"
       class="cat {% if active_cat == c.id %}active{% endif %}" style="--c:{{ c.color }};--bg:{{ c.bg }}">
      <div class="cat-icon-wrap" style="background:{{ c.bg }}">
        {{ c.svg | safe }}
      </div>
      <span class="cat-en" style="color:{{ c.color }}">{{ c.id }}</span>
      <span class="cat-ja">{{ c.ja }}</span>
    </a>
    {% endfor %}
  </div>
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
    <a href="/" class="nav-link">イベントを探す</a>
    <a href="{{ url_for('favorites') }}" class="nav-link active">お気に入り</a>
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

# --- テンプレート: ADMIN ---
ADMIN_TMPL = '''<!DOCTYPE html>
<html lang="ja"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>管理者ページ</title>''' + STYLE + '''</head>
<body>
<header>
  <a class="logo" href="/">LGBTQ+ Event Board 🌈</a>
  <nav>
    <a href="/" class="nav-link">トップ</a>
    <a href="{{ url_for('logout') }}" class="btn btn-outline btn-sm">ログアウト</a>
  </nav>
</header>
<main style="max-width:640px">
  <h2>🔧 管理者ページ</h2>
  <p style="color:#888;font-size:.85rem;margin-bottom:24px">URLを貼り付けるとイベント情報を自動で読み取ります</p>

  <div class="form-wrap" style="margin:0 0 24px">
    <div class="field">
      <label>イベントページのURLを貼り付け</label>
      <input type="text" id="urlInput" placeholder="https://peatix.com/event/... など">
    </div>
    <button class="btn btn-primary" style="width:100%;padding:12px" onclick="fetchUrl()">
      🔍 情報を読み取る
    </button>
    <div id="loadingMsg" style="display:none;text-align:center;margin-top:12px;color:#888;font-size:.85rem">読み取り中...</div>
    <div id="errorMsg" class="error" style="display:none;margin-top:12px"></div>
  </div>

  <div id="resultForm" style="display:none">
    <div class="form-wrap" style="margin:0">
      <h3 style="font-size:1rem;font-weight:700;margin-bottom:16px">✅ 読み取り結果（修正してから投稿できます）</h3>
      <form method="POST" action="{{ url_for('admin_post') }}">
        <input type="hidden" name="source_url" id="sourceUrl">
        <div class="field"><label>イベント名 *</label>
          <input type="text" name="title" id="rTitle" required>
        </div>
        <div class="field-row">
          <div class="field"><label>カテゴリ</label>
            <select name="category">
              <option value="All / Mix">All / Mix 🌈</option>
              <option value="Lesbian">Lesbian 🩷</option>
              <option value="Gay">Gay 🧡</option>
              <option value="Bisexual">Bisexual 💜</option>
              <option value="Transgender">Transgender ⚡</option>
              <option value="Queer">Queer 🌿</option>
              <option value="Ally">Ally ⭐</option>
            </select>
          </div>
          <div class="field"><label>イベント種類</label>
            <select name="event_type">
              <option value="">選択</option>
              <option>パレード</option><option>交流会</option>
              <option>サポート</option><option>パーティー</option><option>講演</option>
            </select>
          </div>
        </div>
        <div class="field-row">
          <div class="field"><label>日付</label>
            <input type="date" name="date" id="rDate">
          </div>
          <div class="field"><label>時間</label>
            <input type="time" name="time" id="rTime">
          </div>
        </div>
        <div class="field-row">
          <div class="field"><label>エリア</label>
            <select name="area" id="rArea">
              <option value="">選択</option>
              <option>東京</option><option>大阪</option><option>名古屋</option>
              <option>福岡</option><option>オンライン</option><option>その他</option>
            </select>
          </div>
          <div class="field"><label>形式</label>
            <select name="mode" id="rMode">
              <option>オフライン</option><option>オンライン</option>
            </select>
          </div>
        </div>
        <div class="field"><label>詳細な場所</label>
          <input type="text" name="location_detail" id="rPlace">
        </div>
        <div class="field"><label>説明</label>
          <textarea name="description" id="rDesc"></textarea>
        </div>
        <div class="field"><label>絵文字</label>
          <input type="text" name="emoji" value="🌈" maxlength="4">
        </div>
        <button type="submit" class="btn btn-primary" style="width:100%;padding:14px;border-radius:12px;margin-top:8px">
          🚀 投稿する
        </button>
      </form>
    </div>
  </div>

  <div style="margin-top:32px">
    <h3 style="font-size:1rem;font-weight:700;margin-bottom:12px">📋 最近の投稿（20件）</h3>
    {% for e in recent_events %}
    <div style="background:#fff;border-radius:12px;padding:12px 16px;margin-bottom:8px;box-shadow:0 1px 4px rgba(0,0,0,.06);display:flex;justify-content:space-between;align-items:center">
      <div>
        <div style="font-weight:600;font-size:.9rem">{{ e.title[:35] }}</div>
        <div style="font-size:.75rem;color:#aaa">{{ e.date or '日付未定' }} · {{ e.area or '未定' }}</div>
      </div>
      <form method="POST" action="{{ url_for('delete_event', event_id=e.id) }}" onsubmit="return confirm('削除しますか？')">
        <button class="btn btn-danger btn-sm">🗑</button>
      </form>
    </div>
    {% endfor %}
  </div>
</main>

<script>
async function fetchUrl() {
  const url = document.getElementById('urlInput').value.trim();
  if (!url) return;
  document.getElementById('loadingMsg').style.display = 'block';
  document.getElementById('errorMsg').style.display = 'none';
  document.getElementById('resultForm').style.display = 'none';
  try {
    const res = await fetch('/admin/fetch', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({url: url})
    });
    const data = await res.json();
    if (data.error) {
      document.getElementById('errorMsg').textContent = data.error;
      document.getElementById('errorMsg').style.display = 'block';
    } else {
      document.getElementById('rTitle').value    = data.title || '';
      document.getElementById('rDate').value     = data.date || '';
      document.getElementById('rTime').value     = data.time || '';
      document.getElementById('rPlace').value    = data.place || '';
      document.getElementById('rDesc').value     = data.desc || '';
      document.getElementById('sourceUrl').value = url;
      const areaSelect = document.getElementById('rArea');
      for (let opt of areaSelect.options) {
        if (data.area && opt.value === data.area) { opt.selected = true; break; }
      }
      if (data.area === 'オンライン') document.getElementById('rMode').value = 'オンライン';
      document.getElementById('resultForm').style.display = 'block';
    }
  } catch(e) {
    document.getElementById('errorMsg').textContent = '読み取りに失敗しました';
    document.getElementById('errorMsg').style.display = 'block';
  }
  document.getElementById('loadingMsg').style.display = 'none';
}
</script>
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
    if sort == 'new':   events = list(reversed(events))
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
    if event.user_id == current_user.id or (current_user.is_authenticated and current_user.is_admin):
        Favorite.query.filter_by(event_id=event_id).delete()
        db.session.delete(event)
        db.session.commit()
    return redirect(request.referrer or url_for('index'))

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

@app.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        return redirect(url_for('index'))
    recent_events = Event.query.order_by(Event.id.desc()).limit(20).all()
    return render_template_string(ADMIN_TMPL, recent_events=recent_events, current_user=current_user)

@app.route('/admin/fetch', methods=['POST'])
@login_required
def admin_fetch():
    if not current_user.is_admin:
        return jsonify({'error': '権限がありません'}), 403

    import requests as req
    from bs4 import BeautifulSoup

    url = request.json.get('url', '').strip()
    if not url:
        return jsonify({'error': 'URLを入力してください'})

    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
        res = req.get(url, headers=headers, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')

        title = ''
        for sel in ['h1', 'h2', '[class*="title"]', '[class*="event-name"]']:
            el = soup.select_one(sel)
            if el:
                title = el.get_text(strip=True)[:100]
                break
        if not title and soup.title:
            title = soup.title.get_text(strip=True)[:100]

        desc = ''
        for sel in ['[class*="description"]', '[class*="summary"]', '[class*="detail"]', 'article p']:
            el = soup.select_one(sel)
            if el:
                desc = el.get_text(strip=True)[:500]
                break

        place = ''
        for sel in ['[class*="location"]', '[class*="venue"]', '[class*="place"]']:
            el = soup.select_one(sel)
            if el:
                place = el.get_text(strip=True)[:200]
                break

        date = ''
        time_str = ''
        time_el = soup.select_one('time[datetime]')
        if time_el:
            dt_str = time_el.get('datetime', '')
            try:
                from datetime import datetime as dt
                d = dt.fromisoformat(dt_str[:19])
                date = d.strftime('%Y-%m-%d')
                time_str = d.strftime('%H:%M')
            except:
                pass

        text = title + place + desc
        area = ''
        if '東京' in text or '渋谷' in text or '新宿' in text:
            area = '東京'
        elif '大阪' in text or '梅田' in text:
            area = '大阪'
        elif '名古屋' in text:
            area = '名古屋'
        elif '福岡' in text:
            area = '福岡'
        elif 'オンライン' in text or 'online' in text.lower():
            area = 'オンライン'

        if url not in desc:
            desc = desc + f'\n\n🔗 元のページ: {url}'

        return jsonify({'title': title, 'desc': desc, 'place': place, 'date': date, 'time': time_str, 'area': area})

    except Exception as e:
        return jsonify({'error': f'読み取りに失敗しました: {str(e)}'})

@app.route('/admin/post', methods=['POST'])
@login_required
def admin_post():
    if not current_user.is_admin:
        return redirect(url_for('index'))

    event = Event(
        user_id         = current_user.id,
        title           = request.form.get('title', '').strip(),
        category        = request.form.get('category', 'All / Mix'),
        area            = request.form.get('area', ''),
        location_detail = request.form.get('location_detail', ''),
        date            = request.form.get('date', ''),
        time            = request.form.get('time', ''),
        event_type      = request.form.get('event_type', ''),
        mode            = request.form.get('mode', 'オフライン'),
        description     = request.form.get('description', ''),
        emoji           = request.form.get('emoji') or '🌈',
        image_url       = None,
        is_pickup       = False,
    )
    db.session.add(event)
    db.session.commit()
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)