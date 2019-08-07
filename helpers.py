import datetime
import re


def get_date(event):
    datetime_object = datetime.datetime.now()
    if 'time' in event:
        datetime_object = datetime.datetime.strptime(event['time'], "%Y-%m-%dT%H:%M:%S%z")
    return datetime_object


def create_filename(form_date, form_type, form_user):
    form_filename = form_date + '_' + form_type + '_' + form_user
    form_filename = re.sub(r"\W", "-", form_filename)
    form_filename = re.sub(r"\s+", '_', form_filename)
    form_filename = form_filename + '.pdf'
    return form_filename