import datetime
import pickle
import os.path

from dateutil.parser import parse
from dateutil import tz

from googleapiclient.errors import HttpError
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

LONDON = tz.gettz('Europe/London')

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/calendar', 'https://www.googleapis.com/auth/calendar.events']

class CalendarQuotaError(Exception):
    def __init__(self):
        self.message = "You have reached the limits for creating calendars, wait a few hours and try again"
    
    def __str__(self):
        return self.message


def parse_ics_to_google(ics):
    try:
        calendar_name = ics.get("SUMMARY").to_ical().decode('utf-8')
    except AttributeError:
        calendar_name = None
    events = []
    for comp in ics.walk():
        if comp.name == 'VEVENT':
            event = {}
            for name, prop in comp.property_items():

                if name in ['SUMMARY', 'LOCATION']:
                    event[name.lower()] = prop.to_ical().decode('utf-8')

                elif name == 'DTSTART':
                    event['start'] = {
                        'dateTime': prop.dt.isoformat(),
                        'timeZone': "Europe/London"
                    }

                elif name == 'DTEND':
                    event['end'] = {
                        'dateTime': prop.dt.isoformat(),
                        'timeZone': "Europe/London"
                    }

                elif name == 'DESCRIPTION':
                    desc = prop.to_ics().decode('utf-8')
                    desc = desc.replace(u'\xa0', u' ')
                    if name.lower() in event:
                        event[name.lower()] = desc + '\r\n' + event[name.lower()]
                    else:
                        event[name.lower()] = desc

                else:
                    # print(name)
                    pass

            events.append(event)

    return calendar_name, events


class GoogleCalendarUploader:
    def __init__(self):
        creds = None
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        self.service = build('calendar', 'v3', credentials=creds)
        self.cal_list = None

    def upload_calendar_data(self, ics):
        upload = False
        batch = self.service.new_batch_http_request()
        cal_name, events = parse_ics_to_google(ics)
        cal_id = self.get_calendar_id(cal_name)
        if cal_id is None:
            body = {"summary": cal_name}
            try:
                created = self.service.calendars().insert(body=body).execute()
            except HttpError:
                raise CalendarQuotaError
            cal_id = created['id']
            self.access_permissions_service(cal_id).execute()
        events_response = self.service.events().list(calendarId=cal_id).execute()
        google_events = events_response['items']
        for event in events:
            for google_event in google_events:
                google_start = parse(google_event['start']['dateTime']).astimezone(LONDON)
                raw_start = parse(event['start']['dateTime']).replace(tzinfo=LONDON)
                if google_start == raw_start:
                    if google_event['summary'] != event['summary'] or google_event['location'] != event['location']:
                        upload = True
                        event_id = google_event['id']
                        batch.add(self.service.events().update(calendarId=cal_id, eventId=event_id, body=event))
                    break
            else:
                upload = True
                batch.add(self.service.events().insert(calendarId=cal_id, body=event))
        if upload:
            batch.execute()

    def access_permissions_service(self, cal_id):
        scope = {
            "type": "domain",
            "value": "laetottenham.ac.uk"
        }

        rule = {
            "scope": scope,
            "role": "owner"
        }

        return self.service.acl().insert(calendarId=cal_id, body=rule)

    def update_calendar_list(self):
        self.cal_list = self.service.calendarList().list().execute().get('items', [])
    
    def get_calendar_id(self, summary):
        self.update_calendar_list()
        for calendar in self.cal_list:
            if calendar.get('summary') == summary:
                return calendar.get('id')
