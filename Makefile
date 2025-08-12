# Makefile for logs-to-bitmap project

.PHONY: all clean run-server run-crawler run-crawler-1k run-crawler-1k-v3 zip anomaly-detect train-model-100 train-model-1k compare-models test test-unit test-integration test-functional test-overfitting test-reproducibility compare-v1-v2 compare-v1-v2-cross help

# Get current unix timestamp
TIMESTAMP := $(shell date +%s)

# Default target
all: help

# Help target
help:
	@echo "Available targets:"
	@echo "  make clean           - Remove log and bitmap files"
	@echo "  make run-server      - Start the Pyramid server"
	@echo "  make run-crawler     - Run the original crawler (100 requests)"
	@echo "  make run-crawler-1k  - Run 1K crawler (1000 requests with 10 anomalies)"
	@echo "  make run-crawler-1k-v3 - Run V3 chaos crawler (diverse attack patterns)"
	@echo "  make anomaly-detect  - Run anomaly detection on bitmap samples"
	@echo "  make train-model-100 - Train model on 100-sample dataset"
	@echo "  make train-model-1k  - Train model on 1K-sample dataset"
	@echo "  make compare-models  - Compare model sizes and performance"
	@echo "  make zip             - Create timestamped zip file of logs and bitmaps in zips/"
	@echo "  make test            - Run all tests (unit, integration, functional)"
	@echo "  make test-unit       - Run unit tests (individual component testing)"
	@echo "  make test-integration - Run integration tests (end-to-end workflow)"
	@echo "  make test-functional - Run functional tests (overfitting diagnosis)"
	@echo "  make test-overfitting - Run cross-validation overfitting detection tests"
	@echo "  make test-reproducibility - Run reproducibility and random seed tests"
	@echo "  make compare-v1-v2   - Compare original vs enhanced feature models"
	@echo "  make compare-v1-v2-cross - Cross-dataset comparison of models"

