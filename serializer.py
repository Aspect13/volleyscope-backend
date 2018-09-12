import datetime

from models_config import DATE_FORMAT


class SerializedField:

	def __init__(self, field, value):
		self.field = field
		self.initial_value = value
		self.value = self.get_value()

	def get_value(self):
		t = type(self.initial_value)
		if t is int or t is bool:
			return self.initial_value
		# if t is bool:
		# 	return 'true' if self.initial_value else 'false'
		if t is datetime.datetime:
			return self.initial_value.strftime(DATE_FORMAT)
		return str(self.initial_value)

	@property
	def data(self):
		return self.field, self.value

	# def __str__(self):
	# 	return '<SerializedField field: {}, value: {}>'.format(self.field, self.value)

	def __repr__(self):
		return '<SerializedField field: {}, value: {}>'.format(self.field, self.value)


class Serializer:
	fields = []
	instance = None

	def __init__(self, instance):
		self.instance = instance
		self.fields = instance.serialize_fields

	@property
	def serialized_fields(self):
		return map(SerializedField, self.fields.values(), self.values)

	@property
	def values(self):
		return map(self.instance.__getattribute__, self.fields.keys())

	@property
	def data(self):
		print([i.data for i in self.serialized_fields])
		return dict(i.data for i in self.serialized_fields)