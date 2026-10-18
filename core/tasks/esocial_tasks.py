import logging
from celery import shared_task
from celery.utils.log import get_task_logger
from django.utils import timezone

from core.models import CompanySettings
from core.services.esocial_services import sync_esocial_payroll

logger = get_task_logger(__name__)


@shared_task
def sync_esocial_payroll_task(force=False):
    """Tarefa Celery para sincronização automática diária da folha de pagamento do eSocial."""
    company = CompanySettings.load()
    if not company:
        logger.warning("sync_esocial_payroll_task: CompanySettings não configurado.")
        return {"count": 0, "message": "Configurações da empresa não encontradas."}

    # Se for execução automática (não forçada manualmente pelo usuário):
    if not force:
        # Desabilitar agendamento automático no ambiente de desenvolvimento para proteger cota
        if company.debug_mode:
            logger.info(
                "sync_esocial_payroll_task: execução automática ignorada em debug_mode (Dev)."
            )
            return {"count": 0, "message": "Execução automática ignorada em modo debug."}

        # Bloqueio dos dias 1 a 7 do mês
        if timezone.localdate().day <= 7:
            logger.info(
                "sync_esocial_payroll_task: execução ignorada na janela bloqueada de 1 a 7 do mês."
            )
            return {
                "count": 0,
                "message": "Execução ignorada na janela bloqueada de 1 a 7 do mês.",
            }

    try:
        count, msg = sync_esocial_payroll(force=force)
        logger.info("sync_esocial_payroll_task concluída: %s", msg)
        return {"count": count, "message": msg}
    except Exception as e:
        logger.exception("Erro em sync_esocial_payroll_task: %s", e)
        return {"count": 0, "message": f"Erro durante a sincronização: {str(e)}"}
