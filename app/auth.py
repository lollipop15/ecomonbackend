from functools import wraps
from flask import request, Response, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import User, UserType
import jwt

def authenticate(**kwargs):
    login = kwargs.get('login')
    password = kwargs.get('password')

    if not login or not password:
        return None
    
    user = User.query.filter_by(Login = login).first()
    if not user or not check_password_hash(user.Password_hash, password):
        return None

    return user


def token_required(f):
    @wraps(f)
    def _verify(*args, **kwargs):
        auth_headers = request.headers.get('Authorization', '').split()

        invalid_msg = {
            'message': 'Invalid token. Registeration and / or authentication required',
            'authenticated': False
        }
        expired_msg = {
            'message': 'Expired token. Reauthentication required.',
            'authenticated': False
        }

        if len(auth_headers) != 2:
            return jsonify(invalid_msg), 401

        try:
            token = auth_headers[1]
            data = jwt.decode(token, current_app.config['SECRET_KEY'])
            user = User.query.first()
            if not user:
                raise RuntimeError('User not found')
            return f(user, *args, **kwargs)
        except jwt.ExpiredSignatureError:
            return jsonify(expired_msg), 401 # 401 is Unauthorized HTTP status code
        except (jwt.InvalidTokenError, Exception) as e:
            print(e)
            return jsonify(invalid_msg), 401

    return _verify

def check_user_rights(f):
    def _check_rights(user, object_name, *args, **kwargs):
        unauth_message = {
            'message': 'You are not unauthorized to complete this request'
        }
        user_type = UserType.query.first()
        if (user_rights[user_type.Type_name].count(object_name) != 0):
            return f(user, object_name, *args, **kwargs)
        else:
            return jsonify(unauth_message), 403
    return _check_rights

def only_admin(f):
    @wraps(f)
    def _check_admin(user, *args, **kwargs):
        unauth_message = {
            'message': 'You are not unauthorized to complete this request'
        }
        user_type = UserType.query.filter_by(Type_id = user.Type_id).first()
        if (user_type.Type_name != 'Администратор'):
            return jsonify(unauth_message), 403
        else:
            return f(user, *args, **kwargs)
    return _check_admin



user_rights = {
    'Администратор': [
        'measurement',
        'measurement_type',
        'measurement_unit',
        'organization',
        'point',
        'point_type',
        'position',
        'try',
        'user',
        'user_type'
    ],
    'Эколог': [
        'measurement',
        'measurement_type',
        'measurement_unit',
        'point',
        'point_type',
        'try',
    ]
}
