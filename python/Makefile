.DEFAULT_GOAL := help
.PHONY: check install test clean

# Pretty colors
GREEN  := \033[0;32m
YELLOW := \033[1;33m
BYELLOW := \033[1;43m
BRAT   := \033[1;92m
NC     := \033[0m

help:
	@echo ""
	@echo "       $(BRAT) Welcome to the Jentic Python SDK$(NC)"
	@echo "  $(BRAT)One integration, unlimited APIs and workflows$(NC)"
	@echo ""
	@echo "$(NC)Please report any issues or feedback to support@jentic.com$(NC)"
	@echo "  $(NC)Discord: https://discord.com/jentic$(NC)"
	@echo "  $(NC)Email:   support@jentic.com$(NC)"
	@echo "  $(NC)Website: https://jentic.com$(NC)"

	@echo ""
	@echo "  $(YELLOW)Developer:$(NC)"
	@echo "    $(GREEN)install$(NC)        Install project dependencies via PDM"
	@echo "    $(GREEN)test$(NC)           Run tests"

	@echo ""
	@echo "  $(YELLOW)Formatting:$(NC)"
	@echo "    $(GREEN)check$(NC)          Run isort+black+mypy+ruff"

	@echo ""
	@echo "  $(YELLOW)Cleaning:$(NC)"
	@echo "    $(GREEN)clean$(NC)          Remove build artefacts & caches"
	@echo ""

clean:
	rm -rf __pycache__ .pytest_cache .ruff_cache .mypy_cache src/jentic/__pycache__ .pdm-build

install:
	@pdm install

test:
	PYTHONPATH=src pdm run pytest

coverage:
	PYTHONPATH=src pdm run pytest --cov=src/jentic --cov-report=term-missing

check:
	@pdm run black .
	@pdm run mypy . --exclude=src/jentic/lib/agent_runtime --exclude=tests/agent_runtime
	@pdm run ruff check --fix --exclude=tests/agent_runtime
