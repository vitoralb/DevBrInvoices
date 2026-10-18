import logging
from datetime import date
from decimal import Decimal
from dateutil.relativedelta import relativedelta
from django.utils import timezone

from core.models import CompanySettings, MonthlyConsolidation
from core.esocial.client import EsocialClient
from core.esocial.parser import (
    build_totalizer_id,
    extract_event_version_key,
    normalize_event_id,
    parse_s5011_xml,
    parse_s5012_xml,
)
from core.services.consolidation import audit_consolidations

logger = logging.getLogger(__name__)


def sync_esocial_payroll(
    force: bool = False,
    max_requests: int = 9,
    target_month: date | None = None,
) -> tuple[int, str]:
    """Sincroniza a folha de pagamento mensal e impostos do eSocial para os meses passados
    desde a data de abertura da empresa até o mês anterior (ou mês alvo específico).

    Respeita a cota diária de 10 requisições do eSocial BX por empregador.
    """
    company = CompanySettings.load()
    if not company:
        return 0, "Configurações da empresa não encontradas."

    if not company.pfx_cert_pem or not company.pfx_key_pem:
        return 0, "Certificado digital não configurado nas Configurações da Empresa."

    if not company.cnpj:
        return 0, "CNPJ da empresa não configurado."

    if not company.opening_date:
        return 0, "Data de abertura da empresa não configurada."

    today = timezone.localdate()

    # O eSocial BX bloqueia consultas entre os dias 1 e 7 de cada mês (código 403)
    if not force and today.day <= 7:
        return (
            0,
            "Sincronização com o eSocial bloqueada entre os dias 1 e 7 de cada mês (regra oficial do eSocial BX).",
        )

    if target_month:
        start_date = target_month.replace(day=1)
        end_date = target_month.replace(day=1)
    else:
        start_date = company.opening_date.replace(day=1)
        # Mês imediatamente anterior ao mês atual
        end_date = today.replace(day=1) - relativedelta(months=1)

    if start_date > end_date:
        return 0, "Nenhuma competência passada para sincronizar desde a abertura da empresa."

    # 1. Garante que os registros MonthlyConsolidation existam para o intervalo
    curr = start_date
    while curr <= end_date:
        MonthlyConsolidation.objects.get_or_create(month_year=curr)
        curr += relativedelta(months=1)

    # 2. Busca meses pendentes de sincronização (ordena do mais recente para o mais antigo)
    pending_cons = MonthlyConsolidation.objects.filter(
        month_year__gte=start_date,
        month_year__lte=end_date,
        esocial_synced=False,
    ).order_by("-month_year")

    if not pending_cons.exists():
        return 0, "Todos os meses passados já estão sincronizados com o eSocial."

    client = EsocialClient(
        cert_pem=company.pfx_cert_pem,
        key_pem=company.pfx_key_pem,
        debug_mode=company.debug_mode,
    )

    requests_used = 0
    # Guardamos 1 requisição para o download em lote
    budget_for_id_queries = max(1, max_requests - 1)

    month_map = {}
    quota_exhausted = False
    blackout_triggered = False

    for cons in pending_cons:
        if requests_used >= budget_for_id_queries:
            logger.info(
                "Limite diário de requisições de consulta atingido no lote atual (%d requisições).",
                requests_used,
            )
            break

        per_apur = cons.month_year.strftime("%Y-%m")
        try:
            resp_consulta = client.consultar_identificadores_eventos_empregador(
                cnpj=company.cnpj,
                tp_evt="S-1299",
                per_apur=per_apur,
            )
            requests_used += 1
        except Exception as e:
            logger.error("Falha ao consultar identificadores para %s: %s", per_apur, e)
            break

        cd_resp = resp_consulta.get("cd_resposta", 0)
        desc_resp = resp_consulta.get("desc_resposta", "")

        if cd_resp == 403:
            blackout_triggered = True
            logger.warning(
                "eSocial retornou bloqueio dos dias 1 a 7 (403): %s", desc_resp
            )
            break

        if cd_resp in (404, 405):
            quota_exhausted = True
            logger.warning(
                "eSocial retornou limite de acessos atingido (%d): %s",
                cd_resp,
                desc_resp,
            )
            break

        if cd_resp in (201, 203):
            identificadores = resp_consulta.get("identificadores", [])
            if identificadores:
                # Localiza recibo do S-1299 (se houver múltiplos, escolhe o mais recente/maior recibo)
                s1299_recibo = ""
                highest_s1299_key = -1
                for ident in identificadores:
                    rec = ident.get("nr_rec", "")
                    eid = ident.get("id", "")
                    if len(eid) == 36 or not eid.startswith(("ID110", "ID120", "ID130")):
                        v_key = extract_event_version_key(evt_id=eid, recibo=rec)
                        if v_key > highest_s1299_key:
                            highest_s1299_key = v_key
                            s1299_recibo = rec
                if not s1299_recibo and identificadores:
                    s1299_recibo = identificadores[-1].get("nr_rec", "")

                month_map[cons.id] = {
                    "cons": cons,
                    "per_apur": per_apur,
                    "s1299_recibo": s1299_recibo,
                    "identificadores": identificadores,
                }
        elif cd_resp in (406, 607):
            # Mês ainda não fechado no eSocial (sem evento S-1299)
            logger.info(
                "Competência %s ainda não possui fechamento S-1299 no eSocial (código %d: %s).",
                per_apur,
                cd_resp,
                desc_resp,
            )

    # 3. Baixa em lote os eventos S-5011 e S-5012 identificados
    all_recibos = []
    all_ids = []
    for info in month_map.values():
        for ident in info["identificadores"]:
            rec = ident.get("nr_rec")
            if rec and rec not in all_recibos:
                all_recibos.append(rec)
            eid = ident.get("id")
            if eid:
                norm_eid = normalize_event_id(eid)
                if norm_eid not in all_ids:
                    all_ids.append(norm_eid)
        s1299_recibo = info["s1299_recibo"]
        if s1299_recibo:
            id_5011 = build_totalizer_id("011", s1299_recibo)
            id_5012 = build_totalizer_id("012", s1299_recibo)
            if id_5011 not in all_ids:
                all_ids.append(id_5011)
            if id_5012 not in all_ids:
                all_ids.append(id_5012)

    downloaded_files = []
    # 1. Download por número de recibo (método oficial para totalizadores S-5011/S-5012 no eSocial BX)
    if all_recibos:
        try:
            for i in range(0, len(all_recibos), 50):
                batch_recibos = all_recibos[i : i + 50]
                resp_down = client.solicitar_download_eventos_por_nr_recibo(
                    cnpj=company.cnpj, nr_recibos=batch_recibos
                )
                requests_used += 1

                # Se o eSocial retornar código 308 (instabilidade temporária SERPRO), tenta novamente após 2s
                if resp_down.get("cd_resposta") == 308:
                    import time
                    logger.warning("eSocial retornou código 308 (instabilidade temporária SERPRO). Aguardando 2s para nova tentativa...")
                    time.sleep(2)
                    resp_down = client.solicitar_download_eventos_por_nr_recibo(
                        cnpj=company.cnpj, nr_recibos=batch_recibos
                    )
                    requests_used += 1

                for arq in resp_down.get("arquivos", []):
                    if arq.get("cd_resposta") == 201:
                        downloaded_files.append(arq)
        except Exception as e:
            logger.warning("Tentativa de download por recibo no eSocial falhou: %s", e)

    # 2. Se nenhum arquivo retornado (ou mock em testes unitários por ID), tenta download por ID
    if not downloaded_files and all_ids:
        try:
            for i in range(0, len(all_ids), 50):
                batch_ids = all_ids[i : i + 50]
                resp_down = client.solicitar_download_eventos_por_id(
                    cnpj=company.cnpj, event_ids=batch_ids
                )
                requests_used += 1
                for arq in resp_down.get("arquivos", []):
                    if arq.get("cd_resposta") == 201:
                        downloaded_files.append(arq)
        except Exception as e:
            logger.error("Falha ao baixar lote de eventos do eSocial por ID: %s", e)

    import re

    files_by_period = {}
    for arq in downloaded_files:
        xml = arq.get("evt_xml") or ""
        eid = arq.get("evt_id") or ""
        if eid.startswith("ID011") or eid.startswith("ID11") or re.search(r"<(?:[a-zA-Z0-9_-]+:)?evtCS[\s>]", xml):
            try:
                p11 = parse_s5011_xml(xml)
                per = p11.get("per_apur")
                if per:
                    v_key = extract_event_version_key(xml, p11, eid)
                    existing = files_by_period.get(per, {}).get("s5011")
                    if not existing or v_key >= existing[2]:
                        files_by_period.setdefault(per, {})["s5011"] = (p11, xml, v_key)
            except Exception as e:
                logger.warning("Erro ao processar S-5011 baixado: %s", e)
        elif eid.startswith("ID012") or eid.startswith("ID12") or re.search(r"<(?:[a-zA-Z0-9_-]+:)?evtIrrf[\s>]", xml):
            try:
                p12 = parse_s5012_xml(xml)
                per = p12.get("per_apur")
                if per:
                    v_key = extract_event_version_key(xml, p12, eid)
                    existing = files_by_period.get(per, {}).get("s5012")
                    if not existing or v_key >= existing[2]:
                        files_by_period.setdefault(per, {})["s5012"] = (p12, xml, v_key)
            except Exception as e:
                logger.warning("Erro ao processar S-5012 baixado: %s", e)

    synced_count = 0
    now = timezone.now()

    for info in month_map.values():
        cons = info["cons"]
        per_apur = info["per_apur"]
        period_data = files_by_period.get(per_apur)
        if not period_data or "s5011" not in period_data:
            logger.warning(
                "S-5011 não retornado para competência %s.",
                per_apur,
            )
            continue

        parsed_5011, xml_5011 = period_data["s5011"][:2]
        parsed_5012, xml_5012 = (
            period_data["s5012"][:2] if "s5012" in period_data else (None, "")
        )

        cons.actual_pro_labore_paid = parsed_5011["total_payroll"]
        cons.esocial_inss_tax = parsed_5011["inss_tax"]
        cons.esocial_irrf_tax = (
            parsed_5012["total_irrf"] if parsed_5012 else None
        )
        cons.esocial_s1299_recibo = info["s1299_recibo"]
        cons.esocial_s5011_xml = xml_5011
        cons.esocial_s5012_xml = xml_5012
        cons.esocial_synced = True
        cons.esocial_synced_at = now
        cons.save(
            update_fields=[
                "actual_pro_labore_paid",
                "esocial_inss_tax",
                "esocial_irrf_tax",
                "esocial_s1299_recibo",
                "esocial_s5011_xml",
                "esocial_s5012_xml",
                "esocial_synced",
                "esocial_synced_at",
            ]
        )
        synced_count += 1

    # 4. Se algum mês foi importado, executa auditoria/reconsolidação para recalcular impostos cronologicamente
    if synced_count > 0:
        audit_consolidations()

    msg = f"Sincronização concluída: {synced_count} competência(s) importada(s) do eSocial."
    if quota_exhausted:
        msg += " Limite diário de requisições do eSocial atingido. As competências restantes serão sincronizadas amanhã."
    elif blackout_triggered:
        msg += " O eSocial BX bloqueia consultas entre os dias 1 e 7 de cada mês."

    return synced_count, msg


