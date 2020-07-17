import os

class Config(object):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI') or 'mysql+pymysql://mysql:mysql@192.168.240.50:3306/ecomondb'
    SECRET_KEY = os.environ.get('SECRET_KEY') or '536f80804b7c77da71c3310cd27bc79baa006b96c2de7f2e'
