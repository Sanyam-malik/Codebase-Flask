import logging
import smtplib
import ssl
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import database_utility
import appenv
import models
import utility

# Configure the logging settings
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)


def save_email_log(subject, body, recipient, date):
    connector = database_utility.create_connection()
    database_utility.insert_data(connector, "maillog", (subject, body, recipient, date))
    connector.close()


def fetch_template(folder_name, replace_vars=None):
    email = utility.read_text_from_file('templates' + "/" + folder_name + "/html_content.html")
    txt = utility.read_text_from_file('templates' + "/" + folder_name + "/plain_content.txt")
    if replace_vars is not None:
        for key, value in replace_vars.items():
            email = email.replace(key, value)
            txt = txt.replace(key, value)
    return {
        'html_content': email,
        'plain_content': txt
    }


def send_email(subject, body_text, body_html):
    # Fetch SMTP credentials from environment variables
    smtp_enable = appenv.environ['SMTP_ENABLE']
    smtp_server = appenv.environ['SMTP_ADDRESS']
    smtp_port = appenv.environ['SMTP_PORT']
    smtp_username = appenv.environ['SMTP_USERNAME']
    smtp_password = appenv.environ['SMTP_PASSWORD']
    recipient_email = appenv.environ['RECIPIENT_EMAIL']

    if not (smtp_server and smtp_port and smtp_username and smtp_password and smtp_enable):
        logging.info("SMTP environment variables not set.")
        return

    if smtp_enable == 'false':
        logging.info("Skipping Sending Mail......")
        return

    logging.info("Attempting to send mail......")
    try:
        context = ssl.create_default_context()
        # Create the email message
        message = MIMEMultipart("alternative")
        message['From'] = f'Codebase Bot <{smtp_username}>'
        message["To"] = recipient_email
        message["Subject"] = subject

        # Attach both plain text and HTML versions of the body
        message.attach(MIMEText(body_text, "plain"))
        message.attach(MIMEText(body_html, "html"))

        # Connect to the SMTP server
        server = smtplib.SMTP(smtp_server, port=int(smtp_port))

        server.starttls(context=context)

        # Log in to the SMTP server
        server.login(smtp_username, smtp_password)

        # Send the email
        server.sendmail(smtp_username, recipient_email, message.as_string())

        # Quit the SMTP server
        server.quit()

        save_email_log(subject, body_html, recipient_email, datetime.now().strftime('%Y-%m-%d'))
        logging.info("Email has been sent successfully")
    except Exception as e:
        logging.info("Exception occured... \n", e)


def check_if_email_send(subject, date):
    connector = database_utility.create_connection()
    result = database_utility.fetch_data(connector,
                                         "select Count(*) from maillog where subject like '%" + subject + "%' and Date(date) = '" + date + "'")
    result = result[0][0]
    if result > 0:
        return True
    else:
        return False
