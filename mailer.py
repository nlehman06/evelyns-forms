import os
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import boto3
from botocore.exceptions import ClientError

SENDER = "Nathan Lehman <nathan@nlehman.dev>"
AWS_REGION = "us-east-1"
CHARSET = "UTF-8"


def send_email(current_date, recipients, attachment_list, rm_list, tc_list, tantrum_graph, student_name):
    first_name = student_name.split()[0]
    subject = current_date + " " + first_name + "'s daily ABA therapy"
    body_text = "Forms for " + current_date + " for " + first_name + " are attached"
    body_html = f"""<html>
    <head></head>
    <body>
    <h1>{first_name}'s daily therapy</h1>
    <p>Forms for {current_date} for {first_name} are attached</p>
    """
    if rm_list:
        body_html += "<h2>" + first_name + " mastered something!</h2>"
        body_html += "<ul>"
        for rm in rm_list:
            body_html += "<li>" + rm + "</li>"
        body_html += "</ul>"
    if tc_list:
        body_html += "<h2>Some stuff " + first_name + " Worked on Today</h2>"
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
    msg['Subject'] = subject
    msg['From'] = SENDER
    msg['To'] = ', '.join(recipients)

    # Create a multipart/alternative child container.
    msg_body = MIMEMultipart('alternative')

    # Encode the text and HTML content and set the character encoding. This step is
    # necessary if you're sending a message with characters outside the ASCII range.
    text_part = MIMEText(body_text.encode(CHARSET), 'plain', CHARSET)
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

    if tantrum_graph:
        att_t = MIMEApplication(open(tantrum_graph, 'rb').read())
        att_t.add_header('Content-Disposition', 'attachment', filename='tantrum.png')
        os.remove(tantrum_graph)
        msg.attach(att_t)

    # Attach the multipart/alternative child container to the multipart/mixed
    # parent container.
    msg.attach(msg_body)

    try:
        response = client.send_raw_email(
            Source=SENDER,
            Destinations=recipients,
            RawMessage={
                'Data': msg.as_string(),
            },
        )
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        print("Email sent! Message ID:"),
        print(response['MessageId'])
