# coding: utf-8
from sqlalchemy import Column, Date, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from app import db
from flask_serialize import FlaskSerializeMixin

FlaskSerializeMixin.db = db

class Measurement(FlaskSerializeMixin, db.Model):
    __tablename__ = 'Measurement'

    Measurement_ID = db.Column(db.Integer, primary_key=True)
    Value = db.Column(db.Float(asdecimal=True))
    Point_ID = db.Column(db.ForeignKey('Point.Point_ID'), index=True)
    Try_ID = db.Column(db.ForeignKey('Try.Try_ID'), index=True)
    Measurement_type_ID = db.Column(db.ForeignKey('Measurement_type.Measurement_type_ID'), index=True)

    Measurement_type = db.relationship('MeasurementType', primaryjoin='Measurement.Measurement_type_ID == MeasurementType.Measurement_type_ID', backref='measurements')
    Point = db.relationship('Point', primaryjoin='Measurement.Point_ID == Point.Point_ID', backref='measurements')

    create_fields = update_fields = ['Value', 'Point_ID', 'Try_ID', 'Measurement_type_ID']



class MeasurementType(FlaskSerializeMixin, db.Model):
    __tablename__ = 'Measurement_type'

    Measurement_type_ID = db.Column(db.Integer, primary_key=True)
    Measurement_type_name = db.Column(db.String(100))
    PDK = db.Column(db.Float(asdecimal=True))
    Measurement_unit_id = db.Column(db.ForeignKey('Measurement_unit.Measurement_unit_id'), index=True)
    is_weather_condition = db.Column(db.Integer)

    Measurement_unit = db.relationship('MeasurementUnit', primaryjoin='MeasurementType.Measurement_unit_id == MeasurementUnit.Measurement_unit_id', backref='measurement_types')

    create_fields = update_fields = ['Measurement_type_name', 'PDK', 'Measurement_unit_id', 'is_weather_condition']



class MeasurementUnit(FlaskSerializeMixin, db.Model):
    __tablename__ = 'Measurement_unit'

    Measurement_unit_id = db.Column(db.Integer, primary_key=True)
    Measurement_unit_name = db.Column(db.String(100))

    create_fields = update_fields = ['Measurement_unit_name']



class Organization(FlaskSerializeMixin, db.Model):
    __tablename__ = 'Organization'

    Organization_ID = db.Column(db.Integer, primary_key=True)
    Organization_name = db.Column(db.String(100))

    create_fields = update_fields = ['Organization_name']



class Point(FlaskSerializeMixin, db.Model):
    __tablename__ = 'Point'

    Point_ID = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(100))
    Latitude = db.Column(db.Integer)
    Longitude = db.Column(db.Integer)
    Point_type_ID = db.Column(db.ForeignKey('Point_type.Point_type_ID'), index=True)

    Point_type = db.relationship('PointType', primaryjoin='Point.Point_type_ID == PointType.Point_type_ID', backref='points')

    create_fields = update_fields = ['Name', 'Latitude', 'Longitude', 'Point_type_ID']



class PointType(FlaskSerializeMixin, db.Model):
    __tablename__ = 'Point_type'

    Point_type_ID = db.Column(db.Integer, primary_key=True)
    Point_type_name = db.Column(db.String(100))

    create_fields = update_fields = ['Point_type_name']



class Position(FlaskSerializeMixin, db.Model):
    __tablename__ = 'Position'

    Position_ID = db.Column(db.Integer, primary_key=True)
    Position_name = db.Column(db.String(100))

    create_fields = update_fields = ['Position_name']



class Try(FlaskSerializeMixin, db.Model):
    __tablename__ = 'Try'

    Try_ID = db.Column(db.Integer, primary_key=True)
    Start_time = db.Column(db.DateTime)
    User_ID = db.Column(db.ForeignKey('User.User_ID'), index=True)
    Is_public = db.Column(db.Integer)
    Duration = db.Column(db.Integer)
    Cicle_number = db.Column(db.Integer)

    User = db.relationship('User', primaryjoin='Try.User_ID == User.User_ID', backref='tries')

    create_fields = update_fields = ['Start_time', 'User_ID', 'Is_public', 'Duration', 'Cicle_number']



class User(FlaskSerializeMixin, db.Model):
    __tablename__ = 'User'

    User_ID = db.Column(db.Integer, primary_key=True)
    Login = db.Column(db.String(100))
    Password_hash = db.Column(db.String(300))
    Type_id = db.Column(db.ForeignKey('User_type.Type_id'), index=True)
    FIO = db.Column(db.String(100))
    Organization_ID = db.Column(db.ForeignKey('Organization.Organization_ID'), index=True)
    Position_ID = db.Column(db.ForeignKey('Position.Position_ID', ondelete='RESTRICT', onupdate='RESTRICT'), index=True)

    Organization = db.relationship('Organization', primaryjoin='User.Organization_ID == Organization.Organization_ID', backref='users')
    Position = db.relationship('Position', primaryjoin='User.Position_ID == Position.Position_ID', backref='users')
    UserType = db.relationship('UserType', primaryjoin='User.Type_id == UserType.Type_id', backref='users')

    create_fields = update_fields = ['Login', 'Password_hash', 'Type_id', 'FIO', 'Organization_ID', 'Position_ID']




class UserType(FlaskSerializeMixin, db.Model):
    __tablename__ = 'User_type'

    Type_id = db.Column(db.Integer, primary_key=True)
    Type_name = db.Column(db.String(100))

    create_fields = update_fields = ['Type_name']

