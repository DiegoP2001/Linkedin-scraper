# Button showed first time in Linkedin
INITIAL_LOGIN_BUTTON_SELECTOR = ".nav__button-secondary"
    
# Form elements to login
USERNAME_SELECTOR = "#username"
PASSWORD_SELECTOR = "#password"
LOGIN_BUTTON = ".btn__primary--large"

# Search input once logged in
SEARCH_INPUT = ".search-global-typeahead__input"
# Filter container once the search is done
FILTER_CONTAINER = ".search-reusables__filter-list"
# All filters ( They can be getted with JS )
ALL_FILTERS = ".search-reusables__filter-pill-button"
# Search results
SEARCH_RESULTS = ".search-results-container"


# Search results parts
PROFILE_DIV = "search-entity-result-universal-template" # data-view-name
PROFILE_LINK = "[data-test-app-aware-link]" #".entity-result__universal-image > div > a" # get_attribute("href")
PROFILE_IMAGE = ".presence-entity__image" # get_attribute("src")
PROFILE_NAME = ".presence-entity__image" # get_attribute("alt")
PROFILE_ROLE = ".t-14.t-black.t-normal" #".entity-result__primary-subtitle" # text
LOCATION = ".mb1 > div:last-child"   #".entity-result__secondary-subtitle" # text
JOB_POSITION = ".entity-result__summary--2-lines" # text
SERVICES_CONTACTS = ".reusable-search-simple-insight__text" # text
SERVICES_PAGE = ".reusable-search-premium-custom-cta-insight > .app-aware-link" # get_attribute("href")

# Unavailable
TOO_MANY_REQUESTS_CONTAINER = ".search-no-results__container"


# Connect phases
CONNECT_FOLLOW_BTN = ".artdeco-button" # get_attribute("aria-label") can be "Connect" or "Follow"
CONNECT_FOLLOW_BTN_SPAN_TEXT = ".artdeco-button > .artdeco-button__text" # text
CONNECT_WITH_MESSAGE = "button[aria-label='Añadir una nota']"
CONNECT_WITHOUT_MESSAGE = "button[aria-label='Enviar sin nota']"
CONNECT_MESSAGE_AREA_TEXT = "#custom-message"
CONNECT_MESSAGE_AREA_SEND_BTN = "button[aria-label='Enviar invitación']" # check if enabled 


NEXT_PAGE_BTN = "button[aria-label='Siguiente']"
    
    
# Search locations form
FILTER_FORM = ".reusable-search-filters-trigger-dropdown__container" # fieldset
SEARCH_INPUT_FILTER = ".search-basic-typeahead > input" #input
FILTER_LIST = "search-reusables__collection-values-container" # ul
FILTER_LIST_ELEMENT = "search-reusables__collection-values-item" # li -> varios
BUTTON_SHOW_FILTER_RESULTS = "button[aria-label='Aplicar el filtro actual para mostrar resultados']"
BUTTON_ARIA_LABEL_ES = "Aplicar el filtro actual para mostrar resultados"
FILTER_HIDDEN_SELECT_LIST = ".basic-typeahead__triggered-content"
FILTER_SPAN_SUGGESTED_TEXT = ".search-typeahead-v2__hit-text"


# Specific member page tags
CONTACT_INFO_HREF = "#top-card-text-details-contact-info" # <a>Información de contacto</a>
INFO_CONTAINER_GENERAL = ".artdeco-container-card" # -> Section
INFO_CONTAINER = ".pv-contact-info__contact-type" # -> Sections dentro de INFO_CONTAINER_GENERAL
INFO_DESCRIPTION = ".pv-contact-info__header" # h3 -> Perfil | Teléfono | Enviar email | Conectado
PHONE_CONTAINER = ".list-style-none > .t-14"
PHONE = ".t-14.t-black.t-normal" # -> Puede tener varios ( Móvil | Fijo | Empresa )
EMAIL = ".link-without-visited-state"
DESCRIPTION = ".full-width.t-14.t-normal.t-black.display-flex.align-items-center > div > span" # Unused 


# Send message aside
ASIDE = "#msg-overlay"
ASIDE_MINIMIZED = "msg-overlay-list-bubble--is-minimized"
ASIDE_USE_BTNS_CONTAINER = ".msg-overlay-bubble-header__controls" # div { div | div | button }
ASIDE_OPEN_WRITE_PANEL_CONTAINER = ".entry-point" # usado solo dentro del aside > header.find_element(By.CLASS_NAME, ".entry-point")
ASIDE_SEARCH_PERSON_INPUT = ".msg-connections-typeahead__search-field" # input
ASIDE_RESULTS_LIST_CONTAINER = ".msg-connections-typeahead__result-list-container" # ul obtener 1er <li>
ASIDE_RESULTS_BTN = ".msg-connections-typeahead__search-result" # li
ASIDE_CONTENT_EDITABLE_TEXT_AREA_MESSAGE = ".msg-form__contenteditable > p" # no es un textarea (div content-editable y se escribe en p)
ASIDE_SEND_MESSAGE_BTN = ".msg-form__send-button"
ASIDE_NOT_FOUND_CONTACT = ".artdeco-inline-feedback__message"
ASIDE_MODAL_EXIT_WITHOUT_SAVE_BTN = ".artdeco-modal__confirm-dialog-btn"

