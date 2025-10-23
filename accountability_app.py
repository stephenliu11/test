from flask import Flask, render_template_string, request, redirect, url_for
import sqlite3
from datetime import date

app = Flask(__name__)
DB_FILE = 'accountability.db'

# Initialize DB
def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS points (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user TEXT NOT NULL,
                entry_date DATE NOT NULL,
                good_points INTEGER NOT NULL,
                bad_points INTEGER NOT NULL
            )
        ''')
init_db()

# Home page: form to submit points
template_form = '''
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Accountability Tracker</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        .golfer { font-size: 2em; margin: 10px 0; }
        .winner { color: #198754; font-weight: bold; }
        .loser { color: #6c757d; }
        .progress { height: 2rem; }
        .streak { font-size: 1.2em; color: #0d6efd; }
        .confetti { animation: confetti 1s linear; }
        @keyframes confetti {
            0% { opacity: 0; }
            50% { opacity: 1; }
            100% { opacity: 0; }
        }
    </style>
</head>
<body class="bg-light">
<div class="container py-4">
    <h1 class="mb-4 text-center">🏆 Accountability Tracker</h1>
    <div class="card shadow mb-4">
        <div class="card-body">
            <h4 class="card-title">{{ month_name }} Points Entry</h4>
            <form method="post" class="row g-3">
                <div class="col-md-3">
                    <label class="form-label">Name</label>
                    <select name="user" class="form-select" required>
                        <option value="Ethan">Ethan</option>
                        <option value="Stephen">Stephen</option>
                    </select>
                </div>
                <div class="col-md-3">
                    <label class="form-label">Date</label>
                    <input name="entry_date" type="date" class="form-control" value="{{ today }}" required>
                </div>
                <div class="col-md-2">
                    <label class="form-label">Good Points</label>
                    <input name="good_points" type="number" class="form-control" required>
                </div>
                <div class="col-md-2">
                    <label class="form-label">Bad Points</label>
                    <input name="bad_points" type="number" class="form-control" required>
                </div>
                <div class="col-md-2 d-flex align-items-end">
                    <button type="submit" class="btn btn-success w-100">Submit</button>
                </div>
            </form>
        </div>
    </div>
    <div class="card shadow mb-4">
        <div class="card-body">
            <h5>{{ month_name }} Standings</h5>
            <div class="row align-items-center">
                <div class="col-md-5 text-center">
                    <span class="fw-bold">Ethan</span><br>
                    <span class="streak">🔥 Streak: {{ streaks['Ethan'] }} days</span>
                </div>
                <div class="col-md-2 text-center">
                    <span class="display-6">vs</span>
                </div>
                <div class="col-md-5 text-center">
                    <span class="fw-bold">Stephen</span><br>
                    <span class="streak">🔥 Streak: {{ streaks['Stephen'] }} days</span>
                </div>
            </div>
            <div class="progress my-3">
                <div class="progress-bar bg-success" role="progressbar" style="width: {{ ethan_pct }}%" aria-valuenow="{{ ethan }}" aria-valuemin="0" aria-valuemax="{{ max_score }}">Ethan: {{ ethan }}</div>
                <div class="progress-bar bg-primary" role="progressbar" style="width: {{ stephen_pct }}%" aria-valuenow="{{ stephen }}" aria-valuemin="0" aria-valuemax="{{ max_score }}">Stephen: {{ stephen }}</div>
            </div>
            <div class="golfer text-center">
                {% if winner %}
                    <span class="winner">🏌️‍♂️ {{ winner }} is ahead by {{ lead }} points!</span><br>
                    <span class="loser">{{ loser }} is trailing. ⛳</span>
                {% else %}
                    <span>It's a tie! Both golfers are neck and neck! 🏌️‍♂️🏌️‍♂️</span>
                {% endif %}
            </div>
            {% if show_confetti %}
                <div class="confetti">🎉🎉🎉</div>
            {% endif %}
        </div>
    </div>
    <div class="text-center mb-3">
        <a href="{{ url_for('history') }}" class="btn btn-outline-secondary">View History</a>
    </div>
    <div class="alert alert-info text-center">
        <b>Motivation:</b> "Success is the sum of small efforts, repeated day in and day out." – Robert Collier
    </div>
</div>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
'''

@app.route('/', methods=['GET', 'POST'])
def home():
    import datetime
    import calendar
    show_confetti = False
    if request.method == 'POST':
        user = request.form['user']
        good = int(request.form['good_points'])
        bad = int(request.form['bad_points'])
        entry_date = request.form['entry_date']
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute(
                'INSERT INTO points (user, entry_date, good_points, bad_points) VALUES (?, ?, ?, ?)',
                (user, entry_date, good, bad)
            )
        # Check if this submission changes the leader
        today = date.today().isoformat()
        month_prefix = today[:7]
        with sqlite3.connect(DB_FILE) as conn:
            data = conn.execute('SELECT user, SUM(good_points), SUM(bad_points) FROM points WHERE entry_date LIKE ? GROUP BY user', (month_prefix+'%',)).fetchall()
        scores = {row[0]: (row[1] or 0) - (row[2] or 0) for row in data}
        ethan = scores.get('Ethan', 0)
        stephen = scores.get('Stephen', 0)
        if (user == 'Ethan' and ethan > stephen) or (user == 'Stephen' and stephen > ethan):
            show_confetti = True
        return redirect(url_for('home', confetti=int(show_confetti)))
    # Calculate current month
    today = date.today().isoformat()
    month_prefix = today[:7]  # 'YYYY-MM'
    year, month_num = today[:4], int(today[5:7])
    month_name = f"{calendar.month_name[month_num]} {year}"
    with sqlite3.connect(DB_FILE) as conn:
        data = conn.execute('SELECT user, SUM(good_points), SUM(bad_points) FROM points WHERE entry_date LIKE ? GROUP BY user', (month_prefix+'%',)).fetchall()
        # Calculate streaks
        streaks = {'Ethan': 0, 'Stephen': 0}
        for user in ['Ethan', 'Stephen']:
            # Get all unique dates for this user this month
            dates = conn.execute('SELECT DISTINCT entry_date FROM points WHERE user=? AND entry_date LIKE ? ORDER BY entry_date DESC', (user, month_prefix+'%')).fetchall()
            streak = 0
            day = datetime.date.today()
            for d in dates:
                if d[0] == day.isoformat():
                    streak += 1
                    day -= datetime.timedelta(days=1)
                else:
                    break
            streaks[user] = streak
    scores = {row[0]: (row[1] or 0) - (row[2] or 0) for row in data}
    ethan = scores.get('Ethan', 0)
    stephen = scores.get('Stephen', 0)
    max_score = max(1, ethan, stephen)
    ethan_pct = int(100 * ethan / max_score) if max_score else 50
    stephen_pct = int(100 * stephen / max_score) if max_score else 50
    if ethan > stephen:
        winner, loser, lead = 'Ethan', 'Stephen', ethan - stephen
    elif stephen > ethan:
        winner, loser, lead = 'Stephen', 'Ethan', stephen - ethan
    else:
        winner = loser = lead = None
    show_confetti = request.args.get('confetti', '0') == '1'
    return render_template_string(template_form, winner=winner, loser=loser, lead=lead, today=today, ethan=ethan, stephen=stephen, ethan_pct=ethan_pct, stephen_pct=stephen_pct, max_score=max_score, streaks=streaks, show_confetti=show_confetti, month_name=month_name)

# History page: show all entries
template_history = '''
<!doctype html>
<title>Accountability History</title>
<h2>Points History ({{ month_name }})</h2>
<form method="get">
    <label>Month: <input type="month" name="month" value="{{ month }}"></label>
    <input type="submit" value="Go">
</form>
<table border=1>
<tr><th>Date</th><th>Name</th><th>Good</th><th>Bad</th></tr>
{% for row in rows %}
<tr><td>{{ row[2] }}</td><td>{{ row[1] }}</td><td>{{ row[3] }}</td><td>{{ row[4] }}</td></tr>
{% endfor %}
<tr style="font-weight:bold;background:#eef;">
    <td colspan=2>Total Ethan</td><td>{{ sums['Ethan']['good'] }}</td><td>{{ sums['Ethan']['bad'] }}</td>
</tr>
<tr style="font-weight:bold;background:#eef;">
    <td colspan=2>Total Stephen</td><td>{{ sums['Stephen']['good'] }}</td><td>{{ sums['Stephen']['bad'] }}</td>
</tr>
<tr style="font-weight:bold;background:#cfc;">
    <td colspan=2>Net Ethan</td><td colspan=2>{{ sums['Ethan']['good'] - sums['Ethan']['bad'] }}</td>
</tr>
<tr style="font-weight:bold;background:#cfc;">
    <td colspan=2>Net Stephen</td><td colspan=2>{{ sums['Stephen']['good'] - sums['Stephen']['bad'] }}</td>
</tr>
</table>
<br>
<a href="{{ url_for('home') }}">Back to Entry</a>
'''

@app.route('/history')
def history():
    import calendar
    from datetime import datetime
    month = request.args.get('month')
    if not month:
        month = date.today().isoformat()[:7]
    month_prefix = month
    year, month_num = int(month[:4]), int(month[5:7])
    month_name = f"{calendar.month_name[month_num]} {year}"
    with sqlite3.connect(DB_FILE) as conn:
        rows = conn.execute('SELECT * FROM points WHERE entry_date LIKE ? ORDER BY entry_date DESC, id DESC', (month_prefix+'%',)).fetchall()
        sums = {'Ethan': {'good': 0, 'bad': 0}, 'Stephen': {'good': 0, 'bad': 0}}
        for user in ['Ethan', 'Stephen']:
            res = conn.execute('SELECT SUM(good_points), SUM(bad_points) FROM points WHERE user=? AND entry_date LIKE ?', (user, month_prefix+'%')).fetchone()
            sums[user]['good'] = res[0] or 0
            sums[user]['bad'] = res[1] or 0
    return render_template_string(template_history, rows=rows, sums=sums, month=month, month_name=month_name)

if __name__ == '__main__':
    app.run(debug=True)
