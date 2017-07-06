# coding: utf-8
"""
Email notifications.
"""

from __future__ import absolute_import, print_function, unicode_literals

import logging
import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate, make_msgid

LOGGER = logging.getLogger(__name__)


def send_email(server, port, subject, _from, _to, txt, html):
    """
    Send an email

    :param server: SMTP server to use.
    :param port: SMTP port to use.
    :param subject: Subject of the email to send.
    :param _from: Email address of the sender.
    :param _to: List of email addresses of the receivers.
    :param txt: Text version of the message.
    :param html: HTML version of the message.
    """
    if not _to:
        LOGGER.warn("No recipients for the email notifications, aborting.")
        return

    server = smtplib.SMTP(server, port)

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = _from
    msg['To'] = ', '.join(_to)
    msg['Date'] = formatdate()
    msg['Message-ID'] = make_msgid()

    msg.attach(MIMEText(txt, 'plain', 'utf-8'))
    msg.attach(MIMEText(html, 'html', 'utf-8'))

    server.sendmail(_from, _to, msg.as_string())
    server.quit()


def send_notification(config, flats):
    """
    Send an email notification about new available flats.

    :param config: A config dict.
    :param flats: List of flats to include in the notification.
    """
    # Don't send an email if there are no new flats.
    if not flats:
        return

    txt = u'Hello dear user,\n\nThe following new flats have been found:\n\n'
    html = """
    <html>
      <head></head>
      <body>
        <p>Hello dear user!</p>
        <p>The following new flats have been found:

            <ul>
    """

    website_url = config["website_url"]

    for flat in flats:
        title = unicode(flat.title)
        flat_id = unicode(flat.id)
        area = unicode(flat.area)
        cost = unicode(flat.cost)
        currency = unicode(flat.currency)

        txt += (
            '- {}: {}#/flat/{} (area: {}, cost: {} {})\n'.format(
                title, website_url, flat_id, area, cost, currency
            )
        )

        html += """
            <li>
                <a href="{}#/flat/{}">{}</a>
                (area: {}, cost: {} {})
            </li>
        """.format(website_url, flat_id, title, area, cost, currency)

    html += "</ul>"

    signature = (
        u"\nHope you'll find what you were looking for.\n\nBye!\nFlatisfy"
    )
    txt += signature
    html += signature.replace('\n', '<br>')

    html += """</p>
      </body>
    </html>"""

    send_email(config["smtp_server"],
               config["smtp_port"],
               "New flats found!",
               config["smtp_from"],
               config["smtp_to"],
               txt,
               html)
