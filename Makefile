# Docker Registry (Defaults to local/empty if not set)
# Example: make push DOCKER_REGISTRY=myrepo/
DOCKER_REGISTRY ?= 
IMAGE_NAME = ipmi-kvm-docker
TAG ?= latest
FULL_IMAGE_NAME = $(DOCKER_REGISTRY)$(IMAGE_NAME)

.PHONY: all build push run dashboard clean

all: build

build:
	docker build --platform linux/amd64 -t $(FULL_IMAGE_NAME):$(TAG) .

push: build
	@if [ -z "$(DOCKER_REGISTRY)" ]; then \
		echo "Warning: DOCKER_REGISTRY is not set. Pushing to Docker Hub by default (if authenticated)."; \
		echo "To push to a specific registry, run: make push DOCKER_REGISTRY=your-registry/"; \
	fi
	docker push $(FULL_IMAGE_NAME):$(TAG)

run:
	@if [ -z "$(START_URL)" ]; then \
		echo "Error: START_URL environment variable is not set. Please provide the target IPMI URL."; \
		exit 1; \
	fi
	docker run -d -p 8080:8080 -e START_URL=$(START_URL) $(FULL_IMAGE_NAME):$(TAG)

dashboard: build
	@echo "Generating dashboard..."
	# This will be replaced by the Python script call
	# Usage: make dashboard NETWORK_CIDR=192.168.1.0/24
	@if [ -z "$(NETWORK_CIDR)" ]; then \
		echo "Error: NETWORK_CIDR is not set. Usage: make dashboard NETWORK_CIDR=192.168.1.0/24"; \
		exit 1; \
	fi
	python3 tiny-dashboard/generate_dashboard.py --image $(FULL_IMAGE_NAME):$(TAG) $(NETWORK_CIDR)
	@echo "Cleaning up existing dashboard containers..."
	docker compose -f ./tiny-dashboard/docker-compose.yml down --remove-orphans || true
	@echo "Starting dashboard..."
	docker compose -f ./tiny-dashboard/docker-compose.yml up -d

clean:
	@echo "Cleaning up all containers and images..."
	docker compose -f ./tiny-dashboard/docker-compose.yml down --remove-orphans || true
	docker rm -f $(shell docker ps -aq --filter ancestor=$(FULL_IMAGE_NAME):$(TAG)) || true
	docker rmi $(FULL_IMAGE_NAME):$(TAG) || true
	rm -rf ./tiny-dashboard/config/* || true
	rm -f ./tiny-dashboard/docker-compose.yml || true
