# Make sure that a specific variable has been set.
check-env-%:
	@ if [ "${${*}}" = "" ]; then \
		echo "Environment variable $* not set"; \
		exit 1; \
	fi

format:
	poetry run black .
	poetry run isort .

lint:
	poetry run black --check .
	poetry run isort --check .
	poetry run flake8 .
	poetry run mypy --namespace-packages --show-error-codes .

test:
	poetry run pytest -v tests/ --cov=pyuploadcare

test-functional:
	poetry run pytest tests/functional --cov=pyuploadcare

test-django:
	poetry run pytest tests/dj --cov=pyuploadcare

test-integration:
	poetry run pytest tests/integration --cov=pyuploadcare

docs_html:
	poetry run sh -c "cd docs && make html"
