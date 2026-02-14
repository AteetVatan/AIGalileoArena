---
name: daily-eval-report
description: Run AI Galileo Arena LLM evaluations and post results to Twitter/X and LinkedIn
---

# Daily LLM Eval Report

Run the AI Galileo Arena evaluation suite and publish results to social media.

## Steps

### 1. Run the evaluation

Use the `exec` tool to run the eval report script:

```
cd s:/SYNC/programming/AIGalileoArena/backend && python scripts/run_eval_report.py --base http://localhost:8000
```

The script runs 6 LLMs (GPT-4o, Claude Sonnet 4, Mistral Large, DeepSeek, Gemini 2.0 Flash, Grok-3) against 2 random datasets with 2 cases each, then generates two report files:

- `reports/eval_YYYY-MM-DD_twitter.txt` — Compact leaderboard with emojis and hashtags
- `reports/eval_YYYY-MM-DD_linkedin.txt` — Professional post format

Both are also printed to stdout.

### 2. Post to Twitter/X

Use the **bird** skill to post the **Twitter report** as a tweet. Read the file `s:/SYNC/programming/AIGalileoArena/backend/reports/eval_YYYY-MM-DD_twitter.txt` (use today's date) and post its contents. If the report is too long for a single tweet, split it into a thread.

### 3. Post to LinkedIn

Use the **browser** tool to post the **LinkedIn report**:

1. Open `https://www.linkedin.com/feed/` in the browser
2. Take a snapshot to find the "Start a post" button and click it
3. Read the file `s:/SYNC/programming/AIGalileoArena/backend/reports/eval_YYYY-MM-DD_linkedin.txt` (use today's date)
4. Type/paste the report content into the post composer
5. Click the "Post" button
6. Confirm it was posted successfully

## Notes

- The backend API must be running at the `--base` URL for evals to work.
- If the bird skill is not installed, install it first: `clawhub install bird`
- LinkedIn requires being logged in via an OpenClaw browser profile. Log in once manually; the session persists.
