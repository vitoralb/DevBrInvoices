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
    running_containers=$(docker ps -a --filter "name=notas-dev-" --format "{{.Names}}")
    if [ -n "$running_containers" ]; then
        log_error "A development environment is already present or running:"
        echo "$running_containers" | while read -r line; do
            echo -e "  - ${YELLOW}$line${NC}"
        done
        echo ""
        log_warn "Only ONE development environment is allowed at any time."
        log_info "To destroy the existing Dev environment before re-spawning: make dev-destroy (or ./scripts/env.sh destroy-dev)"
        log_info "To restart the existing Dev environment: make dev-restart (or ./scripts/env.sh restart-dev)"
        return 1
    fi

    if [ -d "dev_data" ] && [ "$(ls -A dev_data 2>/dev/null)" ]; then
        log_error "Found existing dev_data directory from a previous session."
        log_warn "Run './scripts/env.sh destroy-dev' first to clean up leftover dev state before spawning a new one."
        return 1
    fi

    return 0
}

cmd_spawn_dev() {
    log_info "Starting development environment initialization..."

    if ! check_dev_already_running; then
        exit 1
    fi

    # 1. Verify production database is running
    log_info "Checking if production database ('notas-db-1') is available..."
    if ! docker ps --filter "name=notas-db-1" --filter "status=running" --format "{{.Names}}" | grep -q "notas-db-1"; then
        log_error "Production database 'notas-db-1' is not running."
        log_info "Please ensure the production stack is up before cloning state: docker compose up -d"
        exit 1
    fi

    # 2. Prepare isolated dev data directories
    log_info "Creating dev_data directories..."
    mkdir -p dev_data/postgres_data dev_data/media

    # 3. Start dev DB and redis
    log_info "Starting dev DB and Redis services..."
    docker compose -f "$DEV_COMPOSE" up -d db redis

    # 4. Wait for dev DB to become healthy
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

    # 5. Clone database from prod to dev
    log_info "Cloning database from production (notas-db-1) to development (notas-dev-db-1)..."
    docker exec notas-db-1 pg_dump -U notas -d notas --clean --if-exists | docker exec -i notas-dev-db-1 psql -U notas -d notas >/dev/null

    # 6. Clone media directory
    log_info "Cloning media files to ./dev_data/media/..."
    if [ -d "media" ]; then
        cp -a media/. dev_data/media/
    fi

    # 7. Start the rest of the dev stack (web, celery-worker, celery-beat)
    log_info "Starting development web and celery containers on port 8081..."
    docker compose -f "$DEV_COMPOSE" up -d

    # 8. Wait for dev web container to be ready
    log_info "Waiting for dev web container (notas-dev-web-1)..."
    sleep 3

    # 9. Apply migrations in dev
    log_info "Applying any pending migrations in development..."
    docker exec notas-dev-web-1 python manage.py migrate --noinput

    # 10. Sanitize Dev settings (enforce debug_mode=True, auto_finalize_invoices=False)
    log_info "Sanitizing development CompanySettings (enforcing debug_mode=True, auto_finalize_invoices=False)..."
    docker exec notas-dev-web-1 python manage.py shell -c "
from core.models import CompanySettings
c = CompanySettings.load()
if c:
    c.debug_mode = True
    c.auto_finalize_invoices = False
    c.save()
    print('CompanySettings sanitized successfully in Dev DB.')
else:
    print('No CompanySettings found to sanitize.')
"

    log_success "Development environment spawned successfully!"
    echo ""
    echo -e "  ${GREEN}URL:${NC}                http://localhost:8081"
    echo -e "  ${GREEN}Container Web:${NC}      notas-dev-web-1"
    echo -e "  ${GREEN}Dev Database:${NC}       ./dev_data/postgres_data (isolated from prod)"
    echo -e "  ${GREEN}Dev Media:${NC}          ./dev_data/media (isolated from prod)"
    echo -e "  ${GREEN}Code Reload:${NC}        Live bind-mount of current workspace"
    echo -e "  ${GREEN}Safety Rails:${NC}       debug_mode=True (locked), auto_finalize_invoices=False"
    echo ""
    log_info "To run tests in dev: make dev-test (or ./scripts/env.sh test)"
    log_info "To destroy dev when finished: make dev-destroy (or ./scripts/env.sh destroy-dev)"
}

cmd_destroy_dev() {
    log_info "Stopping and removing development environment containers and volumes..."
    docker compose -f "$DEV_COMPOSE" down -v --remove-orphans || true

    log_info "Removing dev_data directory..."
    rm -rf dev_data

    log_success "Development environment has been completely destroyed."
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
        echo "Usage: $0 {spawn-dev|destroy-dev|restart-dev|test|upgrade-prod|status}"
        exit 1
        ;;
esac

