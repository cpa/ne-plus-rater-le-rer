import pickle
import requests as requests
import datetime
import arrow
from flask import Flask, render_template

app = Flask(__name__)

def compute_eta(message, timestamp):
    if message[2] == ':' and int(message[:2]) in range(24):
        h = int(message[:2])
        m = int(message[3:5])
        eta = str(((h - timestamp.hour)%24)*60 + m - timestamp.minute)
    else:
        eta = ''
    return eta 

def show(message, mission):
    missions = pickle.load(open('missions.pickle', 'rb'))

    f1 = 'Train sans ' in message or 'approche' in message or 'terminus' in message or 'quai' in message
    f2 = True

    try:
        r = missions[mission]
    except Exception as e:
        r = requests.get('https://api-ratp.pierre-grimaud.fr/v3/mission/rers/B/'+mission).json()
        missions[mission] = r

    for n in r['result']['stations']:
        if n['name'] == 'Bagneux':
            f2 = False

    pickle.dump(missions, open('missions.pickle', 'wb'))

    return f1 or f2

def make_cards(r, style, direction):
    timestamp = arrow.get(r['_metadata']['date'])
    cards = []
    for train in r['result']['schedules']:
        tmp = {}
        tmp['style'] = style
        tmp['eta'] = compute_eta(train['message'], timestamp)
        tmp['direction'] = direction
        tmp['time'] = train['message']
        tmp['mission'] = train['code']

        # tmp['destination'] = train['destination']
        if show(train['message'], train['code']):
            # tmp['style'] = 'light'
            continue
        cards.append(tmp)
    return cards



@app.route("/")
def index():
    r1 = requests.get('https://api-ratp.pierre-grimaud.fr/v3/schedules/rers/B/bagneux/A').json()
    r2 = requests.get('https://api-ratp.pierre-grimaud.fr/v3/schedules/rers/B/denfert-rochereau/R').json()

    c1 = make_cards(r1, style='background-color: #FFE0B2', direction='↑')
    c2 = make_cards(r2, style='background-color: #B2DFDB', direction='↓')

    sB = requests.get('https://api-ratp.pierre-grimaud.fr/v3/traffic/rers/B').json()
    s6 = requests.get('https://api-ratp.pierre-grimaud.fr/v3/traffic/metros/6').json()

    return render_template('index.j2.html', cards=c1+c2, statusB=sB, status6=s6)

# app.run(host='0.0.0.0', port=8000, debug=True)
