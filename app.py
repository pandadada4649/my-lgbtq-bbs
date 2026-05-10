from flask import Flask, render_template_string, request, redirect

app = Flask(__name__)

events = []

@app.route('/')
def index():
    # デザインを大幅に強化したHTML
    html = """
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>LGBTQ+ Event Hub</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body { background-color: #f0f2f5; color: #333; }
            .navbar { background: linear-gradient(90deg, #FF0000, #FF7F00, #FFFF00, #00FF00, #0000FF, #4B0082, #8B00FF); }
            .card { border: none; border-radius: 15px; transition: 0.3s; }
            .card:hover { transform: translateY(-5px); box-shadow: 0 10px 20px rgba(0,0,0,0.1); }
            .btn-primary { background-color: #ff69b4; border: none; }
            .btn-primary:hover { background-color: #ff1493; }
            .badge-date { background-color: #6c757d; font-size: 0.9em; }
        </style>
    </head>
    <body>
        <nav class="navbar navbar-dark mb-4">
            <div class="container">
                <span class="navbar-brand mb-0 h1">🌈 LGBTQ+ イベント掲示板</span>
            </div>
        </nav>

        <div class="container">
            <div class="row">
                <div class="col-md-4">
                    <div class="card p-4 mb-4">
                        <h4 class="mb-3">イベントを投稿</h4>
                        <form method="POST" action="/post">
                            <div class="mb-3">
                                <label class="form-label">イベント名</label>
                                <input type="text" name="title" class="form-control" placeholder="交流会、パレードなど" required>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">開催日</label>
                                <input type="text" name="date" class="form-control" placeholder="2026年6月1日" required>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">場所</label>
                                <input type="text" name="place" class="form-control" placeholder="大阪・堂山町" required>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">詳細</label>
                                <textarea name="detail" class="form-control" rows="3" placeholder="イベントの内容や参加方法"></textarea>
                            </div>
                            <button type="submit" class="btn btn-primary w-100">公開する</button>
                        </form>
                    </div>
                </div>

                <div class="col-md-8">
                    <h4 class="mb-3">最新のイベント一覧</h4>
                    {% if not events %}
                        <p class="text-muted">まだ投稿がありません。最初のイベントを投稿してみよう！</p>
                    {% endif %}
                    {% for ev in events %}
                        <div class="card mb-3">
                            <div class="card-body">
                                <span class="badge badge-date mb-2">{{ ev.date }}</span>
                                <h5 class="card-title">{{ ev.title }}</h5>
                                <h6 class="card-subtitle mb-2 text-muted">📍 {{ ev.place }}</h6>
                                <p class="card-text">{{ ev.detail }}</p>
                            </div>
                        </div>
                    {% endfor %}
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return render_template_string(html, events=events)

@app.route('/post', methods=['POST'])
def post():
    new_event = {
        "title": request.form.get('title'),
        "date": request.form.get('date'),
        "place": request.form.get('place'),
        "detail": request.form.get('detail')
    }
    events.insert(0, new_event)
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)S