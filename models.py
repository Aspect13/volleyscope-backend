import json
from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

from models_config import ADMIN_GROUP_NAME, DATE_FORMAT
from serializer import Serializer


# from app import db
db = SQLAlchemy()

participants = db.Table(
	'participants',
	db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
	db.Column('event_id', db.Integer, db.ForeignKey('event.id'), primary_key=True)
)

groups = db.Table(
	'groups',
	db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
	db.Column('group_id', db.Integer, db.ForeignKey('group.id'), primary_key=True)
)


class User(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	# username = db.Column(db.String(80), unique=True, nullable=False)
	first_name = db.Column(db.String(80), nullable=False)
	last_name = db.Column(db.String(80), nullable=False)
	password = db.Column(db.String(500), nullable=False)
	email = db.Column(db.String(120), unique=True, nullable=False)
	date_joined = db.Column(db.DateTime, nullable=False, default=db.func.now())
	is_active = db.Column(db.Boolean, default=True, nullable=False)
	phone = db.Column(db.String(11), nullable=True, )
	# created_events_id = db.Column(db.Integer, db.ForeignKey('Event.id'), nullable=True)
	created_events = db.relationship(
		'Event',
		backref=db.backref('creator', lazy=True),
		foreign_keys='[Event.creator_id]'
	)
	participates_in = db.relationship(
		'Event',
		secondary=participants,
		lazy='subquery',
		backref=db.backref('participants', lazy=True)
	)

	serialize_fields = {
		'id': 'id',
		'first_name': 'first_name',
		'last_name': 'last_name',
		'email': 'email',
		'date_joined': 'date_joined',
		'is_active': 'is_active',
		'phone': 'phone'
	}

	@property
	def is_admin(self):
		return bool(next((x for x in self.member_of if x.name == ADMIN_GROUP_NAME), None))

	# created_events = db.relationship('Event', backref=db.backref('creator', lazy=True),)
	# participates_in_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=True)
	# participants_id = db.Column(db.Integer, db.ForeignKey('participate_in.id'), nullable=False)
	def __init__(self, password, email, **kwargs):
		# self.username = username
		super(User, self).__init__(**kwargs)
		self.email = email
		self.set_password(password)

	def set_password(self, password):
		self.password = generate_password_hash(password)

	def check_password(self, password):
		return check_password_hash(self.password, password)

	def _create(self):
		db.session.add(self)
		db.session.commit()

	def _delete(self, accessor):
		print('delete called')
		if accessor.is_admin:
			print('will be deleted')
			db.session.delete(self)
		elif not self.is_active:
			return 'Item is deleted or inactive', 404
		else:
			print('will become inactive')
			self.is_active = False
		db.session.commit()

	def _update(self, new_data):
		for k, v in new_data.items():
			self.__setattr__(k, v)

	def _change(self, accessor, new_data):
		print('accessor', accessor, accessor.is_admin, self.id, accessor.id)
		print('new_data', new_data)
		if accessor.is_admin or self.id == accessor.id:
			old_password = new_data.pop('old_password', None)
			new_password = new_data.pop('new_password', None)
			new_data.pop('password', None)
			print('after pops', new_data, old_password, new_password)

			self._update(new_data)
			if old_password:
				print('change password requested')
				if self.check_password(old_password):
					print('old password is ok')
					self.set_password(new_password)
			db.session.commit()
		else:
			raise PermissionError

	@property
	def serialized(self):
		return Serializer(self).data

	def __repr__(self):
		return '<user: {}_{}, id: {}>'.format(self.first_name, self.last_name, self.id)


class Group(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
	creation_date = db.Column(db.DateTime, nullable=False, default=db.func.now())
	name = db.Column(db.String(100), nullable=False, unique=True)
	members = db.relationship(
		'User',
		secondary=groups,
		lazy='subquery',
		backref=db.backref('member_of', lazy=True)
	)


class Event(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	start = db.Column(db.DateTime, nullable=False)
	end = db.Column(db.DateTime, nullable=False)
	title = db.Column(db.String(100), nullable=False)
	desc = db.Column(db.String(1000), nullable=True)
	all_day = db.Column(db.Boolean, nullable=False, default=False)
	# created_by = db.relationship('User', backref=db.backref('created_events', lazy=True))
	creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

	serialize_fields = {
		'id': 'id',
		'start': 'start',
		'end': 'end',
		'title': 'title',
		'desc': 'desc',
		'all_day': 'allDay',
		'creator_id': 'creator_id'
	}

	@staticmethod
	def validate(data):
		# 2018-06-09T17:00:00.000Z
		start = data.get('start', None)
		start = datetime.strptime(start, DATE_FORMAT)
		print('startstartstartstartstart', start, start.day)
		end = data.get('end', None)
		all_day = bool(data.get('allDay', False))
		if end:
			end = datetime.strptime(end, DATE_FORMAT)
		elif all_day:
			end = start.replace(hour=23, minute=59, second=59, microsecond=0)
		assert start
		assert end
		data.update({'start': start, 'end': end, 'all_day': all_day})
		return data

	def _create(self):
		db.session.add(self)
		db.session.commit()

	def _delete(self, accessor):
		print('delete called')
		if accessor.is_admin or self.creator_id == accessor.id:
			print('will be deleted')
			db.session.delete(self)
		db.session.commit()

	def _update(self, new_data):
		for k, v in new_data.items():
			self.__setattr__(k, v)

	def _change(self, accessor, new_data):
		print('accessor', accessor, accessor.is_admin, self.id, accessor.id)
		print('new_data', new_data)
		if accessor.is_admin or self.creator_id == accessor.id:
			self._update(self.validate(new_data))
			db.session.commit()
		else:
			raise PermissionError

	@property
	def serialized(self):

		# d = Serializer(self)
		# for i in d.serialized_fields:
		# 	print('*** ', i)
		# print(d.data)
		# d = dict(
		# 	zip(
		# 		self.serialize_fields.values(),
		# 		map(type, map(self.__getattribute__, self.serialize_fields.keys()))
		# 	)
		# )
		# # d = dict()
		# # for i in self.serialize_fields:
		# # 	d[i] = self.__getattribute__(i)
		# print('dddddddddddddddd', d)
		# print('dddddddddddddddd', json.dumps(d))
		# return json.dumps(d.data) if to_json else d.data
		return Serializer(self).data


# participants = db.relationship('User', backref=db.backref('participates_in', lazy=True), foreign_keys='[User.participates_in_id]')

# class Participants(db.Model):
# 	# __tablename__ = 'participants'
# 	id = db.Column(db.Integer, primary_key=True)
# 	user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
# 	event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
#
# 	date_joined = db.Column(db.DateTime, default=db.func.now(), nullable=False)
#
# 	user = db.relationship('User', backref=db.backref('participates_in', cascade="all, delete-orphan"))
# 	event = db.relationship('Event', backref=db.backref("participants", cascade="all, delete-orphan"))
#
# 	def __repr__(self):
# 		return '{} -> {}'.format(self.user, self.event)
