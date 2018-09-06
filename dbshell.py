import sqlalchemy

from app import app
from models import Event, User, db, participants, Group, ADMIN_GROUP_NAME

app.app_context().push()

try:
	u = User.query.first()
except sqlalchemy.exc.OperationalError:
	print('Creating db...')
	db.create_all(app=app)
finally:
	u = User.query.first()

if u is None:
	print('creating user')
	u = User(first_name='Vladimir', last_name='Putin', email='Vladimir666@mail.rf', password='iamtheking', phone='89161234567')
	db.session.add(u)
	db.session.commit()
	u = User.query.first()

e1 = Event(start=db.func.now(), end=db.func.now(), title='title1', desc='desc1', creator_id=u.id)
e2 = Event(start=db.func.now(), end=db.func.now(), title='title2', desc='desc2', creator_id=u.id)
e = Event.query.first()
if e is None:
	print('creating events')
	db.session.add(e1)
	db.session.add(e2)
	db.session.commit()
	e = Event.query.first()

g = Group.query.filter_by(name=ADMIN_GROUP_NAME).first()
if g is None:
	print('creating group', ADMIN_GROUP_NAME)
	g = Group(name=ADMIN_GROUP_NAME, creator_id=u.id, members=[u])
	db.session.add(g)
	db.session.commit()
	g = Group.query.filter_by(name=ADMIN_GROUP_NAME).first()


def participate(user, event):
	user.participates_in.append(event)
	db.session.commit()


def unsubscribe(user, event):
	user.participates_in.remove(event)
	db.session.commit()


def drop():
	tables = db.metadata.tables.keys()

	for table in tables:
		db.engine.execute('drop table "{}"'.format(table))
