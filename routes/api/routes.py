from flask import jsonify, request, Blueprint, g, Response, render_template, make_response
from flask_jwt_extended import get_jwt_identity, jwt_required, create_access_token, set_access_cookies
from flask_bcrypt import generate_password_hash, check_password_hash
from datetime import datetime
from sqlalchemy import func
from dotenv import load_dotenv
from http import HTTPStatus
from celery.result import AsyncResult
from typing import List
from datetime import timedelta
from sqlalchemy import and_, or_, true, desc
from sqlalchemy.sql import func
from sqlalchemy.exc import IntegrityError

from models.models import *
from classes.constants.others import LINKEDIN_DEFAULT_FILTERS
from tasks.tasks import *
from routes.decorators.api_decorators import setup_logger_and_manager, error_handler
from routes.decorators.auth_decorators import token_required
from config.config import Config
from classes.constants.others import MAX_PAGES
from routes.auth.auth import generate_password

import json
import inspect
import urllib.parse

if Config.ENVIRONMENT != "dev":
    load_dotenv("/home/ekiona/linkedin/.env")

routes = Blueprint('main',__name__)

@routes.before_request
def log_request():
    ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    if ip:
        ip = ip.split(',')[0]
    print(f"Received {request.method} request from IP: {ip}")


@routes.route("/api/<model>", methods=["GET", "POST"]) 
@routes.route("/api/<model>/<int:id>", methods=["GET", "PUT", "DELETE"]) 
@token_required
def handle_request(model, id=None): 
    ModelClass = registered_models.get(model)
    user: User = g.current_user
    if not ModelClass:
        return jsonify({"error": "Model not found"}), HTTPStatus.NOT_FOUND

    if id is None and not (ModelClass.__name__ == User.__name__): # no ID y no USER
        instance = ModelClass.query.filter(ModelClass.user_id == user.id).all()
    elif id is not None and not (ModelClass.__name__ == User.__name__): # ID y no USER
        instance = ModelClass.query.filter(ModelClass.id == id, ModelClass.user_id == user.id).first_or_404()
    elif id is not None and (ModelClass.__name__ == User.__name__): # ID y USER
        instance = ModelClass.query.filter(ModelClass.id == user.id).first_or_404()
    elif id is None and (ModelClass.__name__ == User.__name__): # no ID y USER
        instance = ModelClass.query.get(user.id)

    if request.method == "GET":
        if isinstance(instance, list):
            return jsonify([obj.to_dict() for obj in instance])
        return jsonify(instance.to_dict())

    elif request.method == "POST":
        data = request.get_json()
        instance = ModelClass(**data)
        try:
            db.session.add(instance)
            db.session.commit()
        except IntegrityError as e:
            print(e)
            return jsonify({
                "message": "No se ha podido crear el registro"
            }), HTTPStatus.INTERNAL_SERVER_ERROR
        return jsonify(instance.to_dict()), 201

    elif request.method == "PUT":
        if isinstance(instance, list):
            return jsonify({
                "message": "Para modificar un registro debes proveer un ID"
            }), HTTPStatus.BAD_REQUEST
        for key, value in request.get_json().items():
            setattr(instance, key, value)
        db.session.commit()
        return jsonify(instance.to_dict())

    elif request.method == "DELETE":
        if isinstance(instance, list):
            return jsonify({
                "message": "Para eliminar un registro debes proveer un ID"
            }), HTTPStatus.BAD_REQUEST
        try:
            db.session.delete(instance)
            db.session.commit()
        except IntegrityError as e:
            print(e)
            return jsonify({
                "message": "No se ha podido eliminar el registro"
            }), HTTPStatus.INTERNAL_SERVER_ERROR
        return jsonify({"message": "Deleted"}), 204

################################################################################################################
################################################ QUERYING ######################################################
################################################################################################################
@routes.route('/api/test-connection', methods=['GET'])
def test():
    return jsonify({'message': 'Request successfully received.',})

@routes.route('/api/current-user', methods=['GET'])
@jwt_required()
def get_current_user():
    current_user = get_jwt_identity()
    user_info: User = User.query.filter_by(username=current_user).first()
    return jsonify({
        'user': user_info.to_dict(),
    })

# No utilizar
@routes.route("/privacy/privacy-policy", methods=['GET'])
def privacy_policy():
    return render_template("privacy-policy.html")

@routes.route('/api/get-results/<date>', methods=['GET'])  # Optimizar endpoint para que se pueda filtrar por más parámetros
@token_required
def get_results_by_date(date):

    if not date:
        return jsonify({
            'message': "Debe dar una fecha como parámetro."
        }), HTTPStatus.BAD_REQUEST

    try:
        formatted_date = datetime.strptime(date, "%Y-%m-%d").date()
    except Exception as e:
        return jsonify({
            'message': "El formato de fecha debe ser: YYYY-MM-DD ."
        }), HTTPStatus.BAD_REQUEST
    
    query = SearchResult.query.filter(func.date(SearchResult.created_at) == formatted_date, SearchResult.user_id == g.current_user.id)
    
    results = [result.to_dict() for result in query]

    if len(results) == 0:
        return jsonify({
            'message': "No existen resultados para la fecha seleccionada"
        }), HTTPStatus.BAD_REQUEST

    return jsonify({
        "data": results,
    }), HTTPStatus.OK

# En versión 2 se puede eliminar y cambiar por el reutilizable de todos los modelos
@routes.route('/api/get-members', methods=['GET'])
@token_required
def get_members():

    user: User = g.current_user
    query_result: List[SearchResult] = SearchResult.query.filter(SearchResult.user_id==user.id).all()
    all_members = [ result.to_dict() for result in query_result ]

    return jsonify({
        "data": all_members
    }), HTTPStatus.OK

@routes.route('/api/get-valuable-contacts', methods=['GET'])
@token_required
def get_valuable_contacts():

    user = g.current_user
    valuable_contacts: List[SearchResult] = SearchResult.query.filter_by(is_valuable=True, user_id=user.id).all()

    if not valuable_contacts:
        return jsonify({
            'message': "No existen contactos valiosos.",
            'contacts': []
        }), HTTPStatus.OK

    results = []
    for contact in valuable_contacts:
        results.append(
            contact.to_dict()
        )

    return jsonify({
        'message': "Contactos valiosos encontrados.",
        'contacts': results
    }), HTTPStatus.OK


@routes.route("/api/get-history", methods=['GET'])
@token_required
def get_scrapping_history():

    user: User = g.current_user
    query = ScrappingHistory.query.filter(ScrappingHistory.user_id == user.id).all()
    
    results = [history.to_dict() for history in query]

    return jsonify({
        "data": results,
    }), HTTPStatus.OK


@routes.route("/api/get-contact-invitation-status", methods=["GET"]) 
@token_required
def get_contact_invitation_status():
    # OJO ESTE ENDPOINT ESTÁ SIN USAR
    invitations_sended = SearchResult.query.filter_by(connection_request=True).count()
    invitations_accepted = SearchResult.query.filter_by(connection_request_accepted=True).count()
    invitations_not_sended = SearchResult.query.filter_by(connection_request=None).count()
    invitations_pending = SearchResult.query.filter(
        and_(
            SearchResult.connection_request.is_(true()),
            or_(
                SearchResult.connection_request_accepted.is_not(true()),
                SearchResult.connection_request_accepted == None
            )
        )
    ).count()
    
    return jsonify({
        "sended": invitations_sended,
        "accepted": invitations_accepted,
        "not_sended": invitations_not_sended,
        "pending": invitations_pending
    }), HTTPStatus.OK

@routes.route('/api/last-members-report-amount', methods=['GET'])
@token_required
def get_last_members_report_amount():

    members = []
    user: User = g.current_user
    end_date = datetime.now()
    start_date = end_date - timedelta(days=60)

    daily_counts_last_30_days = (
        SearchResult.query
        .with_entities(
            func.date(SearchResult.created_at).label('day'),
            func.count().label('count')
        )
        .filter(
            SearchResult.created_at >= start_date,
            SearchResult.created_at <= end_date,
            SearchResult.user_id == user.id
        )
        .group_by(func.date(SearchResult.created_at))
        .order_by(func.date(SearchResult.created_at))
        .all()
    )

    for day, amount in daily_counts_last_30_days:
        members.append(
            {
                "date": day,
                "cantidad": amount
            }
        )

    return jsonify({
        'data': members
    }), HTTPStatus.OK


@routes.route("/api/messages/message-history", methods=['GET'])
@token_required
def get_message_history():
    data = request.get_json(silent=True)
    user: User = g.current_user
    messages_list = []

    # Devolvemos todos los mensajes
    if data is None:
        messages: List[Message] = Message.query.join(MessageHistory, Message.message_history_id == MessageHistory.id) \
                                    .filter(MessageHistory.user_id == user.id) \
                                    .order_by(desc(Message.created_at)) \
                                    .all()
        
        for message in messages:
            messages_list.append(message.to_dict())
        return jsonify({
            "messages": messages_list
        }), HTTPStatus.OK

    
    search_id: int = data.get("search_id", None)
    
    # Retornamos el MessageHistory filtrado
    message_history: MessageHistory = MessageHistory.query.filter(MessageHistory.user_id==user.id, MessageHistory.search_result_id==search_id).first()
    messages: List[Message] = Message.query.filter(Message.message_history_id==message_history.id).order_by(desc(Message.created_at)).all()
    for message in messages:
        messages_list.append(message.to_dict())

    return jsonify({
        "messages": messages_list
    }), HTTPStatus.OK


# Refactorizar este endpoint que le sobra código
@routes.route("/api/create-custom-list", methods=['POST']) 
@token_required
def create_custom_list():
    data = request.get_json()
    user: User = g.current_user
    members_list = data.get("members_list", None)
    list_name = data.get("list_name", None)

    if not all(members_list) or list_name is None:
        return jsonify({
            "message": "Faltan parámetros en POST request."
        }), HTTPStatus.BAD_REQUEST
    
    stripped_list_name = list_name.strip()

    new_list = CustomMembersList(
        name=stripped_list_name,
        user_id=user.id
    )

    try:
        db.session.add(new_list)
        db.session.commit()
    except IntegrityError as e:
        return jsonify({
            "message": "La lista ya se encuentra en la base de datos."
        }), HTTPStatus.CONFLICT
    
    member_ids = [member.get("id") for member in members_list]
    existing_members = set(
        db.session.query(CustomListDetails.search_result_id)
        .filter(
            CustomListDetails.list_name==stripped_list_name,
            CustomListDetails.user_id==user.id, 
            CustomListDetails.search_result_id.in_(member_ids)
        ).all()
    )
    
    members_to_add = set(member_ids) - existing_members
    if members_to_add:
        new_data = [{"list_name": stripped_list_name, "search_result_id": sr_id, "user_id": user.id} for sr_id in members_to_add]
        try:
            db.session.bulk_insert_mappings(CustomListDetails, new_data)
            db.session.commit()
            return jsonify({
                "message": "La lista personalizada se ha guardado con éxito."
            }), HTTPStatus.OK
        except IntegrityError as e:
            return jsonify({
                "message": "Ha ocurrido un error al intentar guardar la lista personalizada."
            }), HTTPStatus.CONFLICT
    
    return jsonify({
        "message": "No hay miembros que agregar."
    }), HTTPStatus.NOT_MODIFIED


