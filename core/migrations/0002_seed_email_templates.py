# Generated manually

from django.db import migrations


def seed_email_templates(apps, schema_editor):
    EmailTemplate = apps.get_model("core", "EmailTemplate")

    templates = [
        {
            "template_type": "CLIENT_INVOICE_ISSUED",
            "name": "Fatura Emitida (Cliente)",
            "subject": "Invoice for {{ prev_month_name }} {{ prev_month_year }} Services",
            "body": "Dear Payables Team,\n\nPlease find attached invoice for the services rendered during the month of {{ prev_month_name }} {{ prev_month_year }}.\nPayment instructions are included on the invoice.\n\nThank you,\nVitor",
            "language": "en",
        },
        {
            "template_type": "COMPANY_INVOICE_ISSUED",
            "name": "Fatura Emitida (Interno)",
            "subject": "Nova Fatura Emitida: {{ invoice_number }}",
            "body": "Uma nova fatura ({{ invoice_number }}) foi finalizada e emitida para {{ client_name }}.\n\nA fatura está em anexo.\nSe a NFS-e foi gerada, ela também está em anexo.",
            "language": "pt-br",
        },
        {
            "template_type": "COMPANY_CANCEL_FAILED",
            "name": "Falha no Cancelamento (Interno)",
            "subject": "ALERTA: Falha no Cancelamento da NFS-e - Fatura {{ invoice_number }}",
            "body": "O cancelamento da NFS-e para a fatura {{ invoice_number }} ({{ client_name }}) falhou após o número máximo de tentativas.\n\nErro: {{ error }}\n\nPor favor, acesse o sistema e verifique os logs.",
            "language": "pt-br",
        },
        {
            "template_type": "COMPANY_FAILSAFE_TRIGGERED",
            "name": "Failsafe Acionado (Interno)",
            "subject": "ALERTA: Failsafe bloqueou a emissão da NFS-e - Fatura {{ invoice_number }}",
            "body": "A fatura {{ invoice_number }} ({{ client_name }}) foi finalizada e enviada ao cliente com sucesso, porém a emissão automática da NFS-e foi cancelada pelo seguinte motivo:\n\n{{ failsafe_reason }}\n\nPor favor, acesse o sistema para emitir a NFS-e manualmente.",
            "language": "pt-br",
        },
        {
            "template_type": "COMPANY_NFSE_ISSUED",
            "name": "NFS-e Emitida (Interno)",
            "subject": "Nova NFS-e Emitida: {{ nf_number }}",
            "body": "Uma nova NFS-e ({{ nf_number }}) foi emitida para a fatura {{ invoice_number }} ({{ client_name }}).\n\nValor (BRL): R$ {{ amount_brl }}\nCódigo de Verificação: {{ verification_code }}\n\nA NFS-e está em anexo.",
            "language": "pt-br",
        },
        {
            "template_type": "COMPANY_NFSE_FAILED",
            "name": "Falha na Emissão da NFS-e (Interno)",
            "subject": "ALERTA: Falha na Emissão da NFS-e - Fatura {{ invoice_number }}",
            "body": "A emissão da NFS-e para a fatura {{ invoice_number }} ({{ client_name }}) falhou após o número máximo de tentativas.\n\nErro: {{ error }}\n\nPor favor, acesse o sistema e tente emitir a NFS-e manualmente novamente.",
            "language": "pt-br",
        },
    ]

    for data in templates:
        EmailTemplate.objects.get_or_create(
            template_type=data["template_type"],
            defaults={
                "name": data["name"],
                "subject": data["subject"],
                "body": data["body"],
                "language": data["language"],
            },
        )


def reverse_seed(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_email_templates, reverse_seed),
    ]
