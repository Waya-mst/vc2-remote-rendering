PYTHON_FILES=$(shell \
	find . \
	-path "./.ignore" -prune -o \
	-path "./venv" -prune -o \
	-type f -name "*.py" \
	-exec echo -n {}" " \; \
)

black:
	black ${PYTHON_FILES}

black-check:
	black --check ${PYTHON_FILES}

pyflakes:
	pyflakes ${PYTHON_FILES}

notebook:
	python colab/notebook.py > colab/websocket_server.ipynb

notebook-check:
	python colab/notebook.py | diff colab/websocket_server.ipynb -
