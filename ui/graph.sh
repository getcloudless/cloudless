#!/bin/bash

echo "Regenerating graph.dot!" 1>&2
python graph.py >| graph.dot
echo "Regenerating graph.pdf!" 1>&2
dot graph.dot -Tpdf -o graph.pdf
echo "Regenerating graph.svg!" 1>&2
dot graph.dot -Tsvg -o graph.svg
