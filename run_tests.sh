#!/bin/bash
/opt/homebrew/bin/python3.11 -m pip install groq==0.15.0 python-dotenv==1.0.1 pytest --quiet
/opt/homebrew/bin/python3.11 -m pytest
