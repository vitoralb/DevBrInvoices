#!/usr/bin/env bash
set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$SCRIPT_DIR"

PROD_COMPOSE="docker-compose.yaml"
DEV_COMPOSE="docker-compose.dev.yaml"
PROD_PROJECT="notas"
DEV_PROJECT="notas-dev"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

check_dev_already_running() {
    local running_containers
    running_containers=$(docker ps --filter "name=notas-dev-" --filter "status=running" --format "{{.Names}}")
    if [ -n "$running_containers" ]; then
        log_error "A development environment is already running:"
        echo "$running_containers" | while read -r line; do
            echo -e "  - ${YELLOW}$line${NC}"
        done
        echo ""
        log_warn "Only ONE development environment is allowed to run at any time."
        log_info "To stop Dev containers: make dev-destroy (or ./scripts/env.sh destroy-dev)"
        log_info "To reset Dev environment: make dev-reset (or ./scripts/env.sh reset-dev)"
        log_info "To restart Dev containers: make dev-restart (or ./scripts/env.sh restart-dev)"
        return 1
    fi

    return 0
}

cmd_spawn_dev() {
    log_info "Starting development environment initialization..."

    if ! check_dev_already_running; then
        exit 1
    fi

    local is_resuming=false
    if [ -d "dev_data/postgres_data" ] && [ "$(ls -A dev_data/postgres_data 2>/dev/null)" ]; then
        is_resuming=true
    fi

    if [ "$is_resuming" = true ]; then
        log_info "Existing dev_data found. Resuming development environment..."
        docker compose -f "$DEV_COMPOSE" up -d

        log_info "Waiting for dev web container (notas-dev-web-1)..."
        sleep 3

        log_info "Applying any pending migrations in development..."
        docker exec notas-dev-web-1 python manage.py migrate --noinput

        log_info "Running incremental NSU import from Sefin Homologação..."
        docker exec notas-dev-web-1 python manage.py shell -c "
from core.services.nfse_services import import_nfses
try:
    count, msg = import_nfses('NACIONAL')
    print(f'Incremental sync: {count} items. {msg}')
except Exception as ex:
    print(f'Incremental sync notice: {ex}')
"
    else
        log_info "No existing dev_data found. Setting up clean-slate development environment..."

        # 1. Verify production database is running (needed to clone CompanySettings and User accounts)
        log_info "Checking if production database ('notas-db-1') is available..."
        if ! docker ps --filter "name=notas-db-1" --filter "status=running" --format "{{.Names}}" | grep -q "notas-db-1"; then
            log_error "Production database 'notas-db-1' is not running."
            log_info "Please ensure the production stack is up before cloning base configuration: docker compose up -d"
            exit 1
        fi

        # 2. Prepare isolated dev data directories
        log_info "Creating dev_data directories..."
        mkdir -p dev_data/postgres_data dev_data/media

        # 3. Clone media directory if available
        if [ -d "media" ]; then
            log_info "Copying media files to ./dev_data/media/..."
            cp -a media/. dev_data/media/ 2>/dev/null || true
        fi

        # 4. Start dev DB and redis
        log_info "Starting dev DB and Redis services..."
        docker compose -f "$DEV_COMPOSE" up -d db redis

        # 5. Wait for dev DB to become healthy
        log_info "Waiting for dev database to become ready..."
        local attempts=0
        local max_attempts=30
        until docker exec notas-dev-db-1 pg_isready -U notas -d notas >/dev/null 2>&1 || [ $attempts -ge $max_attempts ]; do
            attempts=$((attempts + 1))
            sleep 1
        done

        if [ $attempts -ge $max_attempts ]; then
            log_error "Dev database failed to start within 30 seconds."
            exit 1
        fi

        # 6. Start the rest of the dev stack
        log_info "Starting development web and celery containers on port 8081..."
        docker compose -f "$DEV_COMPOSE" up -d

        # 7. Wait for dev web container to be ready
        log_info "Waiting for dev web container (notas-dev-web-1)..."
        sleep 3

        # 8. Apply migrations in dev to build schema
        log_info "Applying migrations to initialize dev schema..."
        docker exec notas-dev-web-1 python manage.py migrate --noinput

        # 9. Copy only CompanySettings and User accounts from production
        log_info "Copying User accounts and auth tokens from production..."
        docker exec notas-db-1 pg_dump -U notas -d notas -t auth_user -t authtoken_token --data-only --column-inserts 2>/dev/null | docker exec -i notas-dev-db-1 psql -U notas -d notas >/dev/null 2>&1 || true

        log_info "Copying and sanitizing CompanySettings from production..."
        docker exec notas-web-1 python -c "
import django, os, json
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from core.models import CompanySettings
from django.forms.models import model_to_dict
c = CompanySettings.objects.first()
if c:
    d = model_to_dict(c)
    clean = {k: v for k, v in d.items() if k not in ['id', 'default_codigo_tributacao_nacional', 'default_codigo_nbs']}
    print(json.dumps(clean, default=str))
" 2>/dev/null | docker exec -i notas-dev-web-1 python manage.py shell -c "
import sys, json
from core.models import CompanySettings
raw = sys.stdin.read().strip()
if raw:
    data = json.loads(raw)
    c = CompanySettings.objects.first() or CompanySettings()
    for k, v in data.items():
        if hasattr(c, k):
            setattr(c, k, v)
    c.debug_mode = True
    c.auto_finalize_invoices = False
    c.document_series = '4242'
    c.next_document_number = 1
    c.last_adn_nsu = 0
    c.save()
    print('CompanySettings configured: series 4242, debug_mode=True, counters reset.')
else:
    print('Warning: No CompanySettings extracted from production.')
"

        # 10. Seed synthetic client and template if needed
        log_info "Seeding synthetic client and template..."
        docker exec notas-dev-web-1 python manage.py shell -c "
from core.models import Client, InvoiceTemplate

if not Client.objects.exists():
    client = Client.objects.create(
        name='Acme International LLC',
        email='billing@example.com',
        address_line1='100 Market St',
        address_neighborhood='Downtown',
        address_city='San Francisco',
        address_state_province='CA',
        address_postal_code='94105',
        country='United States',
        address_country_code='US',
    )
    print('Created synthetic test client: Acme International LLC.')
else:
    client = Client.objects.first()

if not InvoiceTemplate.objects.exists():
    from core.models import InvoiceTemplateItem
    tmpl = InvoiceTemplate.objects.create(
        name='Template Padrão Homologação',
        currency='USD',
        codigo_tributacao_nacional='010101',
        codigo_servico_municipio='0101',
        codigo_nbs='101010100',
        nfse_description='Serviços de desenvolvimento de software prestados para o exterior.',
    )
    InvoiceTemplateItem.objects.create(
        template=tmpl,
        description='Consultoria e desenvolvimento de software',
        quantity=1,
        unit_price_foreign=1000,
    )
    print('Created synthetic test template.')
"

        # 11. Run automatic NSU import from Sefin Homologação
        log_info "Running initial NSU import from Sefin Homologação to prefill NFS-e data..."
        docker exec notas-dev-web-1 python manage.py shell -c "
from core.services.nfse_services import import_nfses
try:
    count, msg = import_nfses('NACIONAL')
    print(f'Homologação prefill: {count} items processed. {msg}')
except Exception as ex:
    print(f'Homologação prefill notice: {ex}')
"
    fi

    log_success "Development environment ready!"
    echo ""
    echo -e "  ${GREEN}URL:${NC}                http://localhost:8081"
    echo -e "  ${GREEN}Container Web:${NC}      notas-dev-web-1"
    echo -e "  ${GREEN}Dev Database:${NC}       ./dev_data/postgres_data (isolated from prod)"
    echo -e "  ${GREEN}Dev Media:${NC}          ./dev_data/media (isolated from prod)"
    echo -e "  ${GREEN}Series / State:${NC}     document_series=4242, Homologação NFS-es prefilled"
    echo -e "  ${GREEN}Code Reload:${NC}        Live bind-mount of current workspace"
    echo -e "  ${GREEN}Safety Rails:${NC}       debug_mode=True (locked), auto_finalize_invoices=False"
    echo ""
    log_info "To run tests in dev: make dev-test (or ./scripts/env.sh test)"
    log_info "To stop dev (preserves data): make dev-destroy (or ./scripts/env.sh destroy-dev)"
    log_info "To wipe and reset dev from scratch: make dev-reset (or ./scripts/env.sh reset-dev)"
}

