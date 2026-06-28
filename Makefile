install:
	pip install --upgrade pip && \
	pip install -r requirements.txt

format:
	black *.py

train:
	python train.py

eval:
	echo "## Model Metrics" > report.md
	cat ./results/metrics.json >> report.md

	echo "## Confusion Matrix Plot" >> report.md
	echo "![Confusion Matrix](./results/confusion_matrix.png)" >> report.md

	cml comment create report.md