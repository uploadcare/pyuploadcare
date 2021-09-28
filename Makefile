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