cmd_destroy_dev() {
    log_info "Stopping development environment containers..."
    docker compose -f "$DEV_COMPOSE" down --remove-orphans || true
    log_success "Development containers stopped. Dev database (./dev_data/) preserved."
    log_info "To resume, run 'make dev-spawn'. To completely reset dev database, run 'make dev-reset'."
}

cmd_reset_dev() {
    log_info "Wiping development environment and data..."
    docker compose -f "$DEV_COMPOSE" down -v --remove-orphans || true
    rm -rf dev_data
    log_success "Development data wiped."
    log_info "Re-spawning clean development environment..."
    cmd_spawn_dev
}

cmd_restart_dev() {
    log_info "Restarting development web and celery workers..."
    if ! docker ps --filter "name=notas-dev-web-1" --format "{{.Names}}" | grep -q "notas-dev-web-1"; then
        log_error "Dev environment is not running. Use 'make dev-spawn' or './scripts/env.sh spawn-dev' first."
        exit 1
    fi
    docker restart notas-dev-web-1 notas-dev-celery-worker-1 notas-dev-celery-beat-1
    log_success "Dev services restarted."
}

cmd_test() {
    if ! docker ps --filter "name=notas-dev-web-1" --format "{{.Names}}" | grep -q "notas-dev-web-1"; then
        log_error "Tests must ALWAYS be executed inside the development environment (notas-dev-web-1)."
        log_error "The development environment is currently NOT running."
        echo ""
        log_info "Please run 'make dev-spawn' (or ./scripts/env.sh spawn-dev) before running tests."
        exit 1
    fi

    log_info "Running test suite inside development container (notas-dev-web-1)..."
    docker exec notas-dev-web-1 python manage.py test --noinput "$@"
}

