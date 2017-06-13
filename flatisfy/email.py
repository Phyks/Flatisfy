# coding: utf-8

"""
Email notifications.
"""

from __future__ import absolute_import, print_function, unicode_literals
import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def send_email(server, port, subject, _from, to, txt, html):
    if len(to) == 0:
        LOGGER.warn("No recipients for the email notifications, aborting.")
        return

    server = smtplib.SMTP(server, port)

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = _from
    msg['To'] = ', '.join(to)

    msg.attach(MIMEText(txt, 'plain', 'utf-8'))
    msg.attach(MIMEText(html, 'html', 'utf-8'))

    server.sendmail(_from, to, msg.as_string())
    server.quit()

def send_notification(config, flats):
    # Don't send an email if there are no new flats.
    if len(flats) == 0:
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

        txt += '- {}: {}#/flat/{} (area: {}, cost: {} {})\n' \
                .format(title, website_url, flat_id, area, cost, currency)

        html += """
            <li>
                <a href="{}#/flat/{}">{}</a>
                (area: {}, cost: {} {})
            </li>
        """.format(website_url, flat_id, title, area, cost, currency)

    html += "</ul>"

    SIGNATURE = u"\nHope you'll find what you were looking for.\n\nBye!\nFlatisfy"
    txt += SIGNATURE
    html += SIGNATURE.replace('\n', '<br>')

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