def export_esocial_backup() -> tuple[bytes, str]:
    """Gera um arquivo ZIP de backup contendo todos os XMLs de eventos do eSocial
    (S-5011 e S-5012) e um manifest.json detalhado de todas as competências sincronizadas."""
    import io
    import json
    import zipfile

    company = CompanySettings.load()
    cnpj_clean = getattr(company, "cnpj_clean", "esocial")
    now_str = timezone.now().strftime("%Y%m%d_%H%M%S")
    filename = f"backup_esocial_{cnpj_clean}_{now_str}.zip"

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        manifest = {
            "version": "1.0",
            "exported_at": timezone.now().isoformat(),
            "cnpj": company.cnpj if company else "",
            "company_name": company.company_name if company else "",
            "competences": [],
        }

        qs = MonthlyConsolidation.objects.filter(esocial_synced=True).order_by("month_year")
        for cons in qs:
            comp_str = cons.month_year.strftime("%Y-%m")
            comp_info = {
                "competencia": comp_str,
                "actual_pro_labore_paid": str(cons.actual_pro_labore_paid),
                "esocial_inss_tax": str(cons.esocial_inss_tax) if cons.esocial_inss_tax is not None else None,
                "esocial_irrf_tax": str(cons.esocial_irrf_tax) if cons.esocial_irrf_tax is not None else None,
                "esocial_s1299_recibo": cons.esocial_s1299_recibo,
                "has_s5011": bool(cons.esocial_s5011_xml),
                "has_s5012": bool(cons.esocial_s5012_xml),
            }
            manifest["competences"].append(comp_info)

            if cons.esocial_s5011_xml:
                zf.writestr(f"{comp_str}_S-5011.xml", cons.esocial_s5011_xml.encode("utf-8"))
            if cons.esocial_s5012_xml:
                zf.writestr(f"{comp_str}_S-5012.xml", cons.esocial_s5012_xml.encode("utf-8"))

        zf.writestr(
            "manifest.json",
            json.dumps(manifest, indent=2, ensure_ascii=False).encode("utf-8"),
        )

    return buffer.getvalue(), filename