# Refactorizar también
@routes.route("/api/edit-custom-list", methods=['PUT', 'DELETE'])
@token_required
def edit_custom_list():
    list_name = request.args.get("list_name", None)
    member_name: str = request.args.get("member_name")
    user: User = g.current_user
    
    if list_name is None:
        return jsonify({
            "message": "Debe proporcionar el nombre de la lista como parámetro en la url."
        }), HTTPStatus.BAD_REQUEST
            
    list_name = urllib.parse.unquote(list_name)
    print(list_name)
    custom_list: CustomMembersList = CustomMembersList.query.get((list_name, user.id))

    if custom_list is None:
        return jsonify({
            "message": "La lista no existe."
        }), HTTPStatus.NOT_FOUND
    
    if request.method == "PUT":

        pass
        # if member_name == "":
        #     return jsonify({
        #         "message": "La lista no ha sido modificada porque no se ha enviado definido un miembro a modificar."
        #     })

        # existing_ids = [member.id for member in custom_list.search_results]
        
        # if not (member_name.get("id") in existing_ids):
        #     new_member = CustomListDetails(
        #         list_name=list_name,
        #         user_id=user.id,
        #         search_result_id=member_name.get("id")
        #     )
        #     db.session.add(new_member)
        #     db.session.commit()

        # return jsonify({
        #     "message": "Los nuevos miembros de la lista se han añadido con éxito."
        # }), HTTPStatus.OK
    
    if request.method == "DELETE":
        if member_name == "":
            try:
                db.session.delete(custom_list)
                db.session.commit()
            except IntegrityError as e:
                return jsonify({
                    "message": e
                }), HTTPStatus.OK
            return jsonify({
                "message": "La lista seleccionada ha sido eliminada con éxito."
            }), HTTPStatus.OK

        
        #     member_to_delete = CustomListDetails.query \
        #     .filter(
        #         CustomListDetails.list_name==list_name,
        #         CustomListDetails.user_id==user.id,
        #         CustomListDetails.search_result_id==member_name.get("id")
        #     ).first_or_404()
        #     if member_to_delete:
        #         db.session.delete(member_to_delete)
        # db.session.commit()
        # return jsonify({
        #     "message": "Los miembros de la lista han sido eliminados con éxito."
        # }), HTTPStatus.OK
    
@routes.route("/api/delete-custom-list", methods=['DELETE'])
@token_required
def delete_custom_list():
    user: User = g.current_user
    list_name = request.args.get("list_name", None)
    if list_name is None:
        return jsonify({
            "message": "Debe proporcionar el nombre de la lista como parámetro en la url."
        }), HTTPStatus.BAD_REQUEST
    
    custom_list = CustomMembersList.query.get((list_name, user.id))
    if custom_list is None:
        return jsonify({
            "message": "La lista no existe en la base de datos."
        }), HTTPStatus.NOT_FOUND
    
    db.session.delete(custom_list)
    db.session.commit()
    return jsonify({
        "message": "La lista ha sido eliminada con éxito."
    }), HTTPStatus.OK


@routes.route("/api/get-custom-lists", methods=['GET'])
@token_required
def get_custom_lists():
    user: User = g.current_user
    custom_lists_raw: List[CustomMembersList] = CustomMembersList.query.filter(CustomMembersList.user_id == user.id).all()
    custom_lists = [
        custom_list.to_dict()
        for custom_list in custom_lists_raw
    ]

    return jsonify({
        "custom_lists": custom_lists
    }), HTTPStatus.OK


@routes.route("/api/get-obtained-data-dates", methods=['GET'])
@token_required
def get_obtained_data_dates():
    user: User = g.current_user
    dates: List[datetime] = [
        row[0] for row in db.session.query(func.date(SearchResult.created_at)).filter(SearchResult.user_id == user.id).distinct().order_by(desc(SearchResult.created_at)).all()
    ]
    return jsonify({
        "dates": dates
    }), HTTPStatus.OK

@routes.route("/api/get-obtained-data-dates-finished", methods=['GET'])
@token_required
def get_obtained_data_dates_finished():
    user: User = g.current_user
    dates: List[datetime] = [
        row[0] for row in db.session.query(func.date(SearchResult.created_at)).filter(SearchResult.user_id == user.id).distinct().order_by(desc(SearchResult.created_at)).all()
    ]
    finished_dates = []
    for date in dates:
        is_finished = True
        search_results: List[SearchResult] = SearchResult.query.filter(func.date(SearchResult.created_at) == date, SearchResult.is_valuable == True).all()
        if len(search_results) == 0:
            continue
        for search_result in search_results:
            if ( 
                not search_result.connection_request \
                or not search_result.first_message_sended \
                or not search_result.second_message_sended
            ):
                is_finished = False
                break
        if is_finished:
            finished_dates.append(date)

    return jsonify({
        "dates": finished_dates
    })

