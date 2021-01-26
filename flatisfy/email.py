# coding: utf-8
"""
Email notifications.
"""

from __future__ import absolute_import, print_function, unicode_literals
from builtins import str

import logging
import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate, make_msgid

LOGGER = logging.getLogger(__name__)


def send_email(
    server, port, subject, _from, _to, txt, html, username=None, password=None
):
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
    if username or password:
        server.login(username or "", password or "")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = _from
    msg["To"] = ", ".join(_to)
    msg["Date"] = formatdate()
    msg["Message-ID"] = make_msgid()

    msg.attach(MIMEText(txt, "plain", "utf-8"))
    msg.attach(MIMEText(html, "html", "utf-8"))

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

    i18n = {
        "subject": [
            f"{len(flats)} new flats found!",
            f"{len(flats)} nouvelles annonces disponibles !",
        ],
        "hello": ["Hello dear user", "Bonjour cher utilisateur"],
        "following_new_flats": [
            "The following new flats have been found:",
            "Voici les nouvelles annonces :",
        ],
        "area": ["area", "surface"],
        "cost": ["cost", "coût"],
        "signature": ["Hope you'll find what you were looking for.", "Bonne recherche"],
    }
    l = 1 if config["notification_lang"] == "fr" else 0

    txt = i18n["hello"][l] + ",\n\n\n\n"
    html = f"""
    <html>
      <head></head>
      <body>
        <p>{i18n["hello"][l]}!</p>
        <p>{i18n["following_new_flats"][l]}

            <ul>
    """

    website_url = config["website_url"]

    for flat in flats:
        title = str(flat.title)
        flat_id = str(flat.id)
        area = str(flat.area)
        cost = str(flat.cost)
        currency = str(flat.currency)

        txt += "- {}: {}#/flat/{} ({}: {}, {}: {} {})\n".format(
            title,
            website_url,
            flat_id,
            i18n["area"][l],
            area,
            i18n["cost"][l],
            cost,
            currency,
        )

        html += """
            <li>
                <a href="{}#/flat/{}">{}</a>
                ({}: {}, {}: {} {})
            </li>
        """.format(
            website_url,
            flat_id,
            title,
            i18n["area"][l],
            area,
            i18n["cost"][l],
            cost,
            currency,
        )

    html += "</ul>"

    signature = f"\n{i18n['signature'][l]}\n\nBye!\nFlatisfy"
    txt += signature
    html += signature.replace("\n", "<br>")

    html += """</p>
      </body>
    </html>"""

    send_email(
        config["smtp_server"],
        config["smtp_port"],
        i18n["subject"][l],
        config["smtp_from"],
        config["smtp_to"],
        txt,
        html,
        config.get("smtp_username"),
        config.get("smtp_password"),
    )
