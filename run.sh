#!/bin/sh
export PYTHONPATH=src:vendor
command="$1"
[ $# -gt 0 ] && shift
case "$command" in
    repl) python3 src/repl.py ;;
    server) python3 src/server.py "$@" ;;
    client) python3 src/client.py "$@" ;;
    test) python3 -m unittest discover -s tests -v ;;
    lint) python3 -m flake8 --max-line-length=80 src tests ;;
    coverage) python3 -m coverage run --branch --source=src -m unittest discover -s tests && python3 -m coverage report -m ;;
    *) echo "Usage: ./run.sh repl|server|client|test|lint|coverage" ;;
esac
