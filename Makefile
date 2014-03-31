all: client.xpi

.PHONY: client.xpi

client.xpi:
	cd client; zip -r ../client.xpi * -x backend/data/\* -x \*.pyc -x \*~; cd ..