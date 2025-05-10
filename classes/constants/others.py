CONCTACTS_PER_PAGE = 10
MAX_SEARCHES = 1000

# First line of filters when the search results appear 
# For this version only works in Spanish

"""
    Example Structure is:

    touchable_filter_name: {
            input_filter | location_filter (names): placeholder_text
    }, ...
"""

LINKEDIN_DEFAULT_FILTERS = {
    "Personas" : {
        "Ubicaciones": "Añade una ubicación",
        "Empresa actual": "Añadir empresa"
    },
    "Publicaciones": {
        "N/A": "N/A"
    },
    "Empleos": {
        "N/A": "N/A"
    },
    "Productos": {
        "Categoría de productos": "Añadir categoría",
        "Empresa del producto": "Añadir empresa",
    },
    "Empresas": {
        "Ubicaciones": "Añade una ubicación",
        "Sector": "Añade un sector",
        "Tamaño de la empresa": "N/A" 
    },
    "Grupos": {
        "N/A": "N/A"
    },
    "Servicios": {
        "Categorías de servicios": "Añade un servicio",
        "Ubicaciones": "Añade una ubicación"
    },
    "Eventos": {
        "N/A": "N/A"
    }, 
    "Cursos": {
        "N/A": "N/A"
    }   
}

AUTHORIZED_SALES_MANAGERS = [
    "1060348488", # Alberto C Maestre
    "765901250", # Borja Mols
    "1054160630", # Marcel Buzainz
]

MAX_PAGES = 100

DAY_MAPPING = {
    "Domingo": 0,
    "Lunes": 1,
    "Martes": 2,
    "Miércoles": 3,
    "Jueves": 4,
    "Viernes": 5,
    "Sábado": 6
}

MONTH_MAPPING = {
    1: "Enero",
    2: "Febrero",
    3: "Marzo",
    4: "Abril",
    5: "Mayo",
    6: "Junio",
    7: "Julio",
    8: "Agosto",
    9: "Septiembre",
    10: "Octubre",
    11: "Noviembre",
    12: "Diciembre",
}

TASK_NAMES = {
    "check_accepted_invitations": "Verificar invitaciones aceptadas",
    "send_message_to": "Enviar mensaje",
    "deep_scrapp": "Ampliar información de perfiles",
    "massive_mailing": "Envío masivo de emails",
    "scrapp_linkedin_data": "Obtener datos de LinkedIn",
    "connect_with_members": "Enviar solicitudes de 'Conectar'",
    "process_data_with_GPT": "Procesar datos con ChatGPT",
    "check_unread_linkedin_messages": "Verificar nuevos mensajes recibidos",
    "accept_incoming_invitations": "Aceptar todas las invitaciones pendientes",
}