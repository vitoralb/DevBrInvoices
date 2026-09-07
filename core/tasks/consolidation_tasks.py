from decimal import Decimal
from dateutil.relativedelta import relativedelta
from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.utils import timezone
from ..models import Invoice, CompanySettings
from ..services import ( consultar_nfe_na_prefeitura, enviar_nfe_para_prefeitura, fetch_exchange_rate )
from ..pdf_service import generate_pdf_bytes
from ..email_service import send_email_with_debug

logger = get_task_logger(__name__)

