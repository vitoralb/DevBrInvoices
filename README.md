# DevBrInvoices

Uma aplicação Django para gerenciamento de invoices de serviços para o exterior, automação de emissão de Nota Fiscal de Serviços Eletrônica e cálculo de obrigações tributárias do Simples Nacional (Anexo III vs Anexo V, Fator R, e projeções de Pró-labore ideal).

> ⚠️ **ISENÇÃO DE RESPONSABILIDADE (DISCLAIMER): USO POR SUA CONTA E RISCO**
> Este software é fornecido "no estado em que se encontra" (*as is*), sem garantias de qualquer tipo, expressas ou implícitas. O autor não se responsabiliza por perdas financeiras, multas, cálculos incorretos de impostos, vazamento de dados ou qualquer outro dano decorrente do uso deste sistema. Esta aplicação **não substitui um profissional contábil**. Consulte sempre o seu contador antes de realizar quaisquer registros financeiros, emitir notas fiscais ou recolher impostos baseados nos dados gerados por este sistema.
>
> 🔒 **Aviso de Segurança:** Embora as melhores práticas de segurança tenham sido consideradas durante o desenvolvimento, é fortemente recomendado que você execute este sistema **apenas localmente em um ambiente seguro** e **não o exponha à internet pública**, visto que ele lida com certificados digitais, dados financeiros e informações sensíveis de clientes.

**Aviso:** Este projeto é restrito (pelo menos inicialmente) a exportadores de serviços optantes exclusivamente pelo Simples Nacional. Além disso, no momento, apenas os emissores da Prefeitura de São Paulo e o Emissor Nacional são suportados.

**Contexto do Projeto:** Este sistema foi desenvolvido principalmente para atender às minhas próprias necessidades. Por conta disso, algumas premissas e regras de negócio foram fixadas no código (hardcoded) focando no meu caso de uso específico, o que provavelmente não refletirá a realidade de todos. Além disso, a maior parte deste projeto foi gerada através de *vibe-coding*. Sinta-se à vontade para fazer um fork e adaptar à sua realidade!

## Principais Features e Decisões de Design (Code Highlights)

- **Backend em Django & HTMX:** Painel seguro e interações de frontend dinâmicas sem a complexidade de manter uma Single Page Application.
- **Assinatura de Notas Fiscais Integrada:** Assinaturas XML do padrão ABRASF localmente (usando o certificado A1 embutido `.pfx`) através das bibliotecas `cryptography` e `signxml`, removendo a dependência de serviços externos caros de mensageria.
- **Integração SOAP e REST:** Lida com as prefeituras construindo envelopes SOAP manualmente e utilizando a biblioteca `xsdata` para parsing XML (Prefeitura SP), além de clientes HTTP RESTful tradicionais para o Emissor Nacional.
- **Trabalhadores Assíncronos (Celery):** Processamento em background fundamental para não bloquear a interface do usuário durante a comunicação com as APIs de emissão ou com a API do BCB (Banco Central).
- **WeasyPrint para PDFs:** Geração nativa (sem depender de APIs externas) e em alta qualidade de PDFs das invoices enviadas aos clientes estrangeiros.
- **Ambientes Isolados de Produção e Desenvolvimento:** Produção roda a partir de imagens imutáveis (imune a edições de código durante o desenvolvimento). O ambiente de desenvolvimento pode ser criado sob demanda com dados reais clonados, travas estritas de segurança em modo debug e destruído após o término.

## Arquitetura & Stack Tecnológica

- **Backend:** Python 3.12, Django 6.1 (com `django-htmx` para interações dinâmicas)
- **Banco de Dados:** PostgreSQL 16
- **Tarefas Assíncronas:** Celery 5.6, Redis 7+
- **Geração de PDF:** WeasyPrint
- **Integrações Fiscais:** Clientes REST (Emissor Nacional) e SOAP (Prefeitura de São Paulo) para NFS-e com assinatura via certificado digital (A1 PKCS#12 / PFX) usando `cryptography` e `signxml`

---

## Começando em Produção

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

### 3. Executando Produção com Docker Compose
Construa e inicie todos os serviços de produção (PostgreSQL, Redis, Web, Celery Worker, Celery Beat):
```bash
docker compose up -d --build
```
A produção será disponibilizada na porta **8080** (`http://localhost:8080`).

### 4. Migrações do Banco de Dados
Aplique as migrações no container de produção:
```bash
docker exec notas-web-1 python manage.py migrate --noinput
```

### 5. Criar Superusuário & Configuração da Empresa
Crie uma conta de administrador:
```bash
docker exec -it notas-web-1 python manage.py createsuperuser
```
Acesse a aplicação em `http://localhost:8080/` e configure **Sua Empresa** (Company Settings), como dados cadastrais, informações bancárias e série/número de RPS.

### 6. Coletar Arquivos Estáticos (Produção)
```bash
docker exec notas-web-1 python manage.py collectstatic --noinput
```

---

## Fluxo de Desenvolvimento (Dev vs Prod)

Para desenvolver novas funcionalidades sem riscos para o ambiente de produção nem poluição de arquivos reais, utilize o fluxo de desenvolvimento isolado via `Makefile`:

### 1. Criar ou Retomar um Ambiente de Desenvolvimento (Dev)
Gera ou retoma uma stack de desenvolvimento completa (`notas-dev`) na porta **8081**:
```bash
make dev-spawn
```
- **Inicialização Clean Slate (Primeiro Spawn):** Se `./dev_data/` não existir, o script cria uma base limpa de desenvolvimento, copiando exclusivamente as configurações (`CompanySettings`) e usuários (`auth_user`) de produção. Contadores são zerados (`next_document_number=1`, `last_adn_nsu=0`), a série de documentos é fixada em `"4242"`, um cliente de teste sintético e template de invoice são criados, e um processo de importação automática de NFS-es e eventos de Homologação é executado via API de Distribuição ADN do Sefin Nacional.
- **Retomada de Ambiente:** Se `./dev_data/` já existir, os containers existentes são iniciados, migrações pendentes são aplicadas e uma consulta incremental de novos eventos/NFS-es no ADN é disparada.
- **Live Reload:** O diretório do projeto `.:/app` é montado em tempo real no container de desenvolvimento.
- **Travas de Segurança:** `debug_mode` é travado em `True`, `document_series` em `"4242"`, `auto_finalize_invoices` é desativado para evitar disparos acidentais, todos os e-mails são redirecionados para e-mail interno/debug e as emissões de NFS-e são direcionadas para endpoints de teste/homologação (Sefin Nacional Produção Restrita `tpAmb=2` ou Paulistana `TesteEnvioLoteRPS`).
- **Regra de Instância Única:** Apenas **um** ambiente de desenvolvimento pode estar ativo por vez.

### 2. Executar a Suíte de Testes
Os testes devem ser executados **obrigatoriamente** no ambiente de desenvolvimento:
```bash
make dev-test
# ou simplesmente:
make test
# ou testes específicos:
make dev-test ARGS="core.tests.test_models"
```
*O test runner isola automaticamente o diretório de mídia em uma pasta temporária que é excluída ao final dos testes, garantindo que nenhum PDF ou XML fictício de teste permaneça no disco.*

### 3. Reiniciar os Workers no Desenvolvimento
Caso altere tarefas Celery, configurações ou models:
```bash
make dev-restart
```

### 4. Parar o Ambiente de Desenvolvimento (Preservando Dados)
Para pausar o desenvolvimento e liberar memória e CPU:
```bash
make dev-destroy
```
Isso interrompe e remove os containers de desenvolvimento, mas **preserva** a pasta `./dev_data/` intacta, permitindo retomar instantaneamente depois via `make dev-spawn` sem precisar reimportar o histórico do Sefin.

### 5. Reinicializar o Ambiente de Desenvolvimento (Clean Slate)
Caso deseje resetar completamente o banco de dados de desenvolvimento para o estado inicial:
```bash
make dev-reset
```
Isso interrompe os containers, apaga a pasta `./dev_data/` e recria um ambiente limpo com as travas e importação inicial do Sefin Homologação.

### 6. Atualizar a Produção
Após finalizar a funcionalidade, testar em Dev e mesclar o código na branch principal (`master`):
```bash
make prod-upgrade
```
O comando reconstrói a imagem Docker de produção, recria os containers de produção e executa as migrações pendentes e `collectstatic`.

### 7. Verificar o Status dos Ambientes
```bash
make status
```

---

## Lógica de Negócio Principal

- **Simples Nacional & Fator R:** O sistema calcula dinamicamente o faturamento dos últimos 12 meses (RBT12) e a folha de pagamento (Pró-labore + CPP, quando aplicável) para determinar se a empresa se qualifica para o Anexo III (Fator R >= 28%) ou Anexo V.
- **Projeção de Pró-labore Ideal:** Calcula o pró-labore mínimo exato necessário para o mês atual, a fim de manter o Fator R igual ou superior a 28%.
- **Faturamento Automático:** O Celery beat roda periodicamente para finalizar invoices nas datas de emissão agendadas, enviá-la para o cliente, obter taxas de câmbio diárias através da API do Banco Central do Brasil (BCB) e transmitir automaticamente a NFS-e para a Prefeitura de São Paulo ou Emissor Nacional.
