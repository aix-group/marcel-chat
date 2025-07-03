#!/bin/bash

set -e
set -x

python -m marcel.init_data documents
python -m marcel.init_data admins
