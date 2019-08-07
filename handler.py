from ChromeBrowser import ChromeBrowser
from helpers import get_date
from mailer import send_email


def run_email(event, context):
    datetime_object = get_date(event)
    current_date = '{d.month}/{d.day}/{d.year}'.format(d=datetime_object)

    cb = ChromeBrowser(datetime_object)

    cb.log_in()

    tantrum_graph = cb.get_tantrum_graph()

    rm_list = cb.get_recently_mastered()

    tc_list = cb.get_trial_count()

    attachment_list = cb.get_attachments()

    if attachment_list:
        send_email(current_date, attachment_list, rm_list, tc_list, tantrum_graph)

    response = {
        "statusCode": 200
    }

    return response


if __name__ == "__main__":
    run_email('', '')
