# Circuitech Solar Dashboard

This project is a Flask web app for monitoring sunlight and solar panel cleaning using ThingSpeak.

ThingSpeak Channel ID: 3117457
Read API Key: O1MK5ODEM3Z7SKTE

## Run locally
1. Create a virtualenv and install:
```
pip install -r requirements.txt
```
2. Run:
```
export FLASK_APP=app.py
flask run
```
Or:
```
python app.py
```

## Deploy on Render
- Create a new Web Service on Render and connect to this repo.
- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn app:app`
