PYTHON_FILES=$(shell \
	find . \
	-path "./.ignore" -prune -o \
	-path "./venv" -prune -o \
	-type f -name "*.py" \
	-exec echo -n {}" " \; \
)

black:
	black ${PYTHON_FILES}

pyflakes:
	pyflakes ${PYTHON_FILES}
