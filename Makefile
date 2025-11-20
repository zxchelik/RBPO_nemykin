APP_NAME ?= course-app
IMAGE_TAG ?= local
COMPOSE ?= docker compose

.PHONY: docker-build compose-up compose-down hadolint trivy

docker-build:
	@echo "Building $(APP_NAME):$(IMAGE_TAG) image"
	docker build --target runtime -t $(APP_NAME):$(IMAGE_TAG) .

compose-up:
	$(COMPOSE) up --build

compose-down:
	$(COMPOSE) down --remove-orphans

hadolint:
	docker run --rm -i -v $(CURDIR):/workdir -w /workdir ghcr.io/hadolint/hadolint:latest < Dockerfile

trivy:
	docker run --rm \
		-v /var/run/docker.sock:/var/run/docker.sock \
		aquasec/trivy:0.52.3 image --severity HIGH,CRITICAL --exit-code 0 --format table $(APP_NAME):$(IMAGE_TAG)
