import uuid
from datetime import date, datetime, timezone, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from dateutil.relativedelta import relativedelta
from django.contrib.auth.models import User
from django.test import Client as HttpClient, TestCase
from django.urls import reverse
from django.utils import timezone as dj_timezone

from core.models import ApiLog, CompanySettings, MonthlyConsolidation
from core.esocial.client import EsocialClient
from core.esocial.parser import (
    build_totalizer_id,
    extract_event_version_key,
    parse_retorno_consulta_identificadores,
    parse_retorno_solicitacao_download,
    parse_s5011_xml,
    parse_s5012_xml,
)
from core.esocial.signer import assinar_xml_esocial
from core.services.consolidation import audit_consolidations, consolidate_month
from core.services.esocial_services import sync_esocial_payroll
from core.tasks.esocial_tasks import sync_esocial_payroll_task


def generate_self_signed_cert_and_key():
    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "BR"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Test Org"),
        x509.NameAttribute(NameOID.COMMON_NAME, "Test CN"),
    ])
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.now(timezone.utc) - timedelta(days=1))
        .not_valid_after(datetime.now(timezone.utc) + timedelta(days=365))
        .sign(key, hashes.SHA256())
    )
    cert_pem = cert.public_bytes(serialization.Encoding.PEM).decode()
    key_pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()
    return cert_pem, key_pem


class EsocialSignerTests(TestCase):
    def setUp(self):
        self.cert_pem, self.key_pem = generate_self_signed_cert_and_key()

    def test_assinar_xml_esocial_root_reference_empty_uri(self):
        xml_input = '<eSocial xmlns="http://www.esocial.gov.br/schema/download/solicitacao/id/v1_0_0"><pedidoId><id>ID1000000000000002026101700000000001</id></pedidoId></eSocial>'
        signed_xml = assinar_xml_esocial(xml_input, self.key_pem, self.cert_pem)

        self.assertIn("Signature", signed_xml)
        self.assertIn('URI=""', signed_xml)
        self.assertIn("DigestValue", signed_xml)
        self.assertIn("SignatureValue", signed_xml)
        self.assertIn("X509Certificate", signed_xml)