cmd_upgrade_prod() {
    log_info "Initiating production upgrade..."

    # Check Git status
    local branch
    branch=$(git rev-parse --abbrev-ref HEAD)
    if [ "$branch" != "master" ] && [ "$branch" != "main" ]; then
        log_warn "You are currently on branch '${branch}', not 'master' or 'main'."
        read -r -p "Are you sure you want to build and deploy production from '${branch}'? [y/N] " confirm
        if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
            log_info "Upgrade aborted."
            exit 0
        fi
    fi

    if ! git diff-index --quiet HEAD --; then
        log_error "Working tree has uncommitted changes. Please commit or stash changes before upgrading production."
        exit 1
    fi

    log_info "Building production Docker image from current repository state..."
    docker compose -f "$PROD_COMPOSE" build

    log_info "Recreating production containers..."
    docker compose -f "$PROD_COMPOSE" up -d

    log_info "Running migrations on production database..."
    docker exec notas-web-1 python manage.py migrate --noinput

    log_info "Collecting static files on production..."
    docker exec notas-web-1 python manage.py collectstatic --noinput

    log_success "Production upgrade completed successfully!"
}

cmd_status() {
    echo -e "${BLUE}=== Production Environment (project: ${PROD_PROJECT}) ===${NC}"
    docker compose -f "$PROD_COMPOSE" ps
    echo ""
    echo -e "${BLUE}=== Development Environment (project: ${DEV_PROJECT}) ===${NC}"
    if docker ps -a --filter "name=notas-dev-" --format "{{.Names}}" | grep -q "notas-dev"; then
        docker compose -f "$DEV_COMPOSE" ps
    else
        echo "No development containers are currently created or running."
    fi
}

case "$1" in
    spawn-dev)
        cmd_spawn_dev
        ;;
    destroy-dev)
        cmd_destroy_dev
        ;;
    reset-dev)
        cmd_reset_dev
        ;;
    restart-dev)
        cmd_restart_dev
        ;;
    test)
        shift
        cmd_test "$@"
        ;;
    upgrade-prod)
        cmd_upgrade_prod
        ;;
    status)
        cmd_status
        ;;
    *)
        echo "Usage: $0 {spawn-dev|destroy-dev|reset-dev|restart-dev|test|upgrade-prod|status}"
        exit 1
        ;;
esac

