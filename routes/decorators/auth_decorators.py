from functools import wraps
from flask import request, jsonify, g
from flask_jwt_extended import jwt_required, get_jwt_identity

from config.config import Config
from models.models import User

import jwt


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'access_token_cookie' in request.cookies.keys():
            token = request.cookies.get('access_token_cookie')
        if not token and 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]  # "Bearer <TOKEN>"
        if not token:
            return jsonify({'message' : 'Token is missing !!'}), 401
        try:
            data = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=['HS256'])
            current_user: User = User.query\
                .filter_by(username = data['sub'])\
                .first()
            g.current_user = current_user
        except Exception as e:
            print(f"Error in token_required decorator: {e}")
            return jsonify({
                'message' : 'Token is invalid !!'
            }), 401
        return  f(*args, **kwargs)
    return decorated
