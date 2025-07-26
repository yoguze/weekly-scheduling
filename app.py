from flask import Flask, render_template, request, jsonify, send_file
from datetime import datetime, timedelta
import random
import io
import os
from zoneinfo import ZoneInfo

app = Flask(__name__)

USE_PDFKIT = os.getenv('USE_PDFKIT', 'False') == 'True'

if USE_PDFKIT:
    import pdfkit
    pdfkit_config = pdfkit.configuration(wkhtmltopdf=r'C:\Users\numan\weekly-scheduling\wkhtmltopdf\bin\wkhtmltopdf.exe')
else:
    from weasyprint import HTML,CSS

calendar_events = []
flexible_event_pool = []

def assign_flexible_event(event):
    today = datetime.now(ZoneInfo("Asia/Tokyo")).date()
    if event['deadline'] < today:
        return None

    delta_days = (event['deadline'] - today).days
    candidate_days = [(today + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(1,delta_days + 1)]

    for date in candidate_days:
        available_hours = [h for h in range(9, 24 - event['hours'] + 1) if not any(
            e['date'] == date and not (e['end_hour'] <= h or e['hour'] >= h + event['hours'])
            for e in calendar_events
        )]
        if available_hours:
            selected_hour = random.choice(available_hours)
            return {
                "title": event['title'],
                "date": date,
                "hour": selected_hour,
                "end_hour": selected_hour + event['hours'] - 1,
                "fixed": False,
                "deadline": event['deadline'],
                "added_at": event['added_at']
            }
    return None

def reschedule_flexible_events():
    global calendar_events
    calendar_events = [e for e in calendar_events if e['fixed']]

    sorted_pool = sorted(flexible_event_pool, key=lambda e: (e['deadline'], e['added_at']))

    for event in sorted_pool:
        assigned = assign_flexible_event(event)
        if assigned:
            calendar_events.append(assigned)

def generate_calendar_html(events):
    days = ["月", "火", "水", "木", "金", "土", "日"]
    start_date = datetime.now() + timedelta(days=1)

    html = "<table border='1' style='border-collapse: collapse; width: 100%; text-align: center;'><tr><th>時間\\日付</th>"
    for i in range(7):
        day = start_date + timedelta(days=i)
        html += f"<th style='background-color:#dbeeff;'>{day.month}/{day.day}({days[day.weekday()]})</th>"
    html += "</tr>"

    for hour in range(9, 24):
        html += f"<tr><td>{hour}:00</td>"
        for i in range(7):
            day = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
            cell_content = ""
            for event in events:
                if event['date'] == day:
                    if event['hour'] == hour:
                        cell_content = f"<div>{event['title']}</div>"
                    elif event['hour'] < hour <= event['end_hour']:
                        cell_content = "〃"
            html += f"<td>{cell_content}</td>"
        html += "</tr>"
    html += "</table>"
    return html

@app.route('/')
def index():
    return render_template('index.html', calendar_html=generate_calendar_html(calendar_events))

@app.route('/add_flexible', methods=['POST'])
def add_flexible():
    data = request.get_json()
    title = data.get('title')
    hours = int(data.get('hours'))
    deadline = datetime.strptime(data.get('deadline'), "%Y-%m-%d").date()

    if not title or hours <= 0 or not deadline:
        return jsonify({"message": "入力項目が不足しています。"})

    flexible_event_pool.append({
        "title": title,
        "hours": hours,
        "deadline": deadline,
        "added_at": datetime.now()
    })

    reschedule_flexible_events()
    return jsonify({"message": "柔軟予定を追加・スケジュールしました。"})

@app.route('/add_fixed', methods=['POST'])
def add_fixed():
    data = request.get_json()
    title = data.get('taskTitle')
    fixed_date = data.get('fixedDate')
    start_hour = int(data.get('startTime'))
    end_hour = int(data.get('endTime'))

    if not title or not fixed_date or start_hour >= end_hour:
        return jsonify({"message": "入力項目が不足しているか、時間設定が不正です。"})

    if any(
        event['date'] == fixed_date and not (event['end_hour'] <= start_hour or event['hour'] >= end_hour) and event['fixed']
        for event in calendar_events
    ):
        return jsonify({"message": "この時間帯にはすでに固定予定が登録されています。"})

    calendar_events.append({
        "title": title,
        "date": fixed_date,
        "hour": start_hour,
        "end_hour": end_hour,
        "fixed": True
    })
    return jsonify({"message": "固定予定を追加しました。"})

@app.route('/get_calendar')
def get_calendar():
    return generate_calendar_html(calendar_events)

@app.route('/reset_all', methods=['POST'])
def reset_all():
    calendar_events.clear()
    flexible_event_pool.clear()
    return '', 204

@app.route('/download_pdf')
def download_pdf():
    html_content = generate_calendar_html(calendar_events)
    if USE_PDFKIT:
        options = {'encoding': "UTF-8"}
        pdf = pdfkit.from_string(html_content, False, configuration=pdfkit_config, options=options)
    else:
        html_content = generate_calendar_html(calendar_events)
        from weasyprint import CSS
        font_path = os.path.join(app.root_path, 'static', 'fonts', 'ipaexm.ttf')
        css = CSS(string=f'''
            @font-face {{
                font-family: "IPAexMincho";
                src: url("file://{font_path}");
            }}
            body {{
                font-family: "IPAexMincho";
            }}
            ''')
        pdf = HTML(string=html_content).write_pdf(stylesheets=[css])
        
    return send_file(
        io.BytesIO(pdf),
        mimetype='application/pdf',
        as_attachment=True,
        download_name='calendar.pdf'
    )

if __name__ == '__main__':
    import os
    port = int(os.getenv('FLASK_RUN_PORT', 10000))  # デフォルト: 10000（本番）
    debug_mode = os.getenv('FLASK_DEBUG', 'False') == 'True'
    app.run(debug=debug_mode, host='0.0.0.0', port=port)