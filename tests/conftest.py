"""Testovi obrade podataka. Pokretanje iz korijena repozitorija:  pytest"""

import sys
from pathlib import Path

KORIJEN = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KORIJEN / "pipeline"))
