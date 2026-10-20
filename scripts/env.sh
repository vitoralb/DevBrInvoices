#!/usr/bin/env bash
set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$SCRIPT_DIR"

PROD_COMPOSE="docker-compose.yaml"
DEV_COMPOSE="docker-compose.dev.yaml"
DEV_BIND_COMPOSE="docker-compose.dev.bind.yaml"
PROD_PROJECT="notas"

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

get_running_dev_ports() {
    docker ps --filter "name=notas-dev-" --filter "name=-web-1" --filter "status=running" --format "{{.Names}}" 2>/dev/null \
        | sed -E 's/.*notas-dev-([0-9]+)-web-1.*/\1/' \
        | grep -E '^[0-9]+$' \
        | sort -u
}

get_all_dev_ports() {
    docker ps -a --filter "name=notas-dev-" --filter "name=-web-1" --format "{{.Names}}" 2>/dev/null \
        | sed -E 's/.*notas-dev-([0-9]+)-web-1.*/\1/' \
        | grep -E '^[0-9]+$' \
        | sort -u
}

resolve_dev_port() {
    local requested_port="$1"
    local silent_if_none="${2:-false}"
    if [ -n "$requested_port" ]; then
        echo "$requested_port"
        return 0
    fi

    local running_ports
    mapfile -t running_ports < <(get_running_dev_ports)

    # Filter out empty entries if any
    local non_empty_ports=()
    for p in "${running_ports[@]}"; do
        if [ -n "$p" ]; then
            non_empty_ports+=("$p")
        fi
    done

    local count=${#non_empty_ports[@]}
    if [ "$count" -eq 1 ]; then
        log_info "Auto-detected single running dev environment on port ${non_empty_ports[0]}." >&2
        echo "${non_empty_ports[0]}"
        return 0
    elif [ "$count" -gt 1 ]; then
        log_error "Multiple development environments are currently running:" >&2
        for p in "${non_empty_ports[@]}"; do
            echo -e "  - Port ${YELLOW}${p}${NC} (project: notas-dev-${p})" >&2
        done
        echo "" >&2
        log_warn "Please specify which environment to target using PORT=<port> (e.g. PORT=8081)" >&2
        return 1
    else
        if [ "$silent_if_none" != "true" ]; then
            log_error "No running development environment was detected." >&2
            log_info "Please spawn an environment first: make dev-spawn (or specify PORT=<port>)" >&2
        fi
        return 2
    fi
}

cmd_spawn_dev() {
    local target_port="${PORT:-8081}"
    local ref="${REF:-}"
    local bind="${BIND:-}"

    if [ -n "$ref" ]; then
        if [ -z "$bind" ]; then
            bind=0
        fi
    else
        if [ -z "$bind" ]; then
            bind=1
        fi
    fi

    local project="notas-dev-${target_port}"
    local data_dir="./dev_data_${target_port}"
    local image="notas-dev:${target_port}"

    log_info "Starting development environment initialization for port ${target_port}..."

    # Check if this specific dev environment is already running
    if docker ps --filter "name=${project}-web-1" --filter "status=running" --format "{{.Names}}" | grep -q "${project}-web-1"; then
        log_warn "Development environment on port ${target_port} is already running."
        echo -e "  ${GREEN}URL:${NC} http://localhost:${target_port}"
        echo -e "  ${GREEN}Web Container:${NC} ${project}-web-1"
        return 0
    fi

    # Reference mode: build image from git archive of the ref
    if [ -n "$ref" ]; then
        log_info "Reference mode requested for ref '${ref}' on port ${target_port} (BIND=${bind})..."
        if ! git rev-parse --verify "${ref}^{commit}" >/dev/null 2>&1; then
            log_error "Git ref '${ref}' not found."
            exit 1
        fi

        if ! docker image inspect notas-web:latest >/dev/null 2>&1; then
            log_info "Base image notas-web:latest not found. Building base production image first..."
            docker compose -f "$PROD_COMPOSE" build
        fi

        log_info "Packaging git archive of ref '${ref}' and building image ${image}..."
        local tmpdir
        tmpdir=$(mktemp -d)
        git archive "${ref}" | tar -x -C "$tmpdir"
        cat << 'EOF' > "$tmpdir/Dockerfile"
FROM notas-web:latest
WORKDIR /app
RUN rm -rf /app/*
COPY . /app/
RUN SECRET_KEY=build-temp-key python manage.py collectstatic --noinput
EOF
        docker build -t "$image" "$tmpdir"
        rm -rf "$tmpdir"
        log_success "Image ${image} built from git ref '${ref}'."
    else
        # Active work mode: tag notas-web:latest if notas-dev:<port> does not exist
        if ! docker image inspect "$image" >/dev/null 2>&1; then
            if docker image inspect notas-web:latest >/dev/null 2>&1; then
                docker tag notas-web:latest "$image"
            else
                log_info "Building base image for development..."
                docker compose -f "$PROD_COMPOSE" build
                docker tag notas-web:latest "$image"
            fi
        fi
    fi

    local compose_args=("-p" "$project" "-f" "$DEV_COMPOSE")
    if [ "$bind" = "1" ]; then
        compose_args+=("-f" "$DEV_BIND_COMPOSE")
    fi

    run_dev_compose() {
        DEV_PROJECT_NAME="$project" DEV_PORT="$target_port" DEV_DATA_DIR="$data_dir" DEV_IMAGE="$image" \
            docker compose "${compose_args[@]}" "$@"
    }

    local is_resuming=false
    if [ -d "${data_dir}/postgres_data" ] && [ "$(ls -A "${data_dir}/postgres_data" 2>/dev/null)" ]; then
        is_resuming=true
    fi

    if [ "$is_resuming" = true ]; then
        log_info "Existing data found at ${data_dir}. Resuming development environment..."
        run_dev_compose up -d

        log_info "Waiting for dev web container (${project}-web-1)..."
        local attempts=0
        until docker ps --filter "name=${project}-web-1" --filter "status=running" --format "{{.Names}}" | grep -q "${project}-web-1" || [ $attempts -ge 30 ]; do
            attempts=$((attempts + 1))
            sleep 1
        done

        log_info "Applying any pending migrations in development..."
        docker exec "${project}-web-1" python manage.py migrate --noinput
    else
        log_info "No existing data found at ${data_dir}. Setting up clean-slate development environment..."

        # Prepare isolated dev data directories
        mkdir -p "${data_dir}/postgres_data" "${data_dir}/media"

        # Start dev DB and redis
        log_info "Starting dev DB and Redis services..."
        run_dev_compose up -d db redis

        # Wait for dev DB to become healthy
        log_info "Waiting for dev database to become ready..."
        local attempts=0
        local max_attempts=30
        until docker exec "${project}-db-1" pg_isready -U notas -d notas >/dev/null 2>&1 || [ $attempts -ge $max_attempts ]; do
            attempts=$((attempts + 1))
            sleep 1
        done

        if [ $attempts -ge $max_attempts ]; then
            log_error "Dev database failed to start within 30 seconds."
            exit 1
        fi

        # Start the rest of the dev stack
        log_info "Starting development web and celery containers on port ${target_port}..."
        run_dev_compose up -d

        # Wait for dev web container to be ready
        log_info "Waiting for dev web container (${project}-web-1)..."
        attempts=0
        until docker ps --filter "name=${project}-web-1" --filter "status=running" --format "{{.Names}}" | grep -q "${project}-web-1" || [ $attempts -ge 30 ]; do
            attempts=$((attempts + 1))
            sleep 1
        done

        # Apply migrations to build schema
        log_info "Applying migrations to initialize dev schema..."
        docker exec "${project}-web-1" python manage.py migrate --noinput

        # Create default superuser admin / admin
        log_info "Creating default superuser (admin / admin)..."
        docker exec "${project}-web-1" python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin')
    print('Superuser admin created.')
"
    fi

    log_success "Development environment ready!"
    echo ""
    echo -e "  ${GREEN}URL:${NC}                http://localhost:${target_port}"
    echo -e "  ${GREEN}Container Web:${NC}      ${project}-web-1"
    echo -e "  ${GREEN}Dev Database:${NC}       ${data_dir}/postgres_data (isolated from prod)"
    echo -e "  ${GREEN}Dev Media:${NC}          ${data_dir}/media (isolated from prod)"
    echo -e "  ${GREEN}Mode:${NC}               $([ "$bind" = "1" ] && echo "Active work (live reload, BIND=1)" || echo "Reference mode (immutable, BIND=0, ref=${ref})")"
    echo -e "  ${GREEN}Safety Rails:${NC}       debug_mode=True (locked), document_series=4242 (locked)"
    echo ""
    log_info "To run tests in dev: make dev-test PORT=${target_port} (or make dev-test)"
    log_info "To clone prod DB/media: make dev-clone-prod PORT=${target_port}"
    log_info "To stop dev (preserves data): make dev-destroy PORT=${target_port}"
    log_info "To wipe and reset dev: make dev-reset PORT=${target_port}"
}

cmd_destroy_dev() {
    local target_port="$PORT"
    if [ -z "$target_port" ]; then
        local err_code=0
        target_port=$(resolve_dev_port "" "true") || err_code=$?
        if [ $err_code -eq 1 ]; then
            exit 1
        elif [ $err_code -eq 2 ]; then
            local stopped_ports=()
            local all_ports
            mapfile -t all_ports < <(get_all_dev_ports)
            for p in "${all_ports[@]}"; do
                if [ -n "$p" ]; then stopped_ports+=("$p"); fi
            done

            if [ ${#stopped_ports[@]} -eq 1 ]; then
                target_port="${stopped_ports[0]}"
                log_info "Auto-detected stopped dev environment on port ${target_port}."
            elif [ ${#stopped_ports[@]} -gt 1 ]; then
                log_error "Multiple stopped development environments exist:" >&2
                for p in "${stopped_ports[@]}"; do
                    echo -e "  - Port ${YELLOW}${p}${NC} (project: notas-dev-${p})" >&2
                done
                echo "" >&2
                log_warn "Please specify which environment to destroy using PORT=<port> (e.g. PORT=8081)" >&2
                exit 1
            else
                log_info "No active or stopped development environments found."
                return 0
            fi
        fi
    fi

    local project="notas-dev-${target_port}"
    local data_dir="./dev_data_${target_port}"

    log_info "Stopping development environment containers for port ${target_port}..."
    DEV_PROJECT_NAME="$project" DEV_PORT="$target_port" DEV_DATA_DIR="$data_dir" \
        docker compose -p "$project" -f "$DEV_COMPOSE" down --remove-orphans || true
    log_success "Development containers for port ${target_port} stopped. Dev data (${data_dir}/) preserved."
    log_info "To resume, run 'make dev-spawn PORT=${target_port}'. To completely reset dev database, run 'make dev-reset PORT=${target_port}'."
}

cmd_reset_dev() {
    local target_port="$PORT"
    if [ -z "$target_port" ]; then
        local err_code=0
        target_port=$(resolve_dev_port "" "true") || err_code=$?
        if [ $err_code -eq 1 ]; then
            exit 1
        elif [ $err_code -eq 2 ]; then
            local data_dirs=()
            local found_dirs
            mapfile -t found_dirs < <(find . -maxdepth 1 -type d -name "dev_data_*" 2>/dev/null | sed -E 's/.*dev_data_([0-9]+)/\1/' | sort -u)
            for d in "${found_dirs[@]}"; do
                if [ -n "$d" ]; then data_dirs+=("$d"); fi
            done

            if [ ${#data_dirs[@]} -eq 1 ]; then
                target_port="${data_dirs[0]}"
                log_info "Auto-detected dev data directory on port ${target_port}."
            elif [ ${#data_dirs[@]} -gt 1 ]; then
                log_error "Multiple dev data directories exist:" >&2
                for d in "${data_dirs[@]}"; do
                    echo -e "  - Port ${YELLOW}${d}${NC} (directory: ./dev_data_${d})" >&2
                done
                echo "" >&2
                log_warn "Please specify which environment to reset using PORT=<port> (e.g. PORT=8081)" >&2
                exit 1
            else
                target_port="8081"
            fi
        fi
    fi

    local project="notas-dev-${target_port}"
    local data_dir="./dev_data_${target_port}"

    log_info "Wiping development environment and data for port ${target_port}..."
    DEV_PROJECT_NAME="$project" DEV_PORT="$target_port" DEV_DATA_DIR="$data_dir" \
        docker compose -p "$project" -f "$DEV_COMPOSE" down -v --remove-orphans || true
    rm -rf "$data_dir"
    log_success "Development data for port ${target_port} wiped."
    log_info "Re-spawning clean development environment on port ${target_port}..."
    PORT="$target_port" cmd_spawn_dev
}

cmd_restart_dev() {
    local target_port
    if ! target_port=$(resolve_dev_port "$PORT"); then
        exit 1
    fi

    local project="notas-dev-${target_port}"
    local web_container="${project}-web-1"
    local worker_container="${project}-celery-worker-1"
    local beat_container="${project}-celery-beat-1"

    if ! docker ps --filter "name=${web_container}" --format "{{.Names}}" | grep -q "${web_container}"; then
        log_error "Dev web container '${web_container}' is not running."
        exit 1
    fi

    log_info "Restarting development web and celery workers for port ${target_port}..."
    docker restart "${web_container}" "${worker_container}" "${beat_container}"
    log_success "Dev services for port ${target_port} restarted."
}

cmd_clone_prod_to_dev() {
    local target_port
    if ! target_port=$(resolve_dev_port "$PORT"); then
        exit 1
    fi

    local project="notas-dev-${target_port}"
    local dev_db_container="${project}-db-1"
    local dev_web_container="${project}-web-1"
    local data_dir="./dev_data_${target_port}"

    log_info "Cloning production database and media to dev environment on port ${target_port}..."

    # 1. Verify production database is running
    log_info "Checking if production database ('notas-db-1') is available..."
    if ! docker ps --filter "name=notas-db-1" --filter "status=running" --format "{{.Names}}" | grep -q "notas-db-1"; then
        log_error "Production database 'notas-db-1' is not running."
        exit 1
    fi

    # 2. Verify target dev db container is running
    log_info "Checking if target dev database ('${dev_db_container}') is running..."
    if ! docker ps --filter "name=${dev_db_container}" --filter "status=running" --format "{{.Names}}" | grep -q "${dev_db_container}"; then
        log_error "Dev database '${dev_db_container}' is not running. Please spawn it first: make dev-spawn PORT=${target_port}"
        exit 1
    fi

    # 3. Dump PostgreSQL from notas-db-1 and pipe directly into dev DB
    log_info "Dumping production database and restoring into ${dev_db_container}..."
    docker exec notas-db-1 pg_dump -U notas -d notas --clean | docker exec -i "${dev_db_container}" psql -U notas -d notas >/dev/null

    # 4. Copy media files to ./dev_data_<port>/media/
    if [ -d "media" ]; then
        log_info "Copying media files to ${data_dir}/media/..."
        mkdir -p "${data_dir}/media"
        cp -a media/. "${data_dir}/media/" 2>/dev/null || true
    fi

    # 5. Apply any pending migrations to ensure dev schema matches dev code
    log_info "Applying pending migrations in ${dev_web_container}..."
    docker exec "${dev_web_container}" python manage.py migrate --noinput

    # 6. Dev safety sanitization in dev container and cache invalidation
    log_info "Applying dev safety sanitization in ${dev_web_container}..."
    docker exec "${dev_web_container}" python manage.py shell -c "
from core.models import CompanySettings
from django.core.cache import cache
CompanySettings.objects.update(
    debug_mode=True,
    document_series='4242',
    auto_finalize_invoices=False
)
cache.clear()
print('Dev safety sanitization applied: debug_mode=True, series=4242, auto_finalize_invoices=False')
"

    # 7. Restart dev web and Celery workers to reload connections and clear in-memory caches
    log_info "Restarting dev services to refresh connections and caches..."
    docker restart "${dev_web_container}" "${project}-celery-worker-1" "${project}-celery-beat-1"

    log_success "Production clone to dev (port ${target_port}) completed successfully!"
}

cmd_test() {
    local target_port
    if ! target_port=$(resolve_dev_port "$PORT"); then
        exit 1
    fi

    local project="notas-dev-${target_port}"
    local web_container="${project}-web-1"

    if ! docker ps --filter "name=${web_container}" --format "{{.Names}}" | grep -q "${web_container}"; then
        log_error "Tests must ALWAYS be executed inside a running development environment."
        log_error "Container '${web_container}' is currently not running."
        echo ""
        log_info "Please run 'make dev-spawn PORT=${target_port}' before running tests."
        exit 1
    fi

    log_info "Running test suite inside development container (${web_container})..."
    docker exec "${web_container}" python manage.py test --noinput "$@"
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
    echo -e "${BLUE}=== Active Development Environments ===${NC}"
    local running_ports
    mapfile -t running_ports < <(get_running_dev_ports)
    local non_empty=()
    for p in "${running_ports[@]}"; do
        if [ -n "$p" ]; then non_empty+=("$p"); fi
    done

    if [ ${#non_empty[@]} -eq 0 ]; then
        echo "No development containers are currently running."
    else
        for p in "${non_empty[@]}"; do
            echo -e "${GREEN}--- Project: notas-dev-${p} (Port: ${p}) ---${NC}"
            DEV_PROJECT_NAME="notas-dev-${p}" DEV_PORT="$p" DEV_DATA_DIR="./dev_data_${p}" \
                docker compose -p "notas-dev-${p}" -f "$DEV_COMPOSE" ps
            echo ""
        done
    fi
}

ACTION="$1"
shift || true

REMAINING_ARGS=()
for arg in "$@"; do
    case "$arg" in
        PORT=*)
            PORT="${arg#PORT=}"
            ;;
        REF=*)
            REF="${arg#REF=}"
            ;;
        BIND=*)
            BIND="${arg#BIND=}"
            ;;
        *)
            REMAINING_ARGS+=("$arg")
            ;;
    esac
done

case "$ACTION" in
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
    clone-prod)
        cmd_clone_prod_to_dev
        ;;
    test)
        cmd_test "${REMAINING_ARGS[@]}"
        ;;
    upgrade-prod)
        cmd_upgrade_prod
        ;;
    status)
        cmd_status
        ;;
    *)
        echo "Usage: $0 {spawn-dev|destroy-dev|reset-dev|restart-dev|clone-prod|test|upgrade-prod|status} [PORT=<port>] [REF=<ref>] [BIND=0|1] [test_args...]"
        exit 1
        ;;
esac
