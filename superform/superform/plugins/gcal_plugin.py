from flask import session
from superform.models import db, User
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from datetime import datetime
import json
import time


FIELDS_UNAVAILABLE = ['Image']
PROJECT_ID = 'project_id'
CLIENT_ID = 'client_id'
CLIENT_SECRET = 'client_secret'
CONFIG_FIELDS = [PROJECT_ID, CLIENT_ID, CLIENT_SECRET]


def str_converter(datet):
    return datetime.strftime(datet,"%Y-%m-%d")

def creds_to_string(creds):
   return json.dumps({'token': creds.token,
            'refresh_token': creds._refresh_token,
            'token_uri': creds._token_uri,
            'client_id': creds._client_id,
            'client_secret': creds._client_secret,
            'scopes': creds._scopes})

def generate_user_credentials(channel_config):
    SCOPES = 'https://www.googleapis.com/auth/calendar'

    creds = get_user_credentials()
    if not creds:
       channel_config = get_full_config(json.loads(channel_config))
       flow = InstalledAppFlow.from_client_config(channel_config, scopes=[SCOPES])
       creds = flow.run_local_server(host='localhost', port=8080,
                   authorization_prompt_message='Please visit this URL: {url}',
                   success_message='The auth flow is complete, you may close this window.',
                   open_browser=True)
       set_user_credentials(creds)

def get_user_credentials():
   user = User.query.get(session["user_id"])
   return Credentials.from_authorized_user_info(json.loads(user.gcal_cred)) if user.gcal_cred else None

def set_user_credentials(creds):
   user = User.query.get(session["user_id"])
   user.gcal_cred = creds_to_string(creds)
   db.session.commit()

def get_full_config(channel_config):
   return {"installed":{"client_id":channel_config[CLIENT_ID],
                "project_id":channel_config[PROJECT_ID],
                "auth_uri":"https://accounts.google.com/o/oauth2/auth",
                "token_uri":"https://www.googleapis.com/oauth2/v3/token",
                "auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs",
                "client_secret":channel_config[CLIENT_SECRET],
                "redirect_uris":["urn:ietf:wg:oauth:2.0:oob","http://localhost"]}}

def date_format_converter(date, hour):
    return date+'T'+hour+':00Z'

def generate_event(publishing):
   return {
        'summary': publishing.title,
        'description': publishing.description,
        'attachments': [
            {
                "fileUrl": publishing.link_url,
            }
        ],
        'start': {
            'date': str_converter(publishing.date_from),
            'timeZone': 'Europe/Zurich',
        },
        'end': {
            'date': str_converter(publishing.date_until),
            'timeZone': 'Europe/Zurich',
        },
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'email', 'minutes': 24 * 60},
                {'method': 'popup', 'minutes': 10},
            ],
        },
    }

def run(publishing, channel_config):
    creds = get_user_credentials()
    service = build('calendar', 'v3', credentials=creds)
    event = generate_event(publishing)
    id = publish(event, service)

def publish(event, service):
    """
    Publie sur le compte et renvoie l'id de la publication
    """
    event = service.events().insert(calendarId='primary', body=event).execute()
    return event.get('htmlLink')

def delete(id):
    """
    Supprime la publication
    """

def is_valid(pub):
    """
      check if valid
    """
    now = datetime.datetime.now()
    if len(pub.title)==0:
        return False
    if pub.date_from < now :
        return False
    if pub.date_from > pub.date_until:
        return False
    else :
        return True
