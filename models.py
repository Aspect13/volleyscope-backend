from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

ADMIN_GROUP_NAME = 'admins'

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
		else:
			print('will become inactive')
			self.is_active = False
		db.session.commit()

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
	# created_by = db.relationship('User', backref=db.backref('created_events', lazy=True))
	creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
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
