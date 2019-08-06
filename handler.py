import os
import sys
import http.cookiejar as cookielib
import re
import datetime
import boto3
from botocore.exceptions import ClientError
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

here = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(here, "./vendored"))

import mechanize
from bs4 import BeautifulSoup

now = datetime.datetime.now()
# CURRENT_DATE = '8/2/2019'
# CURRENT_DATE_PADDED = '08/02/2019'
CURRENT_DATE = '{d.month}/{d.day}/{d.year}'.format(d=now)
CURRENT_DATE_PADDED = '{d.month:02}/{d.day:02}/{d.year}'.format(d=now)

USERNAME = os.environ['CATALYST_USERNAME']
PASSWORD = os.environ['CATALYST_PASSWORD']

SENDER = "Nathan Lehman <nathan@nlehman.dev>"
RECIPIENTS = ["nathan@nlehman.dev", "ancote@gmail.com"]
SUBJECT = CURRENT_DATE + " Evelyn's daily ABA therapy"
BODY_TEXT = "Forms for " + CURRENT_DATE + " for Evelyn are attached"
AWS_REGION = "us-east-1"
CHARSET = "UTF-8"


def hello(event, context):
    cj = cookielib.LWPCookieJar()
    br = mechanize.Browser()
    br.set_cookiejar(cj)

    # Browser options
    br.set_handle_equiv(True)
    br.set_handle_gzip(True)
    br.set_handle_redirect(True)
    br.set_handle_referer(True)
    br.set_handle_robots(False)
    br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)

    br.addheaders = [('User-agent',
                      'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36')]

    br.open("https://datafinch.com/")

    br.follow_link(text="Catalyst Login")

    # for f in br.forms():
    #     print(f)

    br.select_form(nr=0)
    br.form['Username'] = USERNAME
    br.form['Password'] = PASSWORD
    br.submit()

    # print(br.response().read())
    br.select_form(nr=0)
    # print(br.form)
    br.submit()

    rm_list = []
    recently_mastered_response = br.open_novisit(url_or_request='https://secure.datafinch.com/Widget/RecentlyMasteredTargets?_=Evelyn%20Lehman')
    recently_mastered_soup = BeautifulSoup(recently_mastered_response.read(), 'html.parser')
    rm_tr_list = recently_mastered_soup.find_all('tr')
    for row in rm_tr_list:
        rm_td_list = row.find_all('td')
        if rm_td_list:
            rm_target = rm_td_list[0].text.strip()
            rm_date = rm_td_list[2].text.strip()
            if rm_date == CURRENT_DATE_PADDED:
                rm_list.append(rm_target)

    tc_list = []
    trial_count_response = br.open_novisit(url_or_request='https://secure.datafinch.com/Widget/TrialCounts?_=Evelyn%20Lehman')
    trial_count_soup = BeautifulSoup(trial_count_response.read(), 'html.parser')
    tc_tr_list = trial_count_soup.find_all('tr')
    for row in tc_tr_list[:6]:
        tc_td_list = row.find_all('td')
        if tc_td_list:
            tc_target = tc_td_list[0].text.strip()
            tc_list.append(tc_target)

    br.follow_link(text="Assessments")
    br.follow_link(text="Form Responses")

    # print(br.response().read())
    soup = BeautifulSoup(br.response().read(), 'html.parser')

    tbody = soup.find("tbody")
    tr_list = tbody.find_all('tr')
    attachment_list = []
    for i, tr in enumerate(tr_list):
        td_list = tr.find_all('td')
        form_date = td_list[0].text
        form_type = td_list[1].text
        form_user = td_list[2].text
        row_date = re.findall(r"^[0-9/]+", form_date)
        if row_date[0] == CURRENT_DATE:
            links = tr.find_all('a')
            br_link = br.find_link(url=links[1]['href'])
            (filename, headers) = br.retrieve(
                br_link.absolute_url
            )
            attachment_list.append(
                {
                    'tmp_name': filename,
                    'friendly_name': create_filename(form_date, form_type, form_user)
                })
            # os.remove(filename)

    if attachment_list:
        send_email(attachment_list, rm_list, tc_list)

    response = {
        "statusCode": 200
    }

    return response


def send_email(attachment_list, rm_list, tc_list):
    body_html = f"""<html>
    <head></head>
    <body>
    <h1>Evelyn's daily therapy</h1>
    <p>Forms for {CURRENT_DATE} for Evelyn are attached</p>
    """
    if rm_list:
        body_html += "<h2>Evelyn mastered something!</h2>"
        body_html += "<ul>"
        for rm in rm_list:
            body_html += "<li>" + rm + "</li>"
        body_html += "</ul>"
    if tc_list:
        body_html += "<h2>Some stuff Evelyn Worked on Today</h2>"
        body_html += "<ul>"
        for tc in tc_list:
            body_html += "<li>" + tc + "</li>"
        body_html += "</ul>"
    body_html += """
    </body>
    </html>
    """
    client = boto3.client('ses', region_name=AWS_REGION)

    # Create a multipart/mixed parent container.
    msg = MIMEMultipart('mixed')
    # Add subject, from and to lines.
    msg['Subject'] = SUBJECT
    msg['From'] = SENDER
    msg['To'] = ', '.join(RECIPIENTS)

    # Create a multipart/alternative child container.
    msg_body = MIMEMultipart('alternative')

    # Encode the text and HTML content and set the character encoding. This step is
    # necessary if you're sending a message with characters outside the ASCII range.
    text_part = MIMEText(BODY_TEXT.encode(CHARSET), 'plain', CHARSET)
    html_part = MIMEText(body_html.encode(CHARSET), 'html', CHARSET)

    # Add the text and HTML parts to the child container.
    msg_body.attach(text_part)
    msg_body.attach(html_part)

    for attachment in attachment_list:
        # Define the attachment part and encode it using MIMEApplication.
        att = MIMEApplication(open(attachment['tmp_name'], 'rb').read())

        # Add a header to tell the email client to treat this part as an attachment,
        # and to give the attachment a name.
        att.add_header('Content-Disposition', 'attachment', filename=attachment['friendly_name'])
        os.remove(attachment['tmp_name'])
        # Add the attachment to the parent container.
        msg.attach(att)

    # Attach the multipart/alternative child container to the multipart/mixed
    # parent container.
    msg.attach(msg_body)

    try:
        response = client.send_raw_email(
            Source=SENDER,
            Destinations=RECIPIENTS,
            RawMessage={
                'Data': msg.as_string(),
            },
        )
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        print("Email sent! Message ID:"),
        print(response['MessageId'])


def create_filename(form_date, form_type, form_user):
    form_filename = form_date + '_' + form_type + '_' + form_user
    form_filename = re.sub(r"\W", "-", form_filename)
    form_filename = re.sub(r"\s+", '_', form_filename)
    form_filename = form_filename + '.pdf'
    return form_filename


if __name__ == "__main__":
    hello('', '')
