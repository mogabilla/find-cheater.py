name: Playwright Automation

on: [push]  # Jab bhi repo me push hoga, script auto run hogi

jobs:
  run-playwright:
    runs-on: ubuntu-latest  # Free GitHub Linux server
    steps:
      - name: Repository Clone
        uses: actions/checkout@v2

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'  # Python 3.9 use hoga

      - name: Install Dependencies
        run: |
          pip install playwright
          playwright install

      - name: Run Playwright Script
        run: python myscript.py
