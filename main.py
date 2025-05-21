from flask import Flask, request, jsonify, render_template, url_for
import sqlite3
import os
import json

app = Flask(__name__)

# database setup
def init_db():
    conn = sqlite3.connect('sortinghat.db')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_answers TEXT,
        house TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    conn.commit()
    conn.close()

# calculate house based on answers
def calculate_house(selections):
    house_points = {
        "Gryffindor": 0,
        "Hufflepuff": 0,
        "Ravenclaw": 0,
        "Slytherin": 0
    }

    for question_id, answer_house in selections.items():
        house_points[answer_house] += 1

    max_points = 0
    chosen_house = ""
    for house, points in house_points.items():
        if points > max_points:
            max_points = points
            chosen_house = house

    if chosen_house == "":
        chosen_house = "Gryffindor"

    return chosen_house, house_points

@app.route('/')
def index():
    return render_template('Potter3.1.html')

@app.route('/submit', methods=['POST'])
def submit():
    if request.is_json:
        selections = request.json
    else:
        selections = {}
        for question, house in request.form.items():
            selections[question] = house

    house, house_points = calculate_house(selections)

    conn = sqlite3.connect('sortinghat.db')
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO user_results (user_answers, house) VALUES (?, ?)',
        (json.dumps(selections), house)
    )
    conn.commit()
    conn.close()

    return jsonify({
        "house": house,
        "points": house_points[house]
    })

@app.route('/results', methods=['GET'])
@app.route('/houses', methods=['GET'])
def houses():
    conn = sqlite3.connect('sortinghat.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM user_results ORDER BY house')
    users = cursor.fetchall()

    grouped_users = {
        "Gryffindor": [],
        "Hufflepuff": [],
        "Ravenclaw": [],
        "Slytherin": []
    }

    for user in users:
        user_dict = {
            'id': user['id'],
            'timestamp': user['timestamp']
        }
        grouped_users[user['house']].append(user_dict)

    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Sorting Hat Results</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
            h1 { color: #333; text-align: center; }
            .house { margin-bottom: 30px; padding: 15px; border-radius: 8px;
                     box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .gryffindor { background-color: #740001; color: #D3A625; }
            .hufflepuff { background-color: #ECB939; color: #000000; }
            .ravenclaw { background-color: #0E1A40; color: #946B2D; }
            .slytherin { background-color: #1A472A; color: #5D5D5D; }
            .count { font-size: 2em; font-weight: bold; text-align: center; }
            ul { list-style-type: none; padding-left: 20px; }
            .back {
                display: block;
                width: 100px;
                margin: 20px auto;
                text-align: center;
                padding: 10px;
                background-color: #333;
                color: white;
                text-decoration: none;
                border-radius: 5px;
            }
        </style>
    </head>
    <body>
        <h1>Hogwarts House Sorting Results</h1>
    '''

    for house, users_list in grouped_users.items():
        html += f'''
        <div class="house {house.lower()}">
            <h2>{house}</h2>
            <div class="count">{len(users_list)}</div>
            <p>Students sorted into this house: {len(users_list)}</p>
        </div>
        '''

    html += '''
        <a href="/" class="back">Return to Quiz</a>
    </body>
    </html>
    '''

    return html

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
