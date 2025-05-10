from flask import Blueprint, jsonify, make_response, g, render_template, redirect
from flask import request
from flask_jwt_extended import create_access_token, create_refresh_token, set_refresh_cookies, set_access_cookies, get_jwt_identity, unset_jwt_cookies
from flask_bcrypt import check_password_hash, generate_password_hash
from datetime import timedelta
from functools import wraps

from models.models import User, db
from routes.decorators.auth_decorators import token_required
from config.config import Config
from http import HTTPStatus
from classes.email.sender import Sender
from classes.constants.email_templates import OTP_EMAIL
from flask_dance.contrib.linkedin import linkedin, make_linkedin_blueprint
from dotenv import load_dotenv
from datetime import datetime

import secrets
import os
import requests
import random


load_dotenv()

auth = Blueprint('auth', __name__)

REDIRECT_URI = "https://ilumek.es/api/login/linkedin/authorized"
CLIENT_ID = os.getenv("LINKEDIN_API_CLIENT_ID")
CLIENT_SECRET = os.getenv("LINKEDIN_API_SECRET_KEY")

if not CLIENT_ID or not CLIENT_SECRET or not REDIRECT_URI:
    raise ValueError("Las variables de entorno no están configuradas correctamente.")


def user_exists(user: User | None):
    """
        Implement with returned Query.first() to check is an user.
    """
    if isinstance(user, User):
        return True
    return False

def generate_otp():
    return secrets.randbelow(900000) + 100000

def generate_password(bytes: bytes):
    password = ""
    choices = {
        "mayus" : [chr(i) for i in range(65, 91)],
        "minus" : [chr(i) for i in range(97, 123)],
        "symbols" : ["@", "?", "¿", "_", "$", "#", "&", "!"],
        "numbers" : [str(i) for i in range (10)]
    }

    for _ in range (bytes):
        key = random.choice(list(choices.keys()))
        password += random.choice(choices[key])

    return password

def generate_username(fullname: str, separator: str):
    splitted_name = fullname.split(separator)
    first_letter = [name[0].lower() for name in splitted_name]
    year = datetime.now().year
    
    username = "".join(first_letter) + splitted_name[len(splitted_name) - 1][1:] + "_" + str(year)
    print(username)
    return username
    

@auth.route('/api/login', methods=['POST'])
def login():
    
    if request.method == 'POST':

        data = request.get_json()
        username = data.get('username', None)
        password = data.get('password', None)
        
        if username is None or len(username) == 0:
            return jsonify({
                'message': 'Username must be provided,'
            }), 401

        if password is None or len(password) == 0:
            return jsonify({
                'message': 'Password must be provided.'
            }), 401
        
        # Get user from db
        user = User.query.filter_by(email=username).first()
    
        if user_exists(user):
            
            is_user_checked = check_password_hash(user.password, password)
                
            if is_user_checked:
                access_token = create_access_token(identity=user.username, expires_delta=timedelta(hours=1))
                refresh_token = create_refresh_token(identity=user.username)

                response = make_response(jsonify(access_token=access_token, user=user.to_dict()))
                set_refresh_cookies(response, refresh_token)
                set_access_cookies(response, access_token, max_age=28800)

                if Config.ENVIRONMENT != "dev":
                    response.headers.add('Access-Control-Allow-Origin', 'https://ilumek.es')
                else:
                    response.headers.add('Access-Control-Allow-Origin', 'http://localhost:5173')
                
                response.headers.add('Access-Control-Allow-Credentials', 'true')
                return response, 200
            
            return jsonify({
                'message': 'Wrong username or password.'
            }), 401

        return jsonify({
            'message': "User doesn't exist."
        }), 401

    else:
        return jsonify({
            'message': 'Unsupported HTTP method.'
        }), 405

# No funciona falta implementar correctamente la funcionalidad
@auth.route('/api/refresh_token', methods=['POST'])
@token_required
def refresh():
    if request.method == "POST":
        data = request.get_json()
        username = data.get('username', None)

        user_id = get_jwt_identity()
        access_token = create_access_token(identity=user_id)
        response = jsonify({ 
            'message': 'Token refreshed successfully.',
            'access_token': access_token 
        })

        return response, 200

    return jsonify({
        'message': 'Unsupported HTTP method.'
    }), 405