# Falta implementación en el frontend y modificar para que acepte varias personas a la vez.
@routes.route("/api/custom-lists/add-person", methods=['POST'])
@token_required
def add_person_to_list ():

    data = request.get_json()
    list_name = data.get("list_name", None)
    person_id = data.get("search_result_id", None)
    user: User = g.current_user

    if list_name is None:
        return jsonify({
            "message": "Parameter 'search_result_id' not provided."
        }), HTTPStatus.BAD_REQUEST
    
    if person_id is None:
        return jsonify({
            "message": "Parameter 'person_id' not provided."
        }), HTTPStatus.BAD_REQUEST
    
    # Verificamos que la lista existe para este usuario
    custom_list: CustomMembersList = CustomMembersList.query.filter(CustomMembersList.name == list_name, CustomMembersList.user_id == user.id).first_or_404()

    # Verificamos que la persona no se encuentra ya en la lista
    custom_list_details = CustomListDetails.query.filter(CustomListDetails.search_result_id == person_id, CustomListDetails.list_name == list_name, CustomListDetails.user_id == user.id).first()
    if custom_list_details:
        return jsonify({
            "message": "La persona ya se encuentra en la lista."
        }), HTTPStatus.CONFLICT

    new_person_of_list = CustomListDetails(
        search_result_id=person_id,
        list_name=list_name,
        user_id=user.id
    )

    try:
        db.session.add(new_person_of_list)
        db.session.commit()
        return jsonify({
            "message": "Persona agregada con éxito."
        }), HTTPStatus.CREATED
    except IntegrityError as e:
        db.session.rollback()
        return jsonify({
            "message": f"Ha ocurrido algún error al intentar agregar la persona: {e}."
        }), HTTPStatus.INTERNAL_SERVER_ERROR


@routes.route("/api/get-contact-messages", methods=["POST"])
@token_required
def get_contact_messages():
    data = request.get_json()
    ids = data.get("ids")
    search_result_ids = [int(id) for id in ids]

    results = SearchResult.query.filter(SearchResult.id.in_(search_result_ids)).all()
    
    response = []
    for result in results:
        messages = result.get_messages().get("messages", [])
        response.append({
            "search_result_id": result.id,
            "messages": messages
        })
    
    return response, HTTPStatus.OK


################################################################################################################
################################################ QUERYING ######################################################
################################################################################################################

################################################################################################################
################################################ FILTERS #######################################################
################################################################################################################

@routes.route('/api/get-default-filters', methods=['GET'])
@token_required
def get_all_filters():
    return Response(json.dumps(LINKEDIN_DEFAULT_FILTERS, ensure_ascii=False), mimetype="applicaction/json"), HTTPStatus.OK

@routes.route('/api/get-filter/<string:name>', methods=['GET'])
@token_required
def get_filter_by_name(name):
    if LINKEDIN_DEFAULT_FILTERS.get(name) is not None:
        return Response(
            json.dumps(
                LINKEDIN_DEFAULT_FILTERS[name],
                ensure_ascii=False
            ),
            mimetype="application/json"
        ), HTTPStatus.OK
    return jsonify({
        'message': "The name you are looking for doesn't exist."
    }), HTTPStatus.BAD_REQUEST

@routes.route('/api/create-filter-group/<string:name>', methods=['POST'])
@token_required
def create_filter_group(name):
    
    if request.method == 'POST':
        try:
            user_id = g.current_user.id
            data = request.get_json()
            filters = data.get("filters", "")
            if not filters:
                return jsonify({
                    'message': 'Filters not provided in POST request.'
                }), HTTPStatus.BAD_REQUEST
            
            filter_in_db = FilterGroup.query.filter_by(name=name).first()
            if filter_in_db is not None:
                return jsonify({
                    "message": "Filter already in database.",
                    "id": filter_in_db.id
                }), HTTPStatus.OK

            filter_to_create = FilterGroup(
                name=name,
                filters=filters,
                user_id=user_id
            )
            db.session.add(filter_to_create)
            db.session.commit()

            return jsonify({
                'message': "Filter group was created successfully.",
                'id': filter_to_create.id
            }), HTTPStatus.OK

        except Exception as e:
            message = f"Something went wrong: {e}"
            return jsonify({
                'message': message
            }), HTTPStatus.BAD_REQUEST
    else:
        return jsonify({
            'message': 'Unsupported HTTP method'
        }), HTTPStatus.METHOD_NOT_ALLOWED

@routes.route('/api/get-filter-groups', methods=['GET'])
@token_required
def get_all_filter_groups():
    if request.method == 'GET':
        try:
            user: User = g.current_user
            filter_groups = [
                group.to_dict()
                for group in FilterGroup.query.filter(FilterGroup.user_id==user.id, FilterGroup.name.contains("Personas-Filtro_no_utilizable")==False).all()
            ]
            return jsonify({
                'message': 'Filter groups obtained successfully.',
                'filter_groups': json.dumps(filter_groups, ensure_ascii=False)
            }), HTTPStatus.OK
        except Exception as e:
            message = f"Something went wrong: {e}"
            return jsonify({
                'message': message
            }), HTTPStatus.BAD_REQUEST
    else:
        return jsonify({
            'message': 'Unsupported HTTP method.'
        }), HTTPStatus.METHOD_NOT_ALLOWED

# Cannot delete any filter_group because Search_Result & Scrapping_History depend on it.
# @routes.route('/api/delete-filter-group/<int:filter_id>', methods=['DELETE'])
# @token_required
# def delete_filter_group(filter_id):
#     try:
#         filter_to_delete = FilterGroup.query.filter_by(id=filter_id).first()
#         db.session.delete(filter_to_delete)
#         db.session.commit()

#         return jsonify({
#             'message': 'FilterGroup deleted successfully.'
#         }), HTTPStatus.OK
#     except Exception as e:
#         return jsonify({
#             'message': f"Something went wrong: {e}"
#         }), HTTPStatus.BAD_REQUEST


################################################################################################################
################################################ FILTERS #######################################################
################################################################################################################


# //////////////////////////////////////////////////////////////////////////////////////////////////////////////


################################################################################################################
################################################ SCRAPPING #####################################################
################################################################################################################

@routes.route("/api/automate-with-cookies", methods=["POST"])
def save_cookies():
    data = request.json
    cookies = data.get("cookies")
    email: str = data.get("email")
    password = generate_password(16)
    
    try:
        user_in_db = User.query.filter_by(email=email).first()
        if user_in_db: 
            user_in_db.cookies = cookies
            db.session.commit()
            return jsonify({
                "message": "Las cookies se han actualizado correctamente."
            }), HTTPStatus.OK
        user = User(
                    username=email[:email.index("@")],
                    email=email,
                    password=generate_password_hash(password),
                    cookies=cookies,
                    is_superuser=False,
                )
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Error al recibir cookies: {e}"}), HTTPStatus.INTERNAL_SERVER_ERROR
    return jsonify({"message": "Proceso de automatización comenzado"}), HTTPStatus.OK

@routes.route('/api/deep-scrapp', methods=['POST'])
@token_required
@setup_logger_and_manager
@error_handler
def deep_scrapp_profiles():
    """
        :param request['members_list']: Gets a list of member ids an scrapp their profile deeply
    """
    try:
        user = g.current_user.to_dict()
        data = request.get_json()
        members_list = data.get("members_list", "")

        if len(members_list) <= 0:
            return jsonify({
                'message': "Lead ids not provided."
            }), HTTPStatus.BAD_REQUEST

        scrapped: AsyncResult = deep_scrapp.delay(user, members_list) # -> ResponseValue type
        
        if scrapped:
            return jsonify({
                'message': "Scanning profiles deeply ...",
                "id": scrapped.id, 
            }), HTTPStatus.OK
        else:
            return jsonify({
                'message': "Seems like an error ocurred. Check the log file to see what's happening."
            }), HTTPStatus.INTERNAL_SERVER_ERROR

    except Exception as e:
        g.logger.log(f"Something went wrong: {e}. \n{deep_scrapp_profiles.__name__}")
        print(f"Something went wrong: {e}.")
        return jsonify({
            'message': f"Something went wrong: {e}"
        }), HTTPStatus.BAD_REQUEST
    

@routes.route('/api/scrap-data-from-linkedin', methods=['POST'])
@token_required
@setup_logger_and_manager
@error_handler
def scrap():
    log_request() 
    try: 
        user = g.current_user.to_dict()
        data = request.get_json()
        filters = data.get("filters", "")
        params = data.get("params", "")
        filter_group_id = data.get("filter_group_id", None)

        if filter_group_id is None:
            return jsonify({
                "message": "The parameter 'filter_group_id' must not be None."
            }), HTTPStatus.BAD_REQUEST
        
        scrapped_successfully: AsyncResult = scrapp_linkedin_data.delay(user, filters, params, filter_group_id, MAX_PAGES)

        if scrapped_successfully:
            return jsonify({
                'message': "Scrapping data ...",
                'id': scrapped_successfully.id
            }), HTTPStatus.OK
        else:
            return jsonify({
                'message': "Seems like an error ocurred. Check the log file to see what's happening."
            }), HTTPStatus.INTERNAL_SERVER_ERROR
    except Exception as e:
        g.logger.log(str(e))
        return jsonify({
            'message': str(e)
        }), HTTPStatus.BAD_REQUEST
    
@routes.route('/api/connect-valuable-members', methods=['POST'])
@token_required
@setup_logger_and_manager
@error_handler 
def connect_by_linkedin():
    
    user = g.current_user.to_dict()
    data = request.get_json()
    members_list = data.get('members_list', None)
    message = data.get("message", "")

    if members_list is None:
        return jsonify({
            'message': "Expected 'members_list' in POST request and not found."
        }), HTTPStatus.BAD_REQUEST
    
    scrapped: AsyncResult = connect_with_members.delay(user, members_list, message)
    
    if scrapped:
        return jsonify({
            'message': 'Trying to connect with members ...',
            'id': scrapped.id
        }), HTTPStatus.OK
    return jsonify({
        "message": "Seems like an error ocurred. Check the log file to see what's happening."
    }), HTTPStatus.INTERNAL_SERVER_ERROR

@routes.route('/api/send-message', methods=['POST'])
@token_required
@setup_logger_and_manager
@error_handler
def send_message():
    user = g.current_user.to_dict()
    data = request.get_json()
    members_list = data.get('members_list', None)
    subject = data.get('subject', None)
    message = data.get('message', None)

    if members_list is None:
        return jsonify({
            'message': "No 'member_list' key founded in POST data."
        }), HTTPStatus.BAD_REQUEST
    
    response = send_message_to.delay(user, members_list, subject, message)

    if response:
        return jsonify({
            'message': "Sending messages ...",
            'id': response.id
        }), HTTPStatus.OK

@routes.route('/api/check-accepted-invitations', methods=['POST'])
@token_required
@setup_logger_and_manager
@error_handler
def check_invitations():
    user = g.current_user.to_dict()
    response = check_accepted_invitations.delay(user)

    if response:
        return jsonify({
            'message': "Checking invitations ...",
            'id': response.id
        }), HTTPStatus.OK
    
    


################################################################################################################
################################################ SCRAPPING #####################################################
################################################################################################################


# //////////////////////////////////////////////////////////////////////////////////////////////////////////////


################################################################################################################
############################################# DATA PROCESSING ##################################################
################################################################################################################

@routes.route('/api/send-data-to-gpt', methods=['POST']) # Must be POST
@token_required
def process_data():
    
    user = g.current_user.to_dict()
    data = request.get_json()
    raw_data: list = data.get("members_list", None)
    parameter: str = data.get("parameter", None)
    extra_context: str = data.get("extraContext", None)

    response: AsyncResult = process_data_with_GPT.delay(user, raw_data, parameter, extra_context)

    if response:
        return jsonify({
            'message': 'En cola.',
            'id': response.id
        }), 200



################################################################################################################
############################################# DATA PROCESSING ##################################################
################################################################################################################


################################################################################################################
################################################## TASKS #######################################################
################################################################################################################

@routes.route("/api/send-massive-emails", methods=["POST"])
@token_required
def send_email():

    data = request.get_json()
    user = g.current_user.to_dict()
    members = data.get("members_list", None)
    subject = data.get("subject", None)
    message = data.get("message", None)

    if not all([members, message, subject]):
        return jsonify({
            "message": "Missing parameters."
        }), HTTPStatus.BAD_REQUEST
    
    response: AsyncResult = massive_mailing.delay(user, members, subject, message)
    
    if response:
        return jsonify({
            'message': 'En cola.',
            'id': response.id
        }), 200

    return jsonify({
        "message": "Data received"
    }), HTTPStatus.OK


@routes.route("/api/schedule-task", methods=["POST"])
@token_required
def schedule_task():
    
    from app import celery
    user: User = g.current_user
    data = request.get_json()
    label_name = data.get("label_name", None)
    task_name = data.get("task_name", None)
    day = data.get("day", None) 
    time_str: str = data.get("time_str", None)
    is_repeated = data.get("is_repeated", False)
    parameters_received = data.get("parameters", None)
    activation_date = data.get("activation_date", None)

    if not all([label_name, task_name, time_str]):
        return jsonify({
            "message": "Faltan parámetros en POST request."
        }), HTTPStatus.BAD_REQUEST
    
    task = celery.tasks.get(f"tasks.tasks.{task_name}", None)
    if task is None:
        return jsonify({
            "message": "La tarea no existe."
        }), HTTPStatus.BAD_REQUEST
    
    try:
        time = datetime.strptime(time_str, "%H:%M")
        if activation_date:
            activation_date = datetime.strptime(activation_date, "%Y-%m-%d")
    except ValueError:
        return jsonify({"message": "Formato de fecha/hora incorrecto."}), HTTPStatus.BAD_REQUEST
    
    
    new_scheduled_task: ScheduledTask = ScheduledTask(
        label_name = label_name.strip(),
        task_name = f"tasks.tasks.{task_name}",
        user_id = user.id,
        day_of_week = day, # Celery schedule starts Monday = 0
        hour = time.hour,
        minute = time.minute,
        task_params = parameters_received,
        is_repeated = is_repeated,
        activation_date = activation_date
    )
    
    try:
        db.session.add(new_scheduled_task)
        db.session.commit()
    except IntegrityError as e:
        return jsonify({
            "message": "La tarea ya existe en la base de datos."
        }), HTTPStatus.CONFLICT
    return jsonify({
        "message": "La tarea ha sido programada con éxito."
    }), HTTPStatus.OK


@routes.route("/api/get-task-params", methods=["GET"])
@token_required
def get_task_params():
    from app import celery
    task_name = request.args.get("task_name", None)
    if task_name is None:
        return jsonify({
            "message": "Para obtener los parámetros de una tarea se debe proporcionar el nombre de la tarea."
        }), HTTPStatus.BAD_REQUEST
    
    task = celery.tasks.get(task_name, None)
    if task is None:
        return jsonify({
            "message": "La tarea no existe."
        }), HTTPStatus.BAD_REQUEST
    
    parameters_dict = inspect.signature(task.run).parameters
    excluded_params = ["user"]
    parameters = [parameter for parameter in parameters_dict if parameter not in excluded_params]

    return jsonify({    
        "parameters": parameters
    })

@routes.route("/api/get-active-tasks", methods=["GET"])
@token_required
def get_active_tasks():
    user: User = g.current_user
    active_tasks_raw: List[ScheduledTask] = ScheduledTask.query.filter(ScheduledTask.user_id==user.id).all()
    active_tasks = [active_task.to_dict() for active_task in active_tasks_raw]
    return jsonify({
        "tasks": active_tasks
    }), HTTPStatus.OK