# Clean targets
clean:
	@echo "Cleaning all generated files"
	rm -f logs/*
	@echo "Log files removed"
	rm -f images/*
	@echo "Image files (BMP and JPEG) removed"
	rm -f pastebin.db
	@echo "Database removed"


# Run targets
run-server:
	@echo "Starting Pyramid server on http://localhost:6543"
	@echo "Press Ctrl+C to stop"
	python3 app.py

run-crawler:
	@echo "Running original crawler (100 requests)"
	python3 utils/crawler.py

run-crawler-1k:
	@echo "Running 1K crawler (1000 requests with 10 anomalies)"
	python3 utils/crawler_1k.py

run-crawler-1k-v3:
	@echo "Running V3 chaos crawler (1000 requests with diverse attack patterns)"
	python3 utils/crawler_1k_v3.py


# Anomaly detection
anomaly-detect:
	@echo "Running anomaly detection on image samples"
	@mkdir -p anomaly_scores
	@if [ -d "images" ] && [ -n "$$(ls -A images/ 2>/dev/null)" ]; then \
		python3 utils/anomaly_detection.py images/ --output anomaly_scores/anomaly_results.csv; \
	else \
		echo "Error: No image files found. Run 'make run-crawler' first."; \
		exit 1; \
	fi

# Model training targets
train-model-100:
	@echo "Training model on 100-sample dataset"
	@mkdir -p models anomaly_scores
	@if [ -d "images" ] && [ -n "$$(ls -A images/ 2>/dev/null)" ]; then \
		SAMPLE_COUNT=$$(ls images/*.bmp images/*.jpg 2>/dev/null | wc -l); \
		if [ "$$SAMPLE_COUNT" -eq 100 ] || [ "$$SAMPLE_COUNT" -eq 200 ]; then \
			python3 utils/anomaly_detection.py images/ --save-model models/model_100_samples_$(TIMESTAMP).pkl --output anomaly_scores/results_100_samples.csv; \
			echo "Model saved: models/model_100_samples_$(TIMESTAMP).pkl"; \
		else \
			echo "Error: Expected 100 or 200 image files, found $$SAMPLE_COUNT. Run 'make run-crawler' first."; \
			exit 1; \
		fi \
	else \
		echo "Error: No image files found. Generate 100 samples first."; \
		exit 1; \
	fi

train-model-1k:
	@echo "Training model on 1K-sample dataset"
	@mkdir -p models anomaly_scores
	@if [ -d "images" ] && [ -n "$$(ls -A images/ 2>/dev/null)" ]; then \
		SAMPLE_COUNT=$$(ls images/*.bmp images/*.jpg 2>/dev/null | wc -l); \
		if [ "$$SAMPLE_COUNT" -eq 1000 ] || [ "$$SAMPLE_COUNT" -eq 2000 ]; then \
			python3 utils/anomaly_detection.py images/ --contamination 0.01 --estimators 200 --save-model models/model_1k_samples_$(TIMESTAMP).pkl --output anomaly_scores/results_1k_samples.csv; \
			echo "Model saved: models/model_1k_samples_$(TIMESTAMP).pkl"; \
		else \
			echo "Error: Expected 1000 or 2000 image files, found $$SAMPLE_COUNT. Run 'make run-crawler-1k' first."; \
			exit 1; \
		fi \
	else \
		echo "Error: No image files found. Generate 1000 samples first."; \
		exit 1; \
	fi

train-model-1k-jpeg:
	@echo "Training model on 1K-sample dataset (JPEG only)"
	@mkdir -p models anomaly_scores
	@if [ -d "images" ] && [ -n "$$(ls -A images/ 2>/dev/null)" ]; then \
		SAMPLE_COUNT=$$(ls images/*.jpg 2>/dev/null | wc -l); \
		if [ "$$SAMPLE_COUNT" -eq 1000 ]; then \
			python3 utils/anomaly_detection.py images/ --file-type jpg --contamination 0.01 --estimators 200 --save-model models/model_1k_jpeg_$(TIMESTAMP).pkl --output anomaly_scores/results_1k_jpeg.csv; \
			echo "Model saved: models/model_1k_jpeg_$(TIMESTAMP).pkl"; \
		else \
			echo "Error: Expected 1000 JPEG files, found $$SAMPLE_COUNT. Run 'make run-crawler-1k' first."; \
			exit 1; \
		fi \
	else \
		echo "Error: No image files found. Generate 1000 samples first."; \
		exit 1; \
	fi

compare-models:
	@echo "Comparing trained models"
	@if [ ! -d "models" ] || [ -z "$$(ls models/*.pkl 2>/dev/null)" ]; then \
		echo "No models found. Train models first with 'make train-model-100' or 'make train-model-1k'"; \
		exit 1; \
	fi
	@echo "Model Comparison Report"
	@echo "======================="
	@echo ""
	@for model in models/*.pkl; do \
		if [ -f "$$model" ]; then \
			SIZE=$$(ls -lah "$$model" | awk '{print $$5}'); \
			BYTES=$$(stat -f%z "$$model" 2>/dev/null || stat -c%s "$$model" 2>/dev/null || echo "?"); \
			BASENAME=$$(basename "$$model"); \
			echo "Model: $$BASENAME"; \
			echo "  Size: $$SIZE ($$BYTES bytes)"; \
			if echo "$$BASENAME" | grep -q "100_samples"; then \
				echo "  Dataset: 100 samples"; \
			elif echo "$$BASENAME" | grep -q "1k_samples"; then \
				echo "  Dataset: 1000 samples"; \
			fi; \
			echo "  Created: $$(ls -l "$$model" | awk '{print $$6, $$7, $$8}')"; \
			echo ""; \
		fi \
	done

# Zip target
zip:
	@echo "Creating timestamped logs and images zip"
	@mkdir -p zips
	@if [ -d "logs" ] && [ -d "images" ]; then \
		zip -r zips/$(TIMESTAMP)_logs_and_images.zip logs/ images/; \
		echo "Created: zips/$(TIMESTAMP)_logs_and_images.zip"; \
	else \
		echo "Error: logs and/or images directories not found"; \
		exit 1; \
	fi

# Test targets
test:
	@echo "Running all tests"
	python3 tests/run_tests.py --type all

test-unit:
	@echo "Running unit tests"
	python3 tests/run_tests.py --type unit

test-integration:
	@echo "Running integration tests"
	python3 tests/run_tests.py --type integration

test-functional:
	@echo "Running functional tests for anomaly detection issues"
	python3 tests/run_tests.py --type functional

test-overfitting:
	@echo "Running cross-validation overfitting detection tests"
	python3 -m pytest tests/functional/test_temporal_drift.py::TestOverfittingDetection -v

test-reproducibility:
	@echo "Running reproducibility and random seed tests"
	python3 -m pytest tests/functional/test_temporal_drift.py::TestShufflingReproducibility -v
	python3 -m pytest tests/unit/test_anomaly_detection.py::TestAnomalyDetection::test_random_sampling_reproducibility -v

compare-v1-v2:
	@echo "Comparing original vs enhanced feature extraction models"
	python3 tests/compare_models.py

compare-v1-v2-cross:
	@echo "Cross-dataset comparison of v1 vs v2 models"
	@if [ -d "images_train" ] && [ -d "images" ]; then \
		python3 tests/compare_models.py --train-dir images_train --test-dir images; \
	else \
		echo "Error: Need both images_train/ (training) and images/ (test) directories"; \
		echo "Run: mv images images_train && make run-crawler-1k"; \
	fi