@auth.route('/api/check_auth', methods=['GET'])
@token_required
def check_auth():
    user = g.current_user
    if not user:
        return jsonify({
            'message': 'Authenticationn failed.'
        }), 401
    
    response = make_response(jsonify({
        'message': 'Authentication was made successfully.',
        'user': user.to_dict(),
    }))

    if Config.ENVIRONMENT != "dev":
        response.headers.add('Access-Control-Allow-Origin', 'https://ilumek.es')
    else:
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:5173')
    response.headers.add('Access-Control-Allow-Credentials', 'true')

    return response, 200


@auth.route('/api/logout', methods=['POST'])
@token_required
def logout():
    if request.method == 'POST':
        response = jsonify({ 'message': "Logout successfull" })
        unset_jwt_cookies(response)
        return response, HTTPStatus.OK
    else:
        return jsonify({
            'message': 'Unsupported HTTP method.'
        }), HTTPStatus.METHOD_NOT_ALLOWED



# Este método no se ha implementado
@auth.route("/api/change-password", methods=['POST'])
@token_required
def change_password():
    notifier = Sender()
    user = g.current_user.to_dict()
    code = generate_otp()

    html = OTP_EMAIL.replace("[Token]", str(code))
    try:
        notifier.send_formatted_email(None, user.get("email"), "Cambiar contraseña", html)
        return jsonify({
            "message": "Código enviado correctamente."
        })
    except Exception as e:
        return jsonify({
            "message": "No se ha podido enviar el código OTP por email."
        }), HTTPStatus.BAD_REQUEST
    

# ===================================================
# =============== LINKEDIN AUTH =====================
# ===================================================

@auth.route("/api/login/linkedin")
def linkedin_login():
    state = secrets.token_hex(6)
    auth_url = (
        f"https://www.linkedin.com/oauth/v2/authorization?"
        f"response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&"
        f"scope=profile%20email%20openid&state={state}"
    )
    return jsonify({
        "auth_url": auth_url
    })


@auth.route("/api/login/linkedin/authorized")
def linkedin_callback():
    code = request.args.get("code")
    error = request.args.get("error")

    print(f"Code: {code}")
    print(f"Error: {error}")

    if error:
        return jsonify({"error": "LinkedIn OAuth error", "message": error}), 400
    
    token_url = "https://www.linkedin.com/oauth/v2/accessToken"
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": os.getenv('LINKEDIN_API_CLIENT_ID'),
        "client_secret": os.getenv('LINKEDIN_API_SECRET_KEY')
    }
    response = requests.post(token_url, data=data).json()
    access_token = response.get("access_token")
    
    # Obtener datos del usuario
    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        user_data = requests.get("https://api.linkedin.com/v2/userinfo", headers=headers).json()
        name = user_data.get("name", None)
        email = user_data.get("email", None)
        password = generate_password(16)
    except Exception as e:
        return jsonify({
            "error": e
        }), HTTPStatus.INTERNAL_SERVER_ERROR

    if user_data is not None:
        user = User.query.filter_by(email=user_data.get("email", None)).first()
        if not user_exists(user):
            user = User(
                username=generate_username(name, " "),
                email=email,
                password=generate_password_hash(password),
                is_superuser=False,
            )
            db.session.add(user)
            db.session.commit()
        
        # Loguear
        access_token = create_access_token(identity=user.username, expires_delta=timedelta(hours=8))
        refresh_token = create_refresh_token(identity=user.username)

        response_with_tokens = make_response(redirect("http://localhost:5173"))
        
        set_refresh_cookies(response_with_tokens, refresh_token, domain="localhost")
        set_access_cookies(response_with_tokens, access_token, max_age=28800, domain="localhost")

        if Config.ENVIRONMENT != "dev":
            response_with_tokens.headers.add('Access-Control-Allow-Origin', 'https://ilumek.es')
        else:
            response_with_tokens.headers.add('Access-Control-Allow-Origin', 'http://localhost:5173')
                
        response_with_tokens.headers.add('Access-Control-Allow-Credentials', 'true')
        return response_with_tokens, 200
    
    return jsonify({
        "error": "Los datos del usuario no han podido ser recuperados."
    }), HTTPStatus.INTERNAL_SERVER_ERROR