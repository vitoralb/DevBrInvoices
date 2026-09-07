# DevBrInvoices

Uma aplicação Django para gerenciamento de invoices de serviços para o exterior, automação de emissão de Nota Fiscal de Serviços Eletrônica e cálculo de obrigações tributárias do Simples Nacional (Anexo III vs Anexo V, Fator R, e projeções de Pró-labore ideal).

> ⚠️ **ISENÇÃO DE RESPONSABILIDADE (DISCLAIMER): USO POR SUA CONTA E RISCO**
> Este software é fornecido "no estado em que se encontra" (*as is*), sem garantias de qualquer tipo, expressas ou implícitas. O autor não se responsabiliza por perdas financeiras, multas, cálculos incorretos de impostos, vazamento de dados ou qualquer outro dano decorrente do uso deste sistema. Esta aplicação **não substitui um profissional contábil**. Consulte sempre o seu contador antes de realizar quaisquer registros financeiros, emitir notas fiscais ou recolher impostos baseados nos dados gerados por este sistema.
>
> 🔒 **Aviso de Segurança:** Embora as melhores práticas de segurança tenham sido consideradas durante o desenvolvimento, é fortemente recomendado que você execute este sistema **apenas localmente em um ambiente seguro** e **não o exponha à internet pública**, visto que ele lida com certificados digitais, dados financeiros e informações sensíveis de clientes.

**Aviso:** Este projeto é restrito (pelo menos inicialmente) a exportadores de serviços optantes exclusivamente pelo Simples Nacional. Além disso, no momento, apenas os emissores da Prefeitura de São Paulo e o Emissor Nacional são suportados.

**Contexto do Projeto:** Este sistema foi desenvolvido principalmente para atender às minhas próprias necessidades. Por conta disso, algumas premissas e regras de negócio foram fixadas no código (hardcoded) focando no meu caso de uso específico, o que provavelmente não refletirá a realidade de todos. Além disso, a maior parte deste projeto foi gerada através de *vibe-coding*. Sinta-se à vontade para fazer um fork e adaptar à sua realidade!

## Principais Features e Decisões de Design (Code Highlights)

- **Backend em Django & HTMX:** Escolhidos para fornecer um painel seguro e interações de frontend dinâmicas sem a complexidade de manter uma Single Page Application.
- **Assinatura de Notas Fiscais Integrada:** O código realiza as assinaturas XML do padrão ABRASF localmente (usando o certificado A1 embutido `.pfx`) através das bibliotecas `cryptography` e `signxml`, removendo a dependência de serviços externos caros de mensageria e emissão.
- **Integração SOAP e REST:** Lida com as idiossincrasias das prefeituras construindo envelopes SOAP manualmente e utilizando a biblioteca `xsdata` para parsing XML (Prefeitura SP), além de clientes HTTP RESTful tradicionais para o Emissor Nacional.
- **Trabalhadores Assíncronos (Celery):** Processamento em background fundamental para não bloquear a interface do usuário durante a comunicação muitas vezes instável com as APIs de emissão ou com a API do BCB (Banco Central).
- **WeasyPrint para PDFs:** Geração nativa (sem depender de APIs externas) e em alta qualidade de PDFs das invoices enviadas aos clientes estrangeiros.

## Arquitetura & Stack Tecnológica

- **Backend:** Python 3.12, Django 6.1 (com `django-htmx` para interações dinâmicas)
- **Banco de Dados:** PostgreSQL 16
- **Tarefas Assíncronas:** Celery 5.6, Redis 7+
- **Geração de PDF:** WeasyPrint
- **Integrações Fiscais:** Clientes REST (Emissor Nacional) e SOAP (Prefeitura de São Paulo) para NFS-e com assinatura via certificado digital (A1 PKCS#12 / PFX) usando `cryptography` e `signxml`

## Começando

### 1. Pré-requisitos
- Docker e Docker Compose instalados.

### 2. Configuração do Ambiente
Copie o arquivo de ambiente de exemplo e configure suas credenciais:
```bash
cp .env.example .env
```
Preencha as variáveis de configuração no `.env`:
- `SECRET_KEY`: Chave secreta segura e aleatória para o Django.
- `DEBUG`: Defina como `False` para produção.
- `ALLOWED_HOSTS`: Nomes de domínio ou endereços IP.
- `POSTGRES_*`: Credenciais do banco de dados (nome, usuário, senha, host, porta).
- `CELERY_BROKER_URL`: URL de conexão com o Redis.

### 3. Executando com Docker Compose
Construa e inicie todos os serviços (PostgreSQL, Redis, Web, Celery Worker, Celery Beat):
```bash
docker compose up -d --build
```

### 4. Migrações do Banco de Dados
Aplique as migrações do banco de dados:
```bash
docker compose exec web python manage.py migrate
```

### 5. Criar Superusuário & Configuração da Empresa
Crie uma conta de administrador:
```bash
docker compose exec web python manage.py createsuperuser
```
Acesse a aplicação em `http://localhost:8080/` e defina os detalhes de **Sua Empresa** (Company Settings), como dados cadastrais, informações bancárias e série/número de RPS a ser utilizado.

### 6. Coletar Arquivos Estáticos (Produção)
```bash
docker compose exec web python manage.py collectstatic --no-input
```

## Executando Testes
Rode a suíte de testes dentro do container web:
```bash
docker compose exec web python manage.py test core -v2
```

## Lógica de Negócio Principal

- **Simples Nacional & Fator R:** O sistema calcula dinamicamente o faturamento dos últimos 12 meses (RBT12) e a folha de pagamento (Pró-labore + CPP, quando aplicável) para determinar se a empresa se qualifica para o Anexo III (Fator R >= 28%) ou Anexo V.
- **Projeção de Pró-labore Ideal:** Calcula o pró-labore mínimo exato necessário para o mês atual, a fim de manter o Fator R igual ou superior a 28%.
- **Faturamento Automático:** O Celery beat roda periodicamente para finalizar invoices nas datas de emissão agendadas, enviá-la para o cliente, obter taxas de câmbio diárias através da API do Banco Central do Brasil (BCB) e transmitir automaticamente a NFS-e para a Prefeitura de São Paulo ou Emissor Nacional.
