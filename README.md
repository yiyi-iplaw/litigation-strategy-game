# Litigation Strategy Game Demo

A pure text based Streamlit demo for a U.S. litigation strategy game.

## What it does

- You play as defense counsel
- Initial budget is $5,000
- You investigate facts, file motions, negotiate, or wait
- Facts are incomplete at the start
- Judge style and opponent style change the odds
- The game ends in different litigation outcomes

## Local run

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy to GitHub

Create a new GitHub repository, then from this folder run:

```bash
git init
git add .
git commit -m "Initial litigation strategy game demo"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
git push -u origin main
```

## Deploy to Streamlit Community Cloud

1. Push this repo to GitHub
2. Open Streamlit Community Cloud
3. Choose **New app**
4. Select your GitHub repo
5. Main file path: `app.py`
6. Deploy

## Files

- `app.py` — main Streamlit app
- `requirements.txt` — Python dependencies
- `.gitignore` — basic ignore rules

## Notes

This is an early gameplay prototype. It is built as a narrative strategy demo rather than a legal advice tool.
