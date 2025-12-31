# Makefile for melbourne-moving-sale
# Edit data/items.yaml, then run make commands

.PHONY: help readme issues csv all clean setup

# =============================================================================
# Main Commands
# =============================================================================

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

all:  ## Sync everything (README + Issues + CSV + Item pages)
	python3 scripts/sync.py all
	python3 scripts/generate_item_readmes.py

pages:  ## Generate item pages (images/items/<ID>/README.md)
	python3 scripts/generate_item_readmes.py

readme:  ## Update README.md from items.yaml
	python3 scripts/sync.py readme

issues:  ## Sync GitHub Issues from items.yaml
	python3 scripts/sync.py issues

csv:  ## Export items to CSV (data/items.csv)
	python3 scripts/sync.py csv

# =============================================================================
# Editing & Viewing
# =============================================================================

edit:  ## Edit items.yaml
	$${EDITOR:-vim} data/items.yaml

list:  ## List all items (ID, Name, Status)
	@python3 -c "import yaml; d=yaml.safe_load(open('data/items.yaml')); [print(f\"{i['id']:>3} | {i['status']:<10} | {i['name']}\") for i in d['items']]"

status:  ## Show item counts by status
	@echo "=== Item Status ==="
	@echo -n "Available: " && grep -c "status: available" data/items.yaml || echo "0"
	@echo -n "Reserved:  " && grep -c "status: reserved" data/items.yaml 2>/dev/null || echo "0"
	@echo -n "Sold:      " && grep -c "status: sold" data/items.yaml 2>/dev/null || echo "0"

# =============================================================================
# GitHub
# =============================================================================

open:  ## Open GitHub Issues page in browser
	gh browse --repo ywatanabe1989/melbourne-moving-sale -- issues

# =============================================================================
# Images
# =============================================================================

add-photo:  ## Add photo for an item: make add-photo ID=001 FILE=photo.jpg
	@if [ -z "$(ID)" ] || [ -z "$(FILE)" ]; then \
		echo "Usage: make add-photo ID=001 FILE=photo.jpg"; \
		exit 1; \
	fi
	@mkdir -p images/items/$(ID)
	@cp "$(FILE)" images/items/$(ID)/
	@echo "Added $(FILE) to images/items/$(ID)/"

# =============================================================================
# Setup
# =============================================================================

setup:  ## Initial setup (install dependencies)
	pip install pyyaml

clean:  ## Clean generated files
	rm -f data/items.csv

tree:  ## Show project structure
	@tree -I '__pycache__|.git|.claude' --dirsfirst
