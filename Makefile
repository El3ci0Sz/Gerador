# Makefile for the Mapping Generator Project

# Defines an ARGS variable that can be overridden from the command line.
# Example: make campaign ARGS="--no-images --verbose"
ARGS =

.PHONY: help test campaign clean summary cgra-grammar-test cgra-random-test qca-grammar-test

# --- Main Commands ---

help:
	@echo "Available commands:"
	@echo "  make test                  -> Run all unit tests in the /tests directory."
	@echo "  make campaign              -> Run the full parallel generation campaign."
	@echo "  make clean                 -> Remove all generated files (results, cache, etc)."
	@echo "  make summary               -> Generate a CSV summary from the 'results_campaign' directory."
	@echo ""
	@echo "Quick Test Commands:"
	@echo "  make cgra-grammar-test     -> Run a small test of the CGRA grammar generator."
	@echo "  make cgra-random-test      -> Run a small test of the random CGRA generator."
	@echo "  make qca-grammar-test      -> Run a small test of the QCA grammar generator."
	@echo ""
	@echo "Usage with Parameters:"
	@echo "  You can add extra parameters to any execution command using the ARGS variable."
	@echo "  Example: make campaign ARGS=\"--no-images --verbose --clean\""
	@echo "  Example: make cgra-grammar-test ARGS=\"--arch-size 8 8 --k-graphs 10\""

test:
	@echo ">> Running unit tests..."
	python -m unittest discover tests/

campaign:
	@echo ">> Starting full generation campaign..."
	python scripts/runner.py campaign --output-dir results_campaign $(ARGS)

summary:
	@echo ">> Generating summary of campaign results..."
	python scripts/summarize_results.py results_campaign -o summary_campaign.csv

clean:
	@echo ">> Cleaning up generated files..."
	rm -rf results_campaign test_results __pycache__ */__pycache__ */*/__pycache__ */*/*/__pycache__
	rm -f *.csv *.png *.log
	@echo "Cleanup complete."


# --- Quick Individual Tests ---

cgra-grammar-test:
	@echo ">> Running quick test: CGRA with Grammar..."
	python scripts/runner.py single --tec cgra --gen-mode grammar --arch-size 4 4 --graph-range 6 7 --difficulty 5 --bits 1000 --k-graphs 3 --output-dir test_results $(ARGS)

cgra-random-test:
	@echo ">> Running quick test: Random CGRA..."
	python scripts/runner.py single --tec cgra --gen-mode random --arch-size 4 4 --graph-range 7 8 --bits 1111 --alpha 0.4 --k-graphs 3 --output-dir test_results $(ARGS)

qca-grammar-test:
	@echo ">> Running quick test: QCA with Grammar..."
	python scripts/runner.py single --tec qca --gen-mode grammar --arch-size 6 6 --graph-range 8 9 --qca-arch U --k-graphs 3 --output-dir test_results $(ARGS)
