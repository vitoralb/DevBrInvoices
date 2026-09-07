import logging
from django.core.mail import EmailMessage

logger = logging.getLogger(__name__)


def send_email_with_debug(
    subject, body, to_emails, cc_emails, from_email, attachments, company
):
    """Send an email with debug routing support if debug_mode is active on company."""
    final_to = list(to_emails)
    final_cc = list(cc_emails) if cc_emails else []

    if company and company.debug_mode and company.debug_email:
        debug_info = (
            f"\n\n--- DEBUG INFO ---\n"
            f"Original To: {', '.join(to_emails)}\n"
            f"Original CC: {', '.join(cc_emails) if cc_emails else 'None'}\n"
            f"------------------\n"
        )
        body = debug_info + body
        final_to = [company.debug_email]
        final_cc = []

    email_msg = EmailMessage(
        subject=subject,
        body=body,
        from_email=from_email,
        to=final_to,
        cc=final_cc,
        headers={"Sender": from_email},
    )
    for filename, pdf_bytes, mime in attachments:
        email_msg.attach(filename, pdf_bytes, mime)

    logger.info("Sending email: '%s' to %s (CC: %s)", subject, final_to, final_cc)
    email_msg.send()
