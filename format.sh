#!/bin/bash
pip install --upgrade black || true
black --verbose --exclude migrations .
