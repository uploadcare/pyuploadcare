# Make sure that a specific variable has been set.
check-env-%:
	@ if [ "${${*}}" = "" ]; then \
		echo "Environment variable $* not set"; \
		exit 1; \
	fi

format:
	uv run black .
	uv run isort .

lint:
	uv run black --check .
	uv run isort --check .
	uv run flake8 .
	uv run mypy --namespace-packages --show-error-codes --check-untyped-defs .

test:
	uv run pytest -v tests/ --cov=pyuploadcare

test-functional:
	uv run pytest tests/functional --cov=pyuploadcare

test-django:
	uv run pytest tests/dj --cov=pyuploadcare

test-integration:
	uv run pytest tests/integration --cov=pyuploadcare

# Re-record the file-tags / file-search cassettes against a throwaway VCR
# project. Needs real keys exported; the script strips them for the final
# replay verification so the signature tests keep using demosecretkey.
rerecord-cassettes: check-env-UPLOADCARE_PUBLIC_KEY check-env-UPLOADCARE_SECRET_KEY
	uv run python scripts/rerecord_cassettes.py $(UPLOADCARE_PUBLIC_KEY)

test_with_github_actions:
	act -W .github/workflows/test.yml --container-architecture linux/amd64

docs_html:
	uv run sh -c "cd docs && make html"

run_django:
	uv run python tests/test_project/manage.py migrate
	uv run python tests/test_project/manage.py runserver

update_bundled_static:
	blocks_version=$$(DJANGO_SETTINGS_MODULE=tests.test_project.settings uv run python -c "from pyuploadcare.dj.conf import DEFAULT_CONFIG; print(DEFAULT_CONFIG['widget']['version'])"); \
	curl "https://cdn.jsdelivr.net/npm/@uploadcare/file-uploader@$${blocks_version}/web/file-uploader.min.js" -o pyuploadcare/dj/static/uploadcare/file-uploader.min.js; \
	curl "https://cdn.jsdelivr.net/npm/@uploadcare/file-uploader@$${blocks_version}/web/uc-file-uploader-inline.min.css" -o pyuploadcare/dj/static/uploadcare/uc-file-uploader-inline.min.css; \
	curl "https://cdn.jsdelivr.net/npm/@uploadcare/file-uploader@$${blocks_version}/web/uc-file-uploader-minimal.min.css" -o pyuploadcare/dj/static/uploadcare/uc-file-uploader-minimal.min.css; \
	curl "https://cdn.jsdelivr.net/npm/@uploadcare/file-uploader@$${blocks_version}/web/uc-file-uploader-regular.min.css" -o pyuploadcare/dj/static/uploadcare/uc-file-uploader-regular.min.css

