from flask import Blueprint, jsonify, g
from flask import request
from flask_bcrypt import generate_password_hash
from routes.auth.auth import token_required
from models.models import User, FilterGroup, db
from sqlalchemy import or_
from http import HTTPStatus
from sqlalchemy.exc import IntegrityError
from typing import List

admin_dashboard = Blueprint('admin_dashboard', __name__)

def is_user_registered(username: str, email: str):

    user = User.query.filter(or_(User.username==username, User.email==email)).first()
    if user is None:
        return False
    return True

@admin_dashboard.route('/api/admin/create-user', methods=['POST'])
@token_required
def create_user():

    data = request.get_json()    
    username_data = data.get('username', None)
    password_data = data.get('password', None)
    email = data.get('email', None)
    is_superuser = data.get('is_superuser', False)
    linkedin_pass = data.get("linkedin_password", None)
    linkedin_user = data.get("linkedin_username", None)
    user: User = g.current_user

    if not user.is_superuser:
        return jsonify({
            "message": "You are not authorized to access this feature."
        }), HTTPStatus.UNAUTHORIZED
    
    if not all([username_data, password_data, email, linkedin_pass, linkedin_user]):
        return jsonify({
            'message': "Missing parameters in POST request."
        }), HTTPStatus.BAD_REQUEST

    hashed_password = generate_password_hash(password_data)

    is_email_already_in_db: User | None = User.query.filter_by(email=email).first()
    if is_email_already_in_db:
        return jsonify({
            'message': "El email que ha introducido ya tiene una cuenta."
        }), HTTPStatus.BAD_REQUEST

    try:
        user = User(
            username=username_data,
            password=hashed_password,
            email=email,
            is_superuser=is_superuser,
            linkedin_username=linkedin_user,
        )
        user.set_linkedin_password(linkedin_pass)
        db.session.add(user)
        db.session.commit()
        filter_group = FilterGroup(
            name=f"Personas-Filtro_no_utilizable_{user.id}",
            filters=[],
            user_id=user.id,
        )
        
        db.session.add(filter_group)
        db.session.commit()
        return jsonify({
            'message': 'Usuario registrado con éxito.'
        }), HTTPStatus.CREATED
    except Exception as e:
        return jsonify({
            'message': f"Ha ocurrido un error: {e}"
        }), HTTPStatus.BAD_REQUEST

@admin_dashboard.route("/api/admin/edit-user", methods=['PUT'])
@token_required
def edit_user():

    data = request.get_json()
    id = data.get("id", None)
    new_username = data.get('username', None)
    new_email = data.get('email', None)
    is_superuser = data.get('is_superuser', None)
    linkedin_username = data.get('linkedin_username', None)
    linkedin_password = data.get('linkedin_password', None)
    
    user_requester: User = g.current_user

    if not user_requester.is_superuser:
        return jsonify({
            "message": "You are not authorized to access this feature."
        }), HTTPStatus.UNAUTHORIZED

    user = None
    if id:
        user: User | None = User.query.get(id)
    if user is None:
        return jsonify({
            'message': "El usuario no existe."
        }), HTTPStatus.BAD_REQUEST
    
    if new_username and User.query.filter(User.username == new_username, User.id != user.id).first():
        return jsonify({'message': "El nombre de usuario no está disponible."}), HTTPStatus.CONFLICT

    if new_email and User.query.filter(User.email == new_email, User.id != user.id).first():
        return jsonify({'message': "El email introducido ya tiene una cuenta."}), HTTPStatus.CONFLICT
    
    if new_username is not None:
        user.username = new_username
    if new_email is not None:
        user.email = new_email
    if is_superuser is not None:
        user.is_superuser = is_superuser
    if linkedin_username is not None:
        user.linkedin_username = linkedin_username
    if linkedin_password not in (None, ""):
        user.set_linkedin_password(linkedin_password)

    try:
        db.session.commit()
        return jsonify({'message': "Usuario editado con éxito."}), HTTPStatus.OK
    except IntegrityError:
        db.session.rollback()
        return jsonify({'message': "Error en la base de datos. No se ha podido editar el usuario."}), HTTPStatus.INTERNAL_SERVER_ERROR


@admin_dashboard.route("/api/admin/get-users", methods=["GET"])
@token_required
def get_users():
    user = g.current_user
    if not user.is_superuser:
        return jsonify({
            "message": "You are not authorized to see this information."
        }), HTTPStatus.UNAUTHORIZED
    
    users: List[dict] = [user.to_dict() for user in User.query.all()]
    return jsonify({
        "users": users
    }), HTTPStatus.OK
