.PHONY: install-dev lint format test run

# 第一次拿到项目跑这个
install-dev:
	pip install -e ".[dev]"
	pre-commit install
	@echo "✅ 开发环境安装完成"

lint:
	ruff check src/

format:
	ruff format src/
	ruff check src/ --fix

test:
	pytest tests/ -v

run:
	python src/main.py

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null; true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null; true
	find . -name "*.pyc" -delete 2>/dev/null; true