ASIDE_MESSAGE_WINDOW = ".msg-convo-wrapper" # Para obtener los buttons obtengo el header y luego todos los buttons

ASIDE_UNREAD_MESSAGES_CONTAINER = ".msg-overlay-list-bubble__convo-card-container--v2-unread"
ASIDE_UNREAD_MESSAGE_SENDER = "span.truncate" # for every message_container
ASIDE_NOTIFICATION_CONTAINER = ".notification-badge" # for every message_container
ASIDE_NOTIFICATION_COUNT = ".notification-badge__count" # for every message_container
ASIDE_LAST_SENDER_MESSAGE = "p.msg-overlay-list-bubble__message-snippet--v2" # for every message_container .text



# ADVANCED FILTERS
ALL_FILTERS_LIST = ".search-reusables__secondary-filters-filter" # -> li
ALL_FILTERS_TITLE = "h3" # by tag name
ALL_FILTERS_LIST_VALUE_ITEMS = ".search-reusables__filter-value-item" # li containing (input, label)
ALL_FILTERS_ADD_OPTION_BUTTON = "button[data-add-filter-button]"
ALL_FILTERS_DROPDOWN_SUGGESTION_ELEMENTS = ".search-typeahead-v2__hit-text.t-14.t-black.t-bold"
ALL_FILTERS_APPLY_BUTTON = "button[data-test-reusables-filters-modal-show-results-button]"


# READ MESSAGES
MY_MESSAGES="a[href*='messaging']" # a
PERSON_NAME="thread-detail-jump-target"
UNREAD_BUTTON="button[data-test-messaging-inbox-filters__filter-pill='UNREAD']" # button
CONVERSATIONS_UL=".msg-conversations-container__conversations-list" # ul
CONVERSATIONS_LI=".msg-conversations-container__convo-item" # li
MESSAGES=".msg-s-message-list__event" # seleccionar solo el último
MESSAGES_P=".msg-s-event-listitem__body" # p
MESSAGE_FROM=".msg-s-message-group__meta > span"
LINK_TO_PROFILE=".msg-thread__link-to-profile" # a


# SEND MESSAGES 
SEND_MESSAGE_PROFILE = "button[aria-label*='Enviar mensaje a']"
HEADER = ".msg-overlay-conversation-bubble-header"
SUBJECT = "input[placeholder='Asunto (opcional)']"
MESSAGE = "div[aria-label*='Escribe un mensaje'] > p" # pulsar ENTER para enviar
INMAIL_BANNER = ".msg-inmail-credits-display"
SEND_MESSAGE_BTN = ".msg-form__send-button"
ALL_HEADER_BUTTON_CONTAINER = ".msg-overlay-bubble-header__controls"
MESSAGE_HEADER_BUTTONS = ".msg-overlay-bubble-header__control"
MESSAGE_CONTAINER = "[data-msg-overlay-conversation-bubble-open]"

# CONTACT STATUS SE ENCUENTRA ENCIMA DE EL HILO DE MENSAJES
PENDING_CONNECTION_REQUEST = ".msg-nonconnection-banner__pending"


# INVITATIONS
MY_NETWORK="a[href*='mynetwork']"
ALL_CONTACTS="a[href*='invite-connect']" # [0].click()
CONTACT_NAME=".mn-connection-card__name"
CONTACT_PROFILE_LINK=".ember-view.mn-connection-card__picture"
SHOW_MORE_BUTTON=".scaffold-finite-scroll__load-button"

# ACCEPTING INVITATIONS
INVITATIONS_TO_ACCEPT_LIST="div[data-view-name='pending-invitation']"
ACCEPT_INVITATION_RECEIVED_BTN="button[aria-label*='Aceptar']"


# DEEP_SCRAPP_INVITATIONS ESTO SE ENCUENTRA EN EL PERFIL DE CADA UNO PERO LO USO AL ACEPTAR INVITACIONES
INVITATION_ID="section[data-member-id]"
INVITATION_PROFILE_IMAGE=".pv-top-card-profile-picture__image--show"
INVITATION_JOB_POSITION="div[data-view-name='profile-component-entity']" # -> 0
INVITATION_LOCATION="span.text-body-small.inline.t-black--light.break-words"
INVITATION_ROLE_AND_DESCRIPTION="[data-generated-suggestion-target]" # [0] -> Role [1] -> Description

NOTIFICATIONS_CONTAINER = ".mn-summary-card-notification"
SEE_ALL_INVITATIONS_BUTTON = "button[aria-label='Ver todas las invitaciones aceptadas']"
ACCEPTED_INVITATIONS_UL=".artdeco-list.ph5" # ul
ACCEPTED_INVITATIONS_LIST=".artdeco-list__item.pv3.ph0" # li
INVITATION_PERSON_NAME=".mn-invitation-notifications-modal__headline > strong"