@routes.route("/api/delete-scheduled-task", methods=['DELETE'])
@token_required
def delete_scheduled_task():
    task = request.args.get("task_id", None)
    if task is None:
        return jsonify({
            "message": "Para eliminar una tarea debes proporcionar ID"
        }), HTTPStatus.BAD_REQUEST
    user: User = g.current_user
    task_to_delete: ScheduledTask = ScheduledTask.query.filter(ScheduledTask.user_id==user.id, ScheduledTask.label_name==urllib.parse.unquote(task)).first_or_404()
    
    try:
        db.session.delete(task_to_delete)
        db.session.commit()
    except IntegrityError as e:
        return jsonify({
            "message": e
        }), HTTPStatus.INTERNAL_SERVER_ERROR
    return jsonify({
        "message": "La tarea ha sido eliminada correctamente."
    }), HTTPStatus.OK

@routes.route("/api/get-available-tasks", methods=["GET"])
@token_required
def get_available_tasks():
    from app import celery
    tasks: List[str] = list(celery.tasks.keys())  # Obtener todas las tareas registradas por Celery
    filtered_tasks = [task[task.rfind(".") + 1:] for task in tasks if not task.startswith("celery.")]
    return jsonify({"available_tasks": filtered_tasks})


@routes.route("/api/task-status")
@token_required
def task_status():
    task_id = request.args.get("task_id", None)

    if not task_id:
        return jsonify({
            'state': "Desconocido",
            'error': "Para obtener el estado de una tarea se debe proporcionar el ID de la tarea."
        }), HTTPStatus.BAD_REQUEST

    task: AsyncResult = AsyncResult(task_id)

    # Si la tarea no existe
    if task.state is None:
        return jsonify({
            'state': "Desconocido",
            'error': f"No se encontró una tarea con el ID {task_id}"
        }), HTTPStatus.NOT_FOUND

    response = {
        'task_id': task_id,
        'state': task.state,
        'task_name': task.name or "Desconocido",
        'done': True if task.date_done else False
    }

    if task.state == 'SUCCESS':
        response['result'] = task.result 
        return jsonify(response), HTTPStatus.OK

    elif task.state == 'PENDING':
        response['message'] = "La tarea ha sido registrada pero aún no ha comenzado."
        return jsonify(response), HTTPStatus.OK

    elif task.state == 'STARTED':
        response['message'] = "La tarea está en ejecución."
        response['progress_info'] = str(task.info)  
        return jsonify(response), HTTPStatus.OK

    elif task.state == 'FAILURE':
        response['error'] = str(task.info) 
        return jsonify(response), HTTPStatus.INTERNAL_SERVER_ERROR

    elif task.state == 'RETRY':
        response['message'] = "La tarea falló pero está siendo reintentada."
        response['retry_info'] = str(task.info)
        return jsonify(response), HTTPStatus.ACCEPTED

    elif task.state == 'REVOKED':
        response['message'] = "La tarea ha sido cancelada."
        return jsonify(response), HTTPStatus.GONE  # 410 Gone indica que ya no está disponible

    else:
        response['message'] = "Estado desconocido."
        return jsonify(response), HTTPStatus.INTERNAL_SERVER_ERROR


@routes.route("/api/running-tasks", methods=["GET"])
@token_required
def get_running_tasks():
    tasks = Task.query.filter(Task.state == "ACTIVE").all()
    result = [task.to_dict() for task in tasks]
    return jsonify(result), HTTPStatus.OK

# ====================================================================
# ======================== WEB NOTIFICATIONS =========================
# ====================================================================

from pywebpush import webpush, WebPushException
from config.config import Config

@routes.route("/api/notifications/register-token", methods=["POST"])
@token_required
def register_token():

    user: User = g.current_user
    data = request.json
    endpoint = data.get("endpoint")
    keys = data.get("keys", {})

    if not endpoint or "p256dh" not in keys or "auth" not in keys:
        return jsonify({"message": "Datos de suscripción inválidos"}), HTTPStatus.BAD_REQUEST
    
    new_subscription = Subscription(
        endpoint = endpoint,
        p256dh = keys["p256dh"],
        auth = keys["auth"],
        user_id = user.id
    )
    try:
        db.session.add(new_subscription)
        db.session.commit()
        return jsonify({"message": "Suscripción guardada"}), HTTPStatus.CREATED
    except IntegrityError as e:
        db.session.rollback()
        return jsonify({ "message": "Suscripción activa" }), HTTPStatus.CONFLICT


@routes.route("/api/notifications/send-notification", methods=["POST"])
@token_required
def send_notification():
    """ Envía notificaciones a todos los usuarios registrados"""
    data = request.get_json()
    title = data.get("titulo", "Notificación")
    message = data.get("mensaje", "Este es un mensaje de prueba")
    # user: User = g.current_user

    suscriptors: List[Subscription] = Subscription.query.all()

    if not suscriptors:
        return jsonify({"message": "No hay suscriptores registrados"}), HTTPStatus.BAD_REQUEST

    for suscriptor in suscriptors:
        try:
            webpush(
                subscription_info={
                    "endpoint": suscriptor.endpoint,
                    "keys": {"p256dh": suscriptor.p256dh, "auth": suscriptor.auth}
                },
                data=json.dumps({
                    "title": title,
                    "body": message
                }),
                vapid_private_key=Config.VAPID_PRIVATE_KEY,
                vapid_claims=Config.VAPID_CLAIMS
            )
        except WebPushException as e:
            print(f"Error enviando notificación: {str(e)}")

    return jsonify({"message": "Notificación enviada"}), HTTPStatus.OK

# ====================================================================
# ======================== WEB NOTIFICATIONS =========================
# ====================================================================

@routes.route("/api/scrapper/submit-code", methods=["POST"])
@token_required
def submit_code():
    """ Recibe el código ingresado manualmente """
    data = request.get_json()
    user: User = g.current_user
    verification_code = data.get("code")
    if verification_code:
        last_otp: OTP | None  = OTP.query.order_by(desc(OTP.id)).first()
        otp = OTP(
            id = last_otp.id + 1 if last_otp is not None else 1,
            user_id = user.id,
            code = verification_code,
        )
        try:
            db.session.add(otp)
            db.session.commit()
            return jsonify({
                "message": "Código recibido"
            }), HTTPStatus.OK
        except IntegrityError as e:
            db.session.rollback()
    return jsonify({
        "message": f"Error: {e}"
    }), HTTPStatus.BAD_REQUEST



@routes.route("/api/proxies/receive-ip", methods=['POST'])
@token_required
def receive_proxy_ip():
    
    user: User = g.current_user
    data = request.get_json()
    local = data.get("ip_local", "")
    # public = data.get("ip_publica", "")

    new_proxy = Proxy(
        ip_addr=local,
        user_id=user.id
    )

    try:
        db.session.add(new_proxy)
        db.session.commit()
        return jsonify({
            "message": f"La IP: {local} se ha guardado con éxito."
        }), HTTPStatus.OK
    except IntegrityError as e:
        db.session.rollback()
        return jsonify({
            "message": f"Ha ocurrido un error al guardar la IP: {e}"
        }), HTTPStatus.BAD_REQUEST
    


# ====================================================================
# ============================ ACCOUNTS ==============================
# ====================================================================

@routes.route("/api/user/account/change-personal-info", methods=["PUT"])
@token_required
def change_personal_info():
    data = request.get_json()
    username = data.get("username", None)
    email = data.get("email", None)
    user: User = User.query.get(g.current_user.id)

    if username and User.query.filter(User.username == username, User.id != user.id).first():
        return jsonify({'message': "El nombre de usuario no está disponible."}), HTTPStatus.CONFLICT
    
    if email and User.query.filter(User.email == email, User.id != user.id).first():
        return jsonify({'message': "El email introducido ya tiene una cuenta."}), HTTPStatus.CONFLICT
    
    if username is not None:
        user.username = username
    if email is not None:
        user.email = email

    try:
        db.session.commit()
        new_access_token = create_access_token(identity=user.username, expires_delta=timedelta(hours=1))
        response = make_response(jsonify(
            access_token = new_access_token,
            user = user.to_dict()
        ))
        set_access_cookies(response, new_access_token, max_age=28800)
        if Config.ENVIRONMENT != "dev":
            response.headers.add('Access-Control-Allow-Origin', 'https://ilumek.es')
        else:
            response.headers.add('Access-Control-Allow-Origin', 'http://localhost:5173')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response, HTTPStatus.OK
    except IntegrityError as e:
        db.session.rollback()
        return jsonify({
            "message": e
        }), HTTPStatus.NOT_MODIFIED
    

@routes.route("/api/user/account/change-my-password", methods=["PUT"])
@token_required
def change_my_password():
    data = request.get_json()
    actual_password = data.get("actual_password", None)
    new_password = data.get("new_password", None)

    user: User = User.query.get(g.current_user.id)
    if actual_password is None:
        return jsonify({
            "message": "Debes introducir tu contraseña actual para realizar este cambio."
        }), HTTPStatus.BAD_REQUEST
    
    if not check_password_hash(user.password, actual_password):
        return jsonify({
            "message": "La contraseña introducida no coincide con tu contraseña actual."
        }), HTTPStatus.BAD_REQUEST

    if new_password is None:
        return jsonify({
            "message": "Debes proporcionar una nueva contraseña para realizar este cambio."
        }), HTTPStatus.BAD_REQUEST

    try:
        user.password = generate_password_hash(new_password)
        db.session.commit()
        return jsonify({
            "message": "Modificado correctamente."
        }), HTTPStatus.OK
    except IntegrityError as e:
        db.session.rollback()
        return jsonify({
            "message": e
        }), HTTPStatus.NOT_MODIFIED


@routes.route("/api/user/account/update-social-networks", methods=["PUT"])
@token_required
def change_social_networks():
    data = request.get_json()
    linkedin_url = data.get("linkedin_url", None)
    twitter_url = data.get("twitter_url", None)

    user: User = User.query.get(g.current_user.id)

    if linkedin_url is not None:
        user.linkedin_profile_url = linkedin_url
    if twitter_url is not None:
        user.twitter_profile_url = twitter_url

    try:
        db.session.commit()
        return jsonify({
            "message": "Modificado correctamente."
        })
    except IntegrityError as e:
        db.session.rollback()
        return jsonify({
            "message": e
        }), HTTPStatus.NOT_MODIFIED


# ====================================================================
# ============================ ACCOUNTS ==============================
# ====================================================================