class EsocialParserTests(TestCase):
    def test_build_totalizer_id(self):
        tot_id = build_totalizer_id("011", "1.2.0000000000000000001")
        self.assertTrue(tot_id.startswith("ID011"))
        self.assertEqual(len(tot_id), 36)

    def test_extract_event_version_key(self):
        # 1. From standard receipt with dots
        self.assertEqual(extract_event_version_key(recibo="1.1.0000000028475541238"), 28475541238)
        self.assertEqual(extract_event_version_key(recibo="1.2.0000000000000000001"), 1)

        # 2. From parsed dict
        self.assertEqual(extract_event_version_key(parsed_dict={"nr_rec_arq_base": "1.1.0000000028129293607"}), 28129293607)
        self.assertEqual(extract_event_version_key(parsed_dict={"nr_recibo": "1.1.0000000028426211902"}), 28426211902)

        # 3. From evt_id (e.g. ID011... or ID1...)
        self.assertEqual(extract_event_version_key(evt_id="ID0110000000000000000000028475541238"), 28475541238)
        self.assertEqual(extract_event_version_key(evt_id="ID1123456780001952026091700000000001"), 1123456780001952026091700000000001)

        # 4. Monotonic ordering verification (rectification order)
        key_initial = extract_event_version_key(recibo="1.1.0000000028129293607")
        key_reopen = extract_event_version_key(recibo="1.1.0000000028426211902")
        key_final = extract_event_version_key(recibo="1.1.0000000028475541238")
        self.assertTrue(key_initial < key_reopen < key_final)

        # 5. Fallback on empty
        self.assertEqual(extract_event_version_key(), 0)

    def test_parse_s5011_xml_normal(self):
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <eSocial xmlns="http://www.esocial.gov.br/schema/evt/evtCS/v_S_01_03_00">
          <evtCS Id="ID1123456780001952026081700000000001">
            <ideEvento>
              <perApur>2026-08</perApur>
            </ideEvento>
            <ideEmpregador>
              <tpInsc>1</tpInsc>
              <nrInsc>12345678</nrInsc>
            </ideEmpregador>
            <infoCS>
              <nrRecArqBase>1.2.0000000000000000001</nrRecArqBase>
              <indExistInfo>1</indExistInfo>
              <infoCPSeg>
                <vrDescCP>856.46</vrDescCP>
              </infoCPSeg>
              <ideEstab>
                <tpInsc>1</tpInsc>
                <nrInsc>12345678000195</nrInsc>
                <ideLotacao>
                  <codLotacao>LOT01</codLotacao>
                  <fpas>515</fpas>
                  <codTercs>0000</codTercs>
                  <basesRemun>
                    <indIncid>1</indIncid>
                    <codCateg>722</codCateg>
                    <basesCp>
                      <vrBcCp00>5000.00</vrBcCp00>
                    </basesCp>
                  </basesRemun>
                  <basesRemun>
                    <indIncid>1</indIncid>
                    <codCateg>722</codCateg>
                    <basesCp>
                      <vrBcCp00>2500.00</vrBcCp00>
                    </basesCp>
                  </basesRemun>
                </ideLotacao>
              </ideEstab>
            </infoCS>
          </evtCS>
        </eSocial>
        """
        result = parse_s5011_xml(xml_content)
        self.assertEqual(result["total_payroll"], Decimal("7500.00"))
        self.assertEqual(result["inss_tax"], Decimal("856.46"))
        self.assertEqual(result["per_apur"], "2026-08")

    def test_parse_s5011_xml_sem_movimento(self):
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <eSocial xmlns="http://www.esocial.gov.br/schema/evt/evtCS/v_S_01_03_00">
          <evtCS Id="ID1123456780001952026081700000000002">
            <ideEvento>
              <perApur>2026-08</perApur>
            </ideEvento>
            <ideEmpregador>
              <tpInsc>1</tpInsc>
              <nrInsc>12345678</nrInsc>
            </ideEmpregador>
            <infoCS>
              <nrRecArqBase>1.2.0000000000000000002</nrRecArqBase>
              <indExistInfo>3</indExistInfo>
            </infoCS>
          </evtCS>
        </eSocial>
        """
        result = parse_s5011_xml(xml_content)
        self.assertEqual(result["total_payroll"], Decimal("0.00"))
        self.assertEqual(result["inss_tax"], Decimal("0.00"))
        self.assertEqual(result["ind_exist_info"], 3)

    def test_parse_s5012_xml(self):
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <eSocial xmlns="http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00">
          <evtIrrf Id="ID1123456780001952026081700000000003">
            <ideEvento>
              <perApur>2026-08</perApur>
            </ideEvento>
            <ideEmpregador>
              <tpInsc>1</tpInsc>
              <nrInsc>12345678</nrInsc>
            </ideEmpregador>
            <infoIRRF>
              <nrRecArqBase>1.2.0000000000000000001</nrRecArqBase>
              <indExistInfo>1</indExistInfo>
              <infoCRMen>
                <CRMen>056107</CRMen>
                <vrCRMen>150.25</vrCRMen>
              </infoCRMen>
              <infoCRMen>
                <CRMen>056108</CRMen>
                <vrCRMen>50.00</vrCRMen>
              </infoCRMen>
            </infoIRRF>
          </evtIrrf>
        </eSocial>
        """
        result = parse_s5012_xml(xml_content)
        self.assertEqual(result["total_irrf"], Decimal("200.25"))
        self.assertEqual(result["per_apur"], "2026-08")

    def test_parse_retorno_consulta_identificadores(self):
        xml_resp = """<eSocial xmlns="http://www.esocial.gov.br/schema/consulta/identificadores-eventos/retorno/v1_0_0">
          <retornoConsultaIdentificadoresEvts>
            <status>
              <cdResposta>201</cdResposta>
              <descResposta>Sucesso</descResposta>
            </status>
            <retornoIdentificadoresEvts>
              <identificadoresEvts>
                <identificadorEvt>
                  <id>ID1123456780000002026080100000000001</id>
                  <nrRec>1.2.1111111111111111111</nrRec>
                </identificadorEvt>
                <identificadorEvt>
                  <id>ID1123456780000002026080100000000002</id>
                  <nrRec>1.2.2222222222222222222</nrRec>
                </identificadorEvt>
              </identificadoresEvts>
            </retornoIdentificadoresEvts>
          </retornoConsultaIdentificadoresEvts>
        </eSocial>"""
        result = parse_retorno_consulta_identificadores(xml_resp)
        self.assertEqual(result["cd_resposta"], 201)
        identificadores = result["identificadores"]
        self.assertEqual(len(identificadores), 2)
        self.assertEqual(identificadores[0]["id"], "ID1123456780000002026080100000000001")
        self.assertEqual(identificadores[0]["nr_rec"], "1.2.1111111111111111111")

    def test_parse_retorno_solicitacao_download(self):
        xml_resp = """<eSocial xmlns="http://www.esocial.gov.br/schema/download/solicitacao/retorno/v1_0_0">
          <download>
            <status>
              <cdResposta>201</cdResposta>
              <descResposta>Sucesso</descResposta>
            </status>
            <arquivos>
              <arquivo>
                <status>
                  <cdResposta>201</cdResposta>
                  <descResposta>Sucesso</descResposta>
                </status>
                <evt Id="ID50110001">
                  <eSocial xmlns="http://www.esocial.gov.br/schema/evt/evtCS/v_S_01_03_00">
                    <evtCS Id="ID50110001"><infoCS><indExistInfo>3</indExistInfo></infoCS></evtCS>
                  </eSocial>
                </evt>
              </arquivo>
            </arquivos>
          </download>
        </eSocial>"""
        result = parse_retorno_solicitacao_download(xml_resp)
        self.assertEqual(result["cd_resposta"], 201)
        arquivos = result["arquivos"]
        self.assertEqual(len(arquivos), 1)
        self.assertEqual(arquivos[0]["evt_id"], "ID50110001")


class EsocialClientAndSyncTests(TestCase):
    def setUp(self):
        self.cert_pem, self.key_pem = generate_self_signed_cert_and_key()
        self.company = CompanySettings.objects.create(
            company_name="Empresa Teste eSocial",
            cnpj="12.345.678/0001-95",
            opening_date=date(2026, 7, 1),
            inscricao_municipal="987654",
            email="empresa@teste.com",
            pfx_cert_pem=self.cert_pem,
            pfx_key_pem=self.key_pem,
            debug_mode=True,
        )
        self.user = User.objects.create_superuser("admin_esocial", "admin@teste.com", "pass123")
        self.client = HttpClient()
        self.client.force_login(self.user)

    @patch("core.esocial.client.logged_post")
    def test_esocial_client_logged_post(self, mock_logged_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = """<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/">
            <s:Body>
                <ConsultarIdentificadoresEventosEmpregadorResult>
                    <eSocial xmlns="http://www.esocial.gov.br/schema/consulta/identificadores-eventos/retorno/v1_0_0">
                        <retornoConsultaIdentificadoresEvts>
                            <status><cdResposta>201</cdResposta><descResposta>Sucesso</descResposta></status>
                        </retornoConsultaIdentificadoresEvts>
                    </eSocial>
                </ConsultarIdentificadoresEventosEmpregadorResult>
            </s:Body>
        </s:Envelope>"""
        mock_logged_post.return_value = mock_resp

        client = EsocialClient(self.cert_pem, self.key_pem, debug_mode=True)
        resp_dict = client.consultar_identificadores_eventos_empregador(
            cnpj=self.company.cnpj,
            tp_evt="S-1299",
            per_apur="2026-08",
        )

        self.assertEqual(resp_dict["cd_resposta"], 201)
        mock_logged_post.assert_called_once()

    @patch.object(
        EsocialClient,
        "solicitar_download_eventos_por_nr_recibo",
        return_value={"cd_resposta": 201, "desc_resposta": "Sucesso", "arquivos": []},
    )
    @patch.object(EsocialClient, "solicitar_download_eventos_por_id")
    @patch.object(EsocialClient, "consultar_identificadores_eventos_empregador")
    def test_sync_esocial_payroll_success(
        self, mock_consultar, mock_download, mock_nr_recibo
    ):
        c_jul = MonthlyConsolidation.objects.create(
            month_year=date(2026, 7, 1),
            total_revenue_internal=Decimal("10000.00"),
            actual_pro_labore_paid=Decimal("0.00"),
        )
        c_aug = MonthlyConsolidation.objects.create(
            month_year=date(2026, 8, 1),
            total_revenue_internal=Decimal("20000.00"),
            actual_pro_labore_paid=Decimal("0.00"),
        )

        def fake_consultar(cnpj, tp_evt, per_apur):
            if per_apur == "2026-07":
                return {
                    "cd_resposta": 201,
                    "desc_resposta": "Sucesso",
                    "identificadores": [{"id": "ID1299001", "nr_rec": "1.2.0000000000000000001"}],
                }
            elif per_apur == "2026-08":
                return {
                    "cd_resposta": 201,
                    "desc_resposta": "Sucesso",
                    "identificadores": [{"id": "ID1299002", "nr_rec": "1.2.0000000000000000002"}],
                }
            return {"cd_resposta": 406, "desc_resposta": "Sem dados", "identificadores": []}

        mock_consultar.side_effect = fake_consultar

        def fake_download(cnpj, event_ids):
            arquivos = []
            for eid in event_ids:
                if "011" in eid and "0000000000000000001" in eid:
                    # July S-5011
                    xml = """<eSocial xmlns="http://www.esocial.gov.br/schema/evt/evtCS/v_S_01_03_00">
                      <evtCS Id="{0}">
                        <ideEvento><perApur>2026-07</perApur></ideEvento>
                        <ideEmpregador><tpInsc>1</tpInsc><nrInsc>12345678</nrInsc></ideEmpregador>
                        <infoCS>
                          <nrRecArqBase>1.2.0000000000000000001</nrRecArqBase>
                          <indExistInfo>1</indExistInfo>
                          <infoCPSeg><vrDescCP>330.00</vrDescCP></infoCPSeg>
                          <ideEstab>
                            <tpInsc>1</tpInsc><nrInsc>12345678000195</nrInsc>
                            <ideLotacao>
                              <codLotacao>L1</codLotacao><fpas>515</fpas><codTercs>0000</codTercs>
                              <basesRemun><indIncid>1</indIncid><codCateg>722</codCateg><basesCp><vrBcCp00>3000.00</vrBcCp00></basesCp></basesRemun>
                            </ideLotacao>
                          </ideEstab>
                        </infoCS>
                      </evtCS>
                    </eSocial>""".format(eid)
                    arquivos.append({"cd_resposta": 201, "evt_id": eid, "evt_xml": xml})
                elif "012" in eid and "0000000000000000001" in eid:
                    # July S-5012
                    xml = """<eSocial xmlns="http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00">
                      <evtIrrf Id="{0}">
                        <ideEvento><perApur>2026-07</perApur></ideEvento>
                        <ideEmpregador><tpInsc>1</tpInsc><nrInsc>12345678</nrInsc></ideEmpregador>
                        <infoIRRF>
                          <nrRecArqBase>1.2.0000000000000000001</nrRecArqBase>
                          <indExistInfo>1</indExistInfo>
                          <infoCRMen><CRMen>056107</CRMen><vrCRMen>30.81</vrCRMen></infoCRMen>
                        </infoIRRF>
                      </evtIrrf>
                    </eSocial>""".format(eid)
                    arquivos.append({"cd_resposta": 201, "evt_id": eid, "evt_xml": xml})
                elif "011" in eid and "0000000000000000002" in eid:
                    # August S-5011
                    xml = """<eSocial xmlns="http://www.esocial.gov.br/schema/evt/evtCS/v_S_01_03_00">
                      <evtCS Id="{0}">
                        <ideEvento><perApur>2026-08</perApur></ideEvento>
                        <ideEmpregador><tpInsc>1</tpInsc><nrInsc>12345678</nrInsc></ideEmpregador>
                        <infoCS>
                          <nrRecArqBase>1.2.0000000000000000002</nrRecArqBase>
                          <indExistInfo>1</indExistInfo>
                          <infoCPSeg><vrDescCP>550.00</vrDescCP></infoCPSeg>
                          <ideEstab>
                            <tpInsc>1</tpInsc><nrInsc>12345678000195</nrInsc>
                            <ideLotacao>
                              <codLotacao>L1</codLotacao><fpas>515</fpas><codTercs>0000</codTercs>
                              <basesRemun><indIncid>1</indIncid><codCateg>722</codCateg><basesCp><vrBcCp00>5000.00</vrBcCp00></basesCp></basesRemun>
                            </ideLotacao>
                          </ideEstab>
                        </infoCS>
                      </evtCS>
                    </eSocial>""".format(eid)
                    arquivos.append({"cd_resposta": 201, "evt_id": eid, "evt_xml": xml})
                elif "012" in eid and "0000000000000000002" in eid:
                    # August S-5012
                    xml = """<eSocial xmlns="http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00">
                      <evtIrrf Id="{0}">
                        <ideEvento><perApur>2026-08</perApur></ideEvento>
                        <ideEmpregador><tpInsc>1</tpInsc><nrInsc>12345678</nrInsc></ideEmpregador>
                        <infoIRRF>
                          <nrRecArqBase>1.2.0000000000000000002</nrRecArqBase>
                          <indExistInfo>1</indExistInfo>
                          <infoCRMen><CRMen>056107</CRMen><vrCRMen>250.00</vrCRMen></infoCRMen>
                        </infoIRRF>
                      </evtIrrf>
                    </eSocial>""".format(eid)
                    arquivos.append({"cd_resposta": 201, "evt_id": eid, "evt_xml": xml})
            return {"cd_resposta": 201, "desc_resposta": "Sucesso", "arquivos": arquivos}

        mock_download.side_effect = fake_download

        with patch("django.utils.timezone.localdate") as mock_localdate:
            mock_localdate.return_value = date(2026, 9, 15)
            count, msg = sync_esocial_payroll(force=True)

        self.assertEqual(count, 2)
        self.assertIn("2 competência(s) importada(s)", msg)

        c_jul.refresh_from_db()
        self.assertTrue(c_jul.esocial_synced)
        self.assertEqual(c_jul.actual_pro_labore_paid, Decimal("3000.00"))
        self.assertEqual(c_jul.esocial_inss_tax, Decimal("330.00"))
        self.assertEqual(c_jul.esocial_irrf_tax, Decimal("30.81"))
        self.assertEqual(c_jul.esocial_s1299_recibo, "1.2.0000000000000000001")

        c_aug.refresh_from_db()
        self.assertTrue(c_aug.esocial_synced)
        self.assertEqual(c_aug.actual_pro_labore_paid, Decimal("5000.00"))
        self.assertEqual(c_aug.esocial_inss_tax, Decimal("550.00"))
        self.assertEqual(c_aug.esocial_irrf_tax, Decimal("250.00"))

    def test_esocial_discrepancy_warning_property(self):
        c = MonthlyConsolidation(
            month_year=date(2026, 8, 1),
            actual_pro_labore_paid=Decimal("5000.00"),
            inss_tax=Decimal("550.00"),
            irrf_tax=Decimal("280.00"),
            esocial_synced=True,
            esocial_inss_tax=Decimal("550.00"),
            esocial_irrf_tax=Decimal("200.00"),  # Discrepancy > 0.05
        )
        warning = c.esocial_discrepancy_warning
        self.assertIsNotNone(warning)
        self.assertIn("Divergência com eSocial", warning)
        self.assertIn("IRRF calculado R$ 280.00 vs eSocial R$ 200.00", warning)

        # When matching within 0.05
        c.esocial_irrf_tax = Decimal("280.03")
        self.assertIsNone(c.esocial_discrepancy_warning)

    def test_past_months_protected_from_overwrite(self):
        past_month = date(2026, 6, 1)
        c = MonthlyConsolidation.objects.create(
            month_year=past_month,
            total_revenue_internal=Decimal("10000.00"),
            actual_pro_labore_paid=Decimal("4500.00"),
            esocial_synced=True,
        )

        with patch("django.utils.timezone.localdate") as mock_localdate:
            mock_localdate.return_value = date(2026, 10, 1)
            recon = consolidate_month(past_month)
            self.assertEqual(recon.actual_pro_labore_paid, Decimal("4500.00"))

            audit_consolidations()
            c.refresh_from_db()
            self.assertEqual(c.actual_pro_labore_paid, Decimal("4500.00"))

    def test_htmx_reconsolidate_month_blocks_past_months(self):
        past_month = date(2026, 6, 1)
        c = MonthlyConsolidation.objects.create(
            month_year=past_month,
            total_revenue_internal=Decimal("10000.00"),
            actual_pro_labore_paid=Decimal("4500.00"),
        )
        url = reverse("htmx_reconsolidate_month", kwargs={"pk": c.pk})

        with patch("django.utils.timezone.localdate") as mock_localdate:
            mock_localdate.return_value = date(2026, 10, 1)
            response = self.client.post(url, {"actual_pro_labore_paid": "9999.00"})
            self.assertEqual(response.status_code, 400)
            c.refresh_from_db()
            self.assertEqual(c.actual_pro_labore_paid, Decimal("4500.00"))

    def test_htmx_reconsolidate_month_allows_current_month(self):
        curr_month = date(2026, 10, 1)
        c = MonthlyConsolidation.objects.create(
            month_year=curr_month,
            total_revenue_internal=Decimal("10000.00"),
            actual_pro_labore_paid=Decimal("3000.00"),
        )
        url = reverse("htmx_reconsolidate_month", kwargs={"pk": c.pk})

        with patch("django.utils.timezone.localdate") as mock_localdate:
            mock_localdate.return_value = date(2026, 10, 15)
            response = self.client.post(url, {"actual_pro_labore_paid": "4000.00"})
            self.assertEqual(response.status_code, 200)
            c.refresh_from_db()
            self.assertEqual(c.actual_pro_labore_paid, Decimal("4000.00"))

    def test_sync_esocial_view_post(self):
        url = reverse("sync_esocial")
        with patch("core.services.esocial_services.sync_esocial_payroll") as mock_sync:
            mock_sync.return_value = (2, "Sincronização concluída: 2 competência(s) importada(s) do eSocial.")
            response = self.client.post(url, follow=True)
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "Sincronização concluída")
            self.assertContains(response, "Sincronizar eSocial")

    def test_celery_task_skips_in_debug_mode_without_force(self):
        self.company.debug_mode = True
        self.company.save()

        with patch("core.tasks.esocial_tasks.sync_esocial_payroll") as mock_sync:
            result = sync_esocial_payroll_task(force=False)
            self.assertEqual(result.get("message"), "Execução automática ignorada em modo debug.")
            mock_sync.assert_not_called()

            # When force=True, it should execute
            mock_sync.return_value = (1, "1 importada.")
            result_forced = sync_esocial_payroll_task(force=True)
            self.assertEqual(result_forced.get("count"), 1)
            mock_sync.assert_called_once()


class EsocialBackupTests(TestCase):
    def setUp(self):
        self.cert_pem, self.key_pem = generate_self_signed_cert_and_key()
        self.company = CompanySettings.objects.create(
            company_name="Empresa Teste eSocial",
            cnpj="12.345.678/0001-95",
            opening_date=date(2026, 7, 1),
            inscricao_municipal="987654",
            email="empresa@teste.com",
            pfx_cert_pem=self.cert_pem,
            pfx_key_pem=self.key_pem,
            debug_mode=True,
        )
        self.user = User.objects.create_superuser("admin_esocial", "admin@teste.com", "pass123")
        self.client = HttpClient()
        self.client.force_login(self.user)

    def test_export_and_import_esocial_backup(self):
        import io
        import zipfile
        from core.services.esocial_services import export_esocial_backup, import_esocial_backup

        s5011_sample = """<eSocial xmlns="http://www.esocial.gov.br/schema/evt/evtCS/v_S_01_03_00">
          <evtCS Id="ID1123456780001952026091700000000001">
            <ideEvento><perApur>2026-09</perApur></ideEvento>
            <ideEmpregador><tpInsc>1</tpInsc><nrInsc>12345678</nrInsc></ideEmpregador>
            <infoCS>
              <nrRecArqBase>1.2.9999999999999999999</nrRecArqBase>
              <indExistInfo>1</indExistInfo>
              <infoCPSeg><vrDescCP>750.00</vrDescCP></infoCPSeg>
              <ideEstab>
                <tpInsc>1</tpInsc><nrInsc>12345678000195</nrInsc>
                <ideLotacao>
                  <codLotacao>L1</codLotacao><fpas>515</fpas><codTercs>0000</codTercs>
                  <basesRemun><indIncid>1</indIncid><codCateg>722</codCateg><basesCp><vrBcCp00>6500.00</vrBcCp00></basesCp></basesRemun>
                </ideLotacao>
              </ideEstab>
            </infoCS>
          </evtCS>
        </eSocial>"""

        s5012_sample = """<eSocial xmlns="http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00">
          <evtIrrf Id="ID1123456780001952026091700000000002">
            <ideEvento><perApur>2026-09</perApur></ideEvento>
            <ideEmpregador><tpInsc>1</tpInsc><nrInsc>12345678</nrInsc></ideEmpregador>
            <infoIRRF>
              <nrRecArqBase>1.2.9999999999999999999</nrRecArqBase>
              <indExistInfo>1</indExistInfo>
              <infoCRMen><CRMen>056107</CRMen><vrCRMen>320.00</vrCRMen></infoCRMen>
            </infoIRRF>
          </evtIrrf>
        </eSocial>"""

        # 1. Create a month with XMLs and test export
        cons = MonthlyConsolidation.objects.create(
            month_year=date(2026, 9, 1),
            total_revenue_internal=Decimal("25000.00"),
            actual_pro_labore_paid=Decimal("6500.00"),
            esocial_inss_tax=Decimal("750.00"),
            esocial_irrf_tax=Decimal("320.00"),
            esocial_s1299_recibo="1.2.9999999999999999999",
            esocial_s5011_xml=s5011_sample,
            esocial_s5012_xml=s5012_sample,
            esocial_synced=True,
        )

        zip_bytes, filename = export_esocial_backup()
        self.assertTrue(filename.endswith(".zip"))
        zf = zipfile.ZipFile(io.BytesIO(zip_bytes))
        self.assertIn("manifest.json", zf.namelist())
        self.assertIn("2026-09_S-5011.xml", zf.namelist())
        self.assertIn("2026-09_S-5012.xml", zf.namelist())

        # 2. Reset consolidation and test import
        cons.delete()
        self.assertFalse(MonthlyConsolidation.objects.filter(month_year=date(2026, 9, 1)).exists())

        res = import_esocial_backup(zip_bytes, filename=filename)
        self.assertEqual(res["count"], 1)
        self.assertEqual(res["competences"], ["2026-09"])

        imported = MonthlyConsolidation.objects.get(month_year=date(2026, 9, 1))
        self.assertTrue(imported.esocial_synced)
        self.assertEqual(imported.actual_pro_labore_paid, Decimal("6500.00"))
        self.assertEqual(imported.esocial_inss_tax, Decimal("750.00"))
        self.assertEqual(imported.esocial_irrf_tax, Decimal("320.00"))
        self.assertEqual(imported.esocial_s1299_recibo, "1.2.9999999999999999999")
        self.assertEqual(imported.esocial_s5011_xml, s5011_sample)
        self.assertEqual(imported.esocial_s5012_xml, s5012_sample)

    def test_import_from_single_xml(self):
        from core.services.esocial_services import import_esocial_backup

        s5011_xml = """<eSocial xmlns="http://www.esocial.gov.br/schema/evt/evtCS/v_S_01_03_00">
          <evtCS Id="ID1123456780001952026091700000000003">
            <ideEvento><perApur>2026-09</perApur></ideEvento>
            <ideEmpregador><tpInsc>1</tpInsc><nrInsc>12345678</nrInsc></ideEmpregador>
            <infoCS>
              <nrRecArqBase>1.2.8888888888888888888</nrRecArqBase>
              <indExistInfo>1</indExistInfo>
              <infoCPSeg><vrDescCP>500.00</vrDescCP></infoCPSeg>
              <ideEstab>
                <tpInsc>1</tpInsc><nrInsc>12345678000195</nrInsc>
                <ideLotacao>
                  <codLotacao>L1</codLotacao><fpas>515</fpas><codTercs>0000</codTercs>
                  <basesRemun><indIncid>1</indIncid><codCateg>722</codCateg><basesCp><vrBcCp00>4800.00</vrBcCp00></basesCp></basesRemun>
                </ideLotacao>
              </ideEstab>
            </infoCS>
          </evtCS>
        </eSocial>"""

        res = import_esocial_backup(s5011_xml, filename="2026-09_S-5011.xml")
        self.assertEqual(res["count"], 1)

        c = MonthlyConsolidation.objects.get(month_year=date(2026, 9, 1))
        self.assertEqual(c.actual_pro_labore_paid, Decimal("4800.00"))
        self.assertEqual(c.esocial_inss_tax, Decimal("500.00"))
        self.assertEqual(c.esocial_s1299_recibo, "1.2.8888888888888888888")

    def test_views_export_and_import(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        # Export view
        url_export = reverse("export_esocial_backup")
        resp_export = self.client.get(url_export)
        self.assertEqual(resp_export.status_code, 200)
        self.assertEqual(resp_export["Content-Type"], "application/zip")

        # Import view with empty file
        url_import = reverse("import_esocial_backup")
        resp_empty = self.client.post(url_import, follow=True)
        self.assertEqual(resp_empty.status_code, 200)
        self.assertContains(resp_empty, "Nenhum arquivo enviado")

        # Import view with sample XML
        s5011_xml = """<eSocial xmlns="http://www.esocial.gov.br/schema/evt/evtCS/v_S_01_03_00">
          <evtCS Id="ID1123456780001952026091700000000004">
            <ideEvento><perApur>2026-09</perApur></ideEvento>
            <ideEmpregador><tpInsc>1</tpInsc><nrInsc>12345678</nrInsc></ideEmpregador>
            <infoCS>
              <nrRecArqBase>1.2.7777777777777777777</nrRecArqBase>
              <indExistInfo>1</indExistInfo>
              <infoCPSeg><vrDescCP>600.00</vrDescCP></infoCPSeg>
              <ideEstab>
                <tpInsc>1</tpInsc><nrInsc>12345678000195</nrInsc>
                <ideLotacao>
                  <codLotacao>L1</codLotacao><fpas>515</fpas><codTercs>0000</codTercs>
                  <basesRemun><indIncid>1</indIncid><codCateg>722</codCateg><basesCp><vrBcCp00>5500.00</vrBcCp00></basesCp></basesRemun>
                </ideLotacao>
              </ideEstab>
            </infoCS>
          </evtCS>
        </eSocial>"""
        upload = SimpleUploadedFile("september.xml", s5011_xml.encode("utf-8"), content_type="text/xml")
        resp_upload = self.client.post(url_import, {"backup_file": upload}, follow=True)
        self.assertEqual(resp_upload.status_code, 200)
        self.assertContains(resp_upload, "Importação concluída com sucesso")
        c = MonthlyConsolidation.objects.get(month_year=date(2026, 9, 1))
        self.assertEqual(c.actual_pro_labore_paid, Decimal("5500.00"))

    def test_import_multiple_files_and_zips(self):
        import io
        import zipfile
        from django.core.files.uploadedfile import SimpleUploadedFile
        from core.services.esocial_services import import_esocial_backup

        s5011_jul = """<eSocial xmlns="http://www.esocial.gov.br/schema/evt/evtCS/v_S_01_03_00">
          <evtCS Id="ID1123456780001952026071700000000001">
            <ideEvento><perApur>2026-07</perApur></ideEvento>
            <ideEmpregador><tpInsc>1</tpInsc><nrInsc>12345678</nrInsc></ideEmpregador>
            <infoCS>
              <nrRecArqBase>1.2.1111111111111111111</nrRecArqBase>
              <indExistInfo>1</indExistInfo>
              <infoCPSeg><vrDescCP>330.00</vrDescCP></infoCPSeg>
              <ideEstab>
                <tpInsc>1</tpInsc><nrInsc>12345678000195</nrInsc>
                <ideLotacao>
                  <codLotacao>L1</codLotacao><fpas>515</fpas><codTercs>0000</codTercs>
                  <basesRemun><indIncid>1</indIncid><codCateg>722</codCateg><basesCp><vrBcCp00>3000.00</vrBcCp00></basesCp></basesRemun>
                </ideLotacao>
              </ideEstab>
            </infoCS>
          </evtCS>
        </eSocial>"""

        s5011_aug = """<eSocial xmlns="http://www.esocial.gov.br/schema/evt/evtCS/v_S_01_03_00">
          <evtCS Id="ID1123456780001952026081700000000001">
            <ideEvento><perApur>2026-08</perApur></ideEvento>
            <ideEmpregador><tpInsc>1</tpInsc><nrInsc>12345678</nrInsc></ideEmpregador>
            <infoCS>
              <nrRecArqBase>1.2.2222222222222222222</nrRecArqBase>
              <indExistInfo>1</indExistInfo>
              <infoCPSeg><vrDescCP>440.00</vrDescCP></infoCPSeg>
              <ideEstab>
                <tpInsc>1</tpInsc><nrInsc>12345678000195</nrInsc>
                <ideLotacao>
                  <codLotacao>L1</codLotacao><fpas>515</fpas><codTercs>0000</codTercs>
                  <basesRemun><indIncid>1</indIncid><codCateg>722</codCateg><basesCp><vrBcCp00>4000.00</vrBcCp00></basesCp></basesRemun>
                </ideLotacao>
              </ideEstab>
            </infoCS>
          </evtCS>
        </eSocial>"""

        # Create two distinct ZIP files
        buf1 = io.BytesIO()
        with zipfile.ZipFile(buf1, "w") as z1:
            z1.writestr("2026-07_S-5011.xml", s5011_jul.encode("utf-8"))
        zip1_bytes = buf1.getvalue()

        buf2 = io.BytesIO()
        with zipfile.ZipFile(buf2, "w") as z2:
            z2.writestr("2026-08_S-5011.xml", s5011_aug.encode("utf-8"))
        zip2_bytes = buf2.getvalue()

        # 1. Test service accepting multiple ZIPs
        res = import_esocial_backup([(zip1_bytes, "batch_jul.zip"), (zip2_bytes, "batch_aug.zip")])
        self.assertEqual(res["count"], 2)
        self.assertEqual(res["competences"], ["2026-07", "2026-08"])
        self.assertEqual(res["files_count"], 2)

        c_jul = MonthlyConsolidation.objects.get(month_year=date(2026, 7, 1))
        self.assertEqual(c_jul.actual_pro_labore_paid, Decimal("3000.00"))
        self.assertEqual(c_jul.esocial_inss_tax, Decimal("330.00"))

        c_aug = MonthlyConsolidation.objects.get(month_year=date(2026, 8, 1))
        self.assertEqual(c_aug.actual_pro_labore_paid, Decimal("4000.00"))
        self.assertEqual(c_aug.esocial_inss_tax, Decimal("440.00"))

        # 2. Test view accepting multiple uploaded files simultaneously
        url_import = reverse("import_esocial_backup")
        f1 = SimpleUploadedFile("batch_jul.zip", zip1_bytes, content_type="application/zip")
        f2 = SimpleUploadedFile("batch_aug.zip", zip2_bytes, content_type="application/zip")
        resp = self.client.post(url_import, {"backup_file": [f1, f2]}, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "2 arquivo(s) processado(s)")

    def test_management_command(self):
        import os
        import tempfile
        from django.core.management import call_command

        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            call_command("esocial_backup", export=tmp_path)
            self.assertTrue(os.path.getsize(tmp_path) > 0)

            # Test import
            call_command("esocial_backup", import_files=[tmp_path])
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_import_esocial_bx_wrapped_xml(self):
        import io
        import zipfile
        from core.services.esocial_services import import_esocial_backup

        bx_s5011_wrapped = """<eSocial xmlns="http://www.esocial.gov.br/schema/download/retornoProcessamento/v1_0_0">
          <retornoProcessamentoDownload>
            <evento>
              <eSocial xmlns="http://www.esocial.gov.br/schema/evt/evtCS/v_S_01_03_00">
                <evtCS Id="ID0110000000000000000000043192698437">
                  <ideEvento><perApur>2026-10</perApur></ideEvento>
                  <ideEmpregador><tpInsc>1</tpInsc><nrInsc>12345678</nrInsc></ideEmpregador>
                  <infoCS>
                    <nrRecArqBase>1.1.0000000043192698437</nrRecArqBase>
                    <indExistInfo>1</indExistInfo>
                    <infoCPSeg><vrDescCP>770.00</vrDescCP></infoCPSeg>
                    <ideEstab>
                      <tpInsc>1</tpInsc><nrInsc>12345678000195</nrInsc>
                      <ideLotacao>
                        <codLotacao>L1</codLotacao><fpas>515</fpas><codTercs>0000</codTercs>
                        <basesRemun><indIncid>1</indIncid><codCateg>722</codCateg><basesCp><vrBcCp00>7000.00</vrBcCp00></basesCp></basesRemun>
                      </ideLotacao>
                    </ideEstab>
                  </infoCS>
                </evtCS>
              </eSocial>
            </evento>
            <recibo/>
          </retornoProcessamentoDownload>
        </eSocial>"""

        bx_s5012_wrapped = """<eSocial xmlns="http://www.esocial.gov.br/schema/download/retornoProcessamento/v1_0_0">
          <retornoProcessamentoDownload>
            <evento>
              <eSocial xmlns="http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00">
                <evtIrrf Id="ID0120000000000000000000043192698437">
                  <ideEvento><perApur>2026-10</perApur></ideEvento>
                  <ideEmpregador><tpInsc>1</tpInsc><nrInsc>12345678</nrInsc></ideEmpregador>
                  <infoIRRF>
                    <nrRecArqBase>1.1.0000000043192698437</nrRecArqBase>
                    <indExistInfo>1</indExistInfo>
                    <infoCRMen><CRMen>056107</CRMen><vrCRMen>650.00</vrCRMen></infoCRMen>
                  </infoIRRF>
                </evtIrrf>
              </eSocial>
            </evento>
            <recibo/>
          </retornoProcessamentoDownload>
        </eSocial>"""

        bx_s1299_wrapped = """<eSocial xmlns="http://www.esocial.gov.br/schema/download/retornoProcessamento/v1_0_0">
          <retornoProcessamentoDownload>
            <evento>
              <eSocial xmlns="http://www.esocial.gov.br/schema/evt/evtFechaEvPer/v_S_01_03_00">
                <evtFechaEvPer Id="ID1457913510000002026090208292200876">
                  <ideEvento><perApur>2026-10</perApur></ideEvento>
                  <ideEmpregador><tpInsc>1</tpInsc><nrInsc>12345678</nrInsc></ideEmpregador>
                  <infoFech><evtRemun>S</evtRemun><evtPgtos>S</evtPgtos></infoFech>
                </evtFechaEvPer>
              </eSocial>
            </evento>
            <recibo>
              <eSocial xmlns="http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0">
                <retornoEvento>
                  <recibo>
                    <nrRecibo>1.1.0000000043192698437</nrRecibo>
                  </recibo>
                </retornoEvento>
              </eSocial>
            </recibo>
          </retornoProcessamentoDownload>
        </eSocial>"""

        # Pack in a ZIP
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("S-5011.xml", bx_s5011_wrapped.encode("utf-8"))
            zf.writestr("S-5012.xml", bx_s5012_wrapped.encode("utf-8"))
            zf.writestr("S-1299.xml", bx_s1299_wrapped.encode("utf-8"))

        res = import_esocial_backup(buf.getvalue(), "esocial_bx.zip")
        self.assertEqual(res["count"], 1)
        self.assertEqual(res["competences"], ["2026-10"])

        c = MonthlyConsolidation.objects.get(month_year=date(2026, 10, 1))
        self.assertTrue(c.esocial_synced)
        self.assertEqual(c.actual_pro_labore_paid, Decimal("7000.00"))
        self.assertEqual(c.esocial_inss_tax, Decimal("770.00"))
        self.assertEqual(c.esocial_irrf_tax, Decimal("650.00"))
        self.assertEqual(c.esocial_s1299_recibo, "1.1.0000000043192698437")

    def test_import_only_s1299_does_not_mark_synced(self):
        from core.services.esocial_services import import_esocial_backup

        s1299_only = """<eSocial xmlns="http://www.esocial.gov.br/schema/download/retornoProcessamento/v1_0_0">
          <retornoProcessamentoDownload>
            <evento>
              <eSocial xmlns="http://www.esocial.gov.br/schema/evt/evtFechaEvPer/v_S_01_03_00">
                <evtFechaEvPer Id="ID1457913510000002026090208292200876">
                  <ideEvento><perApur>2026-11</perApur></ideEvento>
                  <ideEmpregador><tpInsc>1</tpInsc><nrInsc>12345678</nrInsc></ideEmpregador>
                  <infoFech><evtRemun>S</evtRemun><evtPgtos>S</evtPgtos></infoFech>
                </evtFechaEvPer>
              </eSocial>
            </evento>
            <recibo>
              <eSocial xmlns="http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0">
                <retornoEvento>
                  <recibo>
                    <nrRecibo>1.1.9999999999999999999</nrRecibo>
                  </recibo>
                </retornoEvento>
              </eSocial>
            </recibo>
          </retornoProcessamentoDownload>
        </eSocial>"""

        res = import_esocial_backup(s1299_only, "s1299_only.xml")
        self.assertEqual(res["count"], 0)
        self.assertEqual(res["competences"], [])
        self.assertIn("Nenhum evento totalizador", res["message"])

        c = MonthlyConsolidation.objects.get(month_year=date(2026, 11, 1))
        self.assertFalse(c.esocial_synced)
        self.assertEqual(c.actual_pro_labore_paid, Decimal("0.00"))
        self.assertEqual(c.esocial_s1299_recibo, "1.1.9999999999999999999")

    def test_import_rectified_events_out_of_order(self):
        import io
        import zipfile
        from core.services.esocial_services import import_esocial_backup

        # Initial closing event (earlier receipt 1.1.0000000010000000000 with 5000.00 payroll)
        s5011_initial = """<eSocial xmlns="http://www.esocial.gov.br/schema/evt/evtCS/v_S_01_03_00">
          <evtCS Id="ID0110000000000000000000010000000000">
            <ideEvento><perApur>2026-05</perApur></ideEvento>
            <ideEmpregador><tpInsc>1</tpInsc><nrInsc>12345678</nrInsc></ideEmpregador>
            <infoCS>
              <nrRecArqBase>1.1.0000000010000000000</nrRecArqBase>
              <indExistInfo>1</indExistInfo>
              <infoCPSeg><vrDescCP>550.00</vrDescCP></infoCPSeg>
              <ideEstab>
                <tpInsc>1</tpInsc><nrInsc>12345678000195</nrInsc>
                <ideLotacao>
                  <codLotacao>L1</codLotacao><fpas>515</fpas><codTercs>0000</codTercs>
                  <basesRemun><indIncid>1</indIncid><codCateg>722</codCateg><basesCp><vrBcCp00>5000.00</vrBcCp00></basesCp></basesRemun>
                </ideLotacao>
              </ideEstab>
            </infoCS>
          </evtCS>
        </eSocial>"""

        # Rectified closing event (later receipt 1.1.0000000020000000000 with 2000.00 payroll)
        s5011_rectified = """<eSocial xmlns="http://www.esocial.gov.br/schema/evt/evtCS/v_S_01_03_00">
          <evtCS Id="ID0110000000000000000000020000000000">
            <ideEvento><perApur>2026-05</perApur></ideEvento>
            <ideEmpregador><tpInsc>1</tpInsc><nrInsc>12345678</nrInsc></ideEmpregador>
            <infoCS>
              <nrRecArqBase>1.1.0000000020000000000</nrRecArqBase>
              <indExistInfo>1</indExistInfo>
              <infoCPSeg><vrDescCP>220.00</vrDescCP></infoCPSeg>
              <ideEstab>
                <tpInsc>1</tpInsc><nrInsc>12345678000195</nrInsc>
                <ideLotacao>
                  <codLotacao>L1</codLotacao><fpas>515</fpas><codTercs>0000</codTercs>
                  <basesRemun><indIncid>1</indIncid><codCateg>722</codCateg><basesCp><vrBcCp00>2000.00</vrBcCp00></basesCp></basesRemun>
                </ideLotacao>
              </ideEstab>
            </infoCS>
          </evtCS>
        </eSocial>"""

        # Case A: Put rectified first, older second inside the ZIP (out of order iteration)
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("event_01_rectified.xml", s5011_rectified.encode("utf-8"))
            zf.writestr("event_02_older_initial.xml", s5011_initial.encode("utf-8"))

        res = import_esocial_backup(buf.getvalue(), "rectification_test.zip")
        self.assertEqual(res["count"], 1)

        c = MonthlyConsolidation.objects.get(month_year=date(2026, 5, 1))
        # Must retain the rectified 2000.00 value and receipt ...20000000000, not the overwritten 5000.00!
        self.assertEqual(c.actual_pro_labore_paid, Decimal("2000.00"))
        self.assertEqual(c.esocial_inss_tax, Decimal("220.00"))
        self.assertEqual(c.esocial_s1299_recibo, "1.1.0000000020000000000")



