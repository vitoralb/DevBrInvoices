.PHONY: help dev-spawn dev-destroy dev-reset dev-restart dev-clone-prod dev-test test prod-upgrade status

help:
	@echo "Available commands:"
	@echo "  make dev-spawn      - Spawn development environment (default PORT=8081, optional REF=<git-ref>, BIND=0|1)"
	@echo "  make dev-destroy    - Stop dev containers (preserves dev_data; auto-detects or PORT=<port>)"
	@echo "  make dev-reset      - Wipe dev_data and recreate clean-slate dev environment (PORT=<port>)"
	@echo "  make dev-restart    - Restart dev web and Celery containers (auto-detects or PORT=<port>)"
	@echo "  make dev-clone-prod - Clone production DB & media to dev (auto-detects or PORT=<port>)"
	@echo "  make dev-test       - Run tests in dev container (auto-detects or PORT=<port>, ARGS='...')"
	@echo "  make test           - Alias for dev-test"
	@echo "  make prod-upgrade   - Build and deploy new production Docker image and run migrations"
	@echo "  make status         - View status of Production and Development containers"

dev-spawn:
	@./scripts/env.sh spawn-dev $(if $(PORT),PORT=$(PORT),) $(if $(REF),REF=$(REF),) $(if $(BIND),BIND=$(BIND),)

dev-destroy:
	@./scripts/env.sh destroy-dev $(if $(PORT),PORT=$(PORT),)

dev-reset:
	@./scripts/env.sh reset-dev $(if $(PORT),PORT=$(PORT),)

dev-restart:
	@./scripts/env.sh restart-dev $(if $(PORT),PORT=$(PORT),)

dev-clone-prod:
	@./scripts/env.sh clone-prod $(if $(PORT),PORT=$(PORT),)

dev-test:
	@./scripts/env.sh test $(if $(PORT),PORT=$(PORT),) $(ARGS)

test: dev-test

prod-upgrade:
	@./scripts/env.sh upgrade-prod

status:
	@./scripts/env.sh status
