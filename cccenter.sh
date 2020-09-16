#!/bin/bash
if [ ! -d "./env" ]; then
	# environment not existent
	# create new one
	python3 -m venv ./env
	# activate environment
	. ./env/bin/activate
	#install neccessary libraries
	pip3 install urwid python-can
	#deactivate environment
	deactivate
fi

# activate environment, run program and deactivate after
. ./env/bin/activate
python3 ./cancontrol.py $@
deactivate
