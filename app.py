from flask import Flask, jsonify
from flask_jwt import JWT
from werkzeug.security import safe_str_cmp

from models import db, User
from views import app as rest_api

app = Flask(__name__)
app.config.from_json('config.json')


from datetime import timedelta
app.config['JWT_EXPIRATION_DELTA'] = timedelta(days=10)


def authenticate(email, password):
	print('***authenticate', email, password)
	user = User.query.filter_by(email=email).first_or_404()
	print('***authenticate', user)
	if user.is_active and user.check_password(password.encode('utf-8')):
		return user
	return


def identify(payload):
	print('***identify', payload)
	user_id = payload['identity']
	user = User.query.get(user_id)
	print('***identify', user, user.is_active)
	if user.is_active:
		return user
	return


jwt = JWT(app, authenticate, identify)

app.register_blueprint(rest_api)
db.init_app(app)


# db = SQLAlchemy(app)


@app.before_first_request
def init_db():
	print('EVENT FIRED, db created')
	db.create_all(app=app)


if __name__ == '__main__':
	app.run(host='localhost', port=8000, debug=True)
