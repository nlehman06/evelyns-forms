import ast
from ChromeBrowser import ChromeBrowser
from helpers import get_date
from mailer import send_email


def run_email(event, context):
    student = event['key'] if 'key' in event else 'Lehman, Hayes'
    case = event['case'] if 'case' in event else '0a608d99-9484-4333-a735-29179e1e1ef5'
    student_parsed = student.split(', ')
    student_name = student_parsed[1] + ' ' + student_parsed[0]
    print(student_name)
    recipients = [
        'nathan@nlehman.dev',
        'ancote@gmail.com'
    ]
    if 'queryStringParameters' in event and 'recipients' in event['queryStringParameters']:
        recipients = ast.literal_eval(event['queryStringParameters']['recipients'])
    datetime_object = get_date(event)
    current_date = '{d.month}/{d.day}/{d.year}'.format(d=datetime_object)

    cb = ChromeBrowser(datetime_object)

    cb.log_in()

    cb.select_student(case)

    tantrum_graph = cb.get_tantrum_graph(case)

    rm_list = cb.get_recently_mastered(student_name)

    tc_list = cb.get_trial_count(student_name)

    attachment_list = cb.get_attachments()

    if attachment_list:
        send_email(current_date, recipients, attachment_list, rm_list, tc_list, tantrum_graph, student_name)

    response = {
        "statusCode": 200
    }

    return response


if __name__ == "__main__":
    run_email('', '')
