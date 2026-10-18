.PHONY: help dev-spawn dev-destroy dev-reset dev-restart dev-test test prod-upgrade status

help:
	@echo "Available commands:"
	@echo "  make dev-spawn    - Spawn development environment (clean-slate or resume existing)"
	@echo "  make dev-destroy  - Stop development environment containers (preserves dev_data for quick resume)"
	@echo "  make dev-reset    - Wipe dev_data and recreate clean-slate development environment"
	@echo "  make dev-restart  - Restart development web and Celery containers"
	@echo "  make dev-test     - Run the test suite inside the development container (never pollutes prod)"
	@echo "  make test         - Alias for dev-test"
	@echo "  make prod-upgrade - Build and deploy new production Docker image and run migrations"
	@echo "  make status       - View status of Production and Development containers"

dev-spawn:
	@./scripts/env.sh spawn-dev

dev-destroy:
	@./scripts/env.sh destroy-dev

dev-reset:
	@./scripts/env.sh reset-dev

dev-restart:
	@./scripts/env.sh restart-dev

dev-test:
	@./scripts/env.sh test $(ARGS)

test: dev-test

prod-upgrade:
	@./scripts/env.sh upgrade-prod

status:
	@./scripts/env.sh status