def _process_single_xml(
    xml_content: str,
    months_data: dict,
    s1299_recibo_override: str = "",
):
    """Auxiliar para analisar um XML (S-5011, S-5012, S-1299, lote de download ou pacote eSocial BX)
    e acumular em months_data."""
    from core.esocial.parser import parse_retorno_solicitacao_download

    # Se for um pacote de download do eSocial BX (offline export):
    if "retornoProcessamentoDownload" in xml_content or "retornoProcessamento" in xml_content:
        try:
            from lxml import etree
            root = etree.fromstring(xml_content.encode("utf-8"))
            for proc in root.xpath("//*[local-name()='retornoProcessamentoDownload' or local-name()='retornoProcessamento']"):
                evento_node = proc.xpath(".//*[local-name()='evento']")
                recibo_node = proc.xpath(".//*[local-name()='recibo']//*[local-name()='nrRecibo']")
                nr_rec = recibo_node[0].text.strip() if recibo_node and recibo_node[0].text else ""
                if evento_node and len(evento_node[0]):
                    inner_xml = etree.tostring(evento_node[0][0], encoding="utf-8").decode("utf-8")
                    _process_single_xml(inner_xml, months_data, s1299_recibo_override=nr_rec)
            return
        except Exception as e:
            logger.warning("Falha ao processar retornoProcessamentoDownload eSocial BX: %s", e)

    # Se for um XML de lote de download retornado pelo eSocial BX:
    if "retornoSolicitacaoDownloadEventos" in xml_content or "<download>" in xml_content:
        try:
            down_res = parse_retorno_solicitacao_download(xml_content)
            for arq in down_res.get("arquivos", []):
                evt_xml = arq.get("evt_xml", "")
                if evt_xml:
                    _process_single_xml(evt_xml, months_data)
            return
        except Exception as e:
            logger.warning("Falha ao processar arquivo de lote de download eSocial: %s", e)

    import re

    # S-5011 (evtCS)
    if re.search(r"<(?:[a-zA-Z0-9_-]+:)?evtCS[\s>]", xml_content):
        try:
            parsed = parse_s5011_xml(xml_content)
            per_apur = parsed.get("per_apur", "")
            if per_apur:
                v_key = extract_event_version_key(xml_content, parsed, recibo=s1299_recibo_override)
                months_data.setdefault(per_apur, {})
                existing = months_data[per_apur].get("s5011")
                if existing and v_key < existing.get("version_key", 0):
                    # Evento existente é mais recente/definitivo; ignora este evento anterior superado
                    return
                months_data[per_apur]["s5011"] = {
                    "parsed": parsed,
                    "xml": xml_content,
                    "version_key": v_key,
                }
                return
        except Exception as e:
            logger.warning("Falha ao analisar XML S-5011 no backup: %s", e)

    # S-5012 (evtIrrf) - não confundir com evtIrrfBenef (S-5002)
    if re.search(r"<(?:[a-zA-Z0-9_-]+:)?evtIrrf[\s>]", xml_content):
        try:
            parsed = parse_s5012_xml(xml_content)
            per_apur = parsed.get("per_apur", "")
            if per_apur:
                v_key = extract_event_version_key(xml_content, parsed, recibo=s1299_recibo_override)
                months_data.setdefault(per_apur, {})
                existing = months_data[per_apur].get("s5012")
                if existing and v_key < existing.get("version_key", 0):
                    # Evento existente é mais recente/definitivo; ignora este evento anterior superado
                    return
                months_data[per_apur]["s5012"] = {
                    "parsed": parsed,
                    "xml": xml_content,
                    "version_key": v_key,
                }
                return
        except Exception as e:
            logger.warning("Falha ao analisar XML S-5012 no backup: %s", e)

    # S-1299 (evtFechaEvPer)
    if "evtFechaEvPer" in xml_content:
        try:
            per_match = re.search(r"<(?:[a-zA-Z0-9_-]+:)?perApur>(\d{4}-\d{2})</(?:[a-zA-Z0-9_-]+:)?perApur>", xml_content)
            rec_match = re.search(r"<(?:[a-zA-Z0-9_-]+:)?nrRecArqBase>([^<]+)</(?:[a-zA-Z0-9_-]+:)?nrRecArqBase>", xml_content)
            if not rec_match:
                rec_match = re.search(r"<(?:[a-zA-Z0-9_-]+:)?nrRecibo>([^<]+)</(?:[a-zA-Z0-9_-]+:)?nrRecibo>", xml_content)
            rec_val = s1299_recibo_override or (rec_match.group(1) if rec_match else "")
            if per_match:
                per_apur = per_match.group(1)
                v_key = extract_event_version_key(xml_content, {"nr_rec": rec_val}, recibo=rec_val)
                months_data.setdefault(per_apur, {})
                existing = months_data[per_apur].get("s1299")
                if existing and v_key < existing.get("version_key", 0):
                    return
                months_data[per_apur]["s1299"] = {
                    "nr_rec": rec_val,
                    "xml": xml_content,
                    "version_key": v_key,
                }
        except Exception as e:
            logger.warning("Falha ao analisar XML S-1299 no backup: %s", e)


def import_esocial_backup(
    file_data: bytes | str | list[bytes | str | tuple[bytes | str, str]],
    filename: str = "",
) -> dict:
    """Importa um ou múltiplos arquivos de backup (ZIP, JSON ou XMLs avulsos do eSocial),
    extrai os totalizadores das competências e atualiza os registros do sistema
    exatamente como se tivessem sido recebidos via chamadas da API do eSocial.
    """
    import io
    import json
    import zipfile
    from core.models import ApiLog

    # Normaliza a entrada para uma lista de (bytes, filename)
    items_to_process: list[tuple[bytes, str]] = []
    if isinstance(file_data, list):
        for entry in file_data:
            if isinstance(entry, tuple) and len(entry) == 2:
                b = entry[0].encode("utf-8") if isinstance(entry[0], str) else entry[0]
                items_to_process.append((b, entry[1] or ""))
            elif hasattr(entry, "read") and hasattr(entry, "name"):
                items_to_process.append((entry.read(), entry.name or ""))
            elif isinstance(entry, (bytes, str)):
                b = entry.encode("utf-8") if isinstance(entry, str) else entry
                items_to_process.append((b, ""))
    else:
        b = file_data.encode("utf-8") if isinstance(file_data, str) else file_data
        items_to_process.append((b, filename))

    months_data = {}
    total_xml_count = 0
    file_names_processed = []

    for raw_bytes, item_name in items_to_process:
        if item_name:
            file_names_processed.append(item_name)

        is_zip = False
        try:
            is_zip = zipfile.is_zipfile(io.BytesIO(raw_bytes))
        except Exception:
            is_zip = False

        if is_zip:
            with zipfile.ZipFile(io.BytesIO(raw_bytes), "r") as zf:
                for item in zf.infolist():
                    if item.is_dir():
                        continue
                    name_lower = item.filename.lower()
                    content = zf.read(item).decode("utf-8", errors="replace")

                    if name_lower.endswith(".xml"):
                        total_xml_count += 1
                        _process_single_xml(content, months_data)
                    elif name_lower.endswith(".json") and name_lower != "manifest.json":
                        try:
                            data = json.loads(content)
                            if isinstance(data, list):
                                for entry in data:
                                    if "xml" in entry:
                                        total_xml_count += 1
                                        _process_single_xml(entry["xml"], months_data)
                        except Exception:
                            pass
        else:
            text_content = raw_bytes.decode("utf-8", errors="replace").strip()
            if text_content.startswith("<"):
                total_xml_count += 1
                _process_single_xml(text_content, months_data)
            elif text_content.startswith("{") or text_content.startswith("["):
                try:
                    data = json.loads(text_content)
                    if isinstance(data, list):
                        for entry in data:
                            if "xml" in entry:
                                total_xml_count += 1
                                _process_single_xml(entry["xml"], months_data)
                except Exception:
                    pass

    num_files = len(items_to_process)
    if not months_data:
        return {
            "count": 0,
            "competences": [],
            "files_count": num_files,
            "message": "Nenhum evento válido do eSocial (S-5011, S-5012 ou S-1299) foi encontrado no(s) arquivo(s) enviado(s).",
        }

    now = timezone.now()
    imported_comps = []

    for per_apur, data in sorted(months_data.items()):
        try:
            year, month = map(int, per_apur.split("-"))
            month_date = date(year, month, 1)
        except ValueError:
            continue

        cons, _ = MonthlyConsolidation.objects.get_or_create(month_year=month_date)

        has_totalizer = ("s5011" in data) or ("s5012" in data)

        if "s5011" in data:
            s5011_parsed = data["s5011"]["parsed"]
            cons.actual_pro_labore_paid = s5011_parsed.get("total_payroll", Decimal("0.00"))
            cons.esocial_inss_tax = s5011_parsed.get("inss_tax")
            cons.esocial_s5011_xml = data["s5011"]["xml"]
            rec = s5011_parsed.get("nr_rec_arq_base", "")
            if rec:
                cons.esocial_s1299_recibo = rec

        if "s5012" in data:
            s5012_parsed = data["s5012"]["parsed"]
            cons.esocial_irrf_tax = s5012_parsed.get("total_irrf")
            cons.esocial_s5012_xml = data["s5012"]["xml"]

        if "s1299" in data and not cons.esocial_s1299_recibo:
            cons.esocial_s1299_recibo = data["s1299"].get("nr_rec", "")

        update_fields = [
            "actual_pro_labore_paid",
            "esocial_inss_tax",
            "esocial_irrf_tax",
            "esocial_s1299_recibo",
            "esocial_s5011_xml",
            "esocial_s5012_xml",
        ]

        if has_totalizer:
            cons.esocial_synced = True
            cons.esocial_synced_at = now
            update_fields.extend(["esocial_synced", "esocial_synced_at"])
            imported_comps.append(per_apur)

        cons.save(update_fields=update_fields)

    if not imported_comps:
        return {
            "count": 0,
            "competences": [],
            "files_count": num_files,
            "message": "Nenhum evento totalizador (S-5011 ou S-5012) foi encontrado no(s) arquivo(s) enviado(s).",
        }

    # 3. Registra em ApiLog como importação offline de auditoria
    try:
        files_desc = ", ".join(file_names_processed[:5])
        if len(file_names_processed) > 5:
            files_desc += f" e mais {len(file_names_processed) - 5} arquivo(s)"
        ApiLog.objects.create(
            endpoint="offline://esocial/backup/import",
            method="IMPORT",
            request_payload=f"Arquivos ({num_files}): {files_desc or filename}. XMLs lidos: {total_xml_count}",
            response_payload=json.dumps({"competencias": imported_comps}),
            status_code=200,
        )
    except Exception as e:
        logger.warning("Falha ao registrar ApiLog de importação offline: %s", e)

    # 4. Recalcula cronologicamente impostos e Fator R
    if imported_comps:
        audit_consolidations()

    files_info = f"{num_files} arquivo(s) processado(s)" if num_files > 1 else "1 arquivo processado"
    return {
        "count": len(imported_comps),
        "competences": imported_comps,
        "files_count": num_files,
        "message": f"Importação concluída com sucesso: {files_info}, {len(imported_comps)} competência(s) ({', '.join(imported_comps)}) atualizada(s).",
    }

