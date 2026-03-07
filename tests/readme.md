Run with python -m pytest tests/ -v from the project root. 
Each new iteration gets its own test_iterN_*.py file. 
Test files are located in tests/files
The conftest.py fixture handles build → up → wait → migrate automatically, once per session.