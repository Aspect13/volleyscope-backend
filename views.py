from functools import wraps

from flask import jsonify, Blueprint, render_template, request, json, current_app
from flask.views import MethodView
from flask_jwt import JWT, jwt_required, current_identity, JWTError, _jwt_required

from models import User, Event

app = Blueprint('api', __name__, static_folder='static', template_folder='templates', url_prefix=None)

def register_api(view, endpoint, url, pk='id', pk_type='int'):
	view_func = view.as_view(endpoint)
	app.add_url_rule(url, defaults={pk: None}, view_func=view_func, methods=['GET', ])
	app.add_url_rule(url, view_func=view_func, methods=['POST', ])
	app.add_url_rule(f'{url}<{pk_type}:{pk}>', view_func=view_func, methods=['GET', 'PUT', 'DELETE'])



@app.route('/')
def index():
	if not current_identity:
		return 'Not Authorized!'
	return render_template('tst.html', user=current_identity.first_name + ' ' + current_identity.last_name)



# @app.before_request
# # @jwt_required()
# def handle_before_request():
# 	pass


@app.route('/login', methods=['POST', 'GET'])
def login():
	print(request.method)
	# print(request.user)
	print(request.get_json())
	print(request.form)
	print(request.data)
	print(request.json)
	print('current_identity', current_identity)
	# print('is admin:', request.user.is_admin)
	return jsonify(str(request.form.keys())), 200


def jwt_wrapper(fn):
	@wraps(fn)
	def decorator(*args, **kwargs):
		_jwt_required(current_app.config['JWT_DEFAULT_REALM'])
		return fn(*args, **kwargs)

	return decorator


class ModelAPI(MethodView):
	# decorators = [jwt_wrapper]
	Model = None

	@jwt_wrapper
	def get(self, id):
		print('VIEW GET', id, request)
		if id is None:
			return jsonify([i.serialized for i in self.Model.query.all()])
		else:
			return jsonify(self.Model.query.get_or_404(id).serialized)

	@jwt_wrapper
	def post(self):
		# create a new user
		data = json.loads(request.data)
		print('request data', data)
		new_item = self.Model(**data)
		print('new_item', new_item)
		try:
			new_item._create()
		except AttributeError as e:
			return jsonify({'error': e.args[0]}), 501
		except Exception as e:
			print(e)
			return jsonify({'error': e.args[0]}), 400
		return str(new_item), 201

	@jwt_wrapper
	def delete(self, id):
		# item = self.Model.query.filter(self.Model.id == id).delete(synchronize_session=False)
		item = self.Model.query.get_or_404(id)
		print('deleted item: ', item)
		try:
			item._delete(current_identity)
		except AttributeError as e:
			return jsonify({'error': e.args[0]}), 501
		return 'OK', 200

	@jwt_wrapper
	def put(self, id):
		item = self.Model.query.get_or_404(id)
		data = json.loads(request.data)
		print('Changing item: ', item, data)
		try:
			item._change(current_identity, data)
		except AttributeError as e:
			return jsonify({'error': e.args[0]}), 501
		except PermissionError as e:
			return jsonify({'error': e.args[0]}), 401
		return 'OK', 200

	def options(self):
		return 'OK', 200


class UserView(ModelAPI):
	Model = User

	def post(self):
		data = json.loads(request.data)
		print('request data', data)
		new_item = self.Model(**data)
		print('new_item', new_item)
		try:
			new_item._create()
		except AttributeError as e:
			return jsonify({'error': e.args[0]}), 501
		except Exception as e:
			print(e)
			return jsonify({'error': e.args[0]}), 400
		return str(new_item), 201

from datetime import datetime
class EventView(ModelAPI):
	Model = Event

	@jwt_wrapper
	def post(self):
		data = json.loads(request.data)
		data['creator_id'] = current_identity.id
		print('request data', data)
		new_item = self.Model(**self.Model.validate(data))
		print('new_item', new_item)
		try:
			new_item._create()
		except AttributeError as e:
			return jsonify({'error': e.args[0]}), 501
		except Exception as e:
			print(e)
			return jsonify({'error': e.args[0]}), 400
		return str(new_item), 201


register_api(UserView, 'users', '/users/')
register_api(EventView, 'events', '/events/')
