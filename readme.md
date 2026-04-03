# Groq PR Reviewer Bot (Reusable)

A professional-grade, automated code reviewer that uses the **Groq Llama-3.3-70b** engine to analyze pull requests, detect bugs, and suggest optimizations.

---

## Features

- Reviews PR code for **logic bugs**, **security risks**, and **performance issues**.
- Suggests **optimizations** and **new feature ideas**.
- Posts concise, actionable feedback directly as PR comments.
- Fully reusable workflow for multiple repositories.

---

## How to Use This Bot in Your Repository

### 1. Create the Workflow File

In your repository, create the directory:

```

.github/workflows

````

Then create a file named `groq-reviewer.yml` and paste the following:

```yaml
name: Groq PR Reviewer

on:
  pull_request_target:
    types: [opened, synchronize, reopened]

permissions:
  pull-requests: write
  contents: read

jobs:
  review:
    uses: rasbelikeSOON/prbotfinal/.github/workflows/groq-pr-review.yml@main
    secrets:
      GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }}
````

---

### 2. Add Your Groq API Key

For the bot to communicate with the AI engine, you need a **Groq API Key**:

1. Generate an API Key at [console.groq.com](https://console.groq.com).
2. Go to your repository **Settings → Secrets and variables → Actions**.
3. Add a new repository secret named:

```
GROQ_API_KEY
```

and paste your key.

---

### 3. How It Works

* When a pull request is **opened**, **reopened**, or **synchronized**, the workflow triggers.
* The bot fetches a **clean diff** of the PR changes.
* Each diff file is analyzed by the **Groq Llama-3.3-70b** engine for:

  * Logic bugs and security risks
  * Performance improvements
  * New feature ideas
* The bot aggregates all findings and posts a **structured comment** in the PR.

---

### 4. Optional Customization

* You can adjust the instructions sent to Groq in the reusable workflow to focus on specific areas like security, performance, or code style.
* Exclude files you don’t want reviewed (e.g., `package-lock.json`) by updating the workflow’s diff command.

---

### 5. Example PR Comment

```
###  Groq PR Review & Optimization

File: src/utils/helpers.js
-  Suggestion: Consider caching results of expensive computations to improve performance.
- Warning: Potential null reference when input is undefined; add validation.
-  New Feature Idea: Add optional logging parameter for debugging purposes.

---

File: src/components/Button.jsx
-  Suggestion: Use memoization to prevent unnecessary re-renders.
```

---

## Reusable Workflow Contents (groq-pr-review.yml)

For reference, here’s the actual reusable workflow that the `groq-reviewer.yml` calls:

```yaml
name: Groq PR Reviewer Bot

on:
  workflow_call:
    secrets:
      GROQ_API_KEY:
        required: true

jobs:
  review:
    runs-on: ubuntu-latest
    permissions:
      pull-requests: write
      contents: read

    steps:
      - name: Checkout Code
        uses: actions/checkout@v4
        with:
          repository: ${{ github.event.pull_request.head.repo.full_name }}
          ref: ${{ github.event.pull_request.head.ref }}
          fetch-depth: 0

      - name: Fetch Clean PR Diff
        run: |
          git fetch origin ${{ github.base_ref }}:base_branch
          git diff base_branch...HEAD \
            --unified=3 \
            --ignore-all-space \
            -- ":(exclude)package-lock.json" ":(exclude)*.lock" > full_diff.txt
          csplit -s -z -f diff_ full_diff.txt '/^diff --git/' '{*}' || true

      - name: Groq Analysis & Optimization
        id: review
        run: |
          mkdir -p reviews
          for f in diff_*; do
            [ -s "$f" ] || continue
            CONTENT=$(head -c 4000 "$f" | jq -Rs .)
            
            RESPONSE=$(curl -s https://api.groq.com/openai/v1/chat/completions \
              -H "Authorization: Bearer ${{ secrets.GROQ_API_KEY }}" \
              -H "Content-Type: application/json" \
              -d "{
                \"model\": \"llama-3.3-70b-versatile\",
                \"messages\": [
                  {
                    \"role\": \"system\", 
                    \"content\": \"You are a senior developer and code architect. Review this diff for: 1. Logic bugs and security risks. 2. Performance optimizations. 3. New feature ideas. Be concise but insightful.\"
                  },
                  {\"role\": \"user\", \"content\": $CONTENT}
                ]
              }")
            
            REVIEW=$(echo $RESPONSE | jq -r '.choices[0].message.content' 2>/dev/null || echo "null")
            
            if [ "$REVIEW" == "null" ] || [ "$REVIEW" == "" ]; then
              ERROR_MSG=$(echo $RESPONSE | jq -r '.error.message' 2>/dev/null || echo "Unknown API Error")
              echo " **Groq Error on file $(head -n 1 $f | cut -d' ' -f3):** $ERROR_MSG" > "reviews/$f.txt"
            else
              echo "$REVIEW" > "reviews/$f.txt"
            fi
          done

      - name: Aggregate Feedback
        id: aggregate
        run: |
          {
            echo 'comment<<EOF'
            echo "###  Groq PR Review & Optimization"
            for r in reviews/*.txt; do
              echo ""
              cat "$r"
              echo ""
              echo "---"
            done
            echo 'EOF'
          } >> "$GITHUB_OUTPUT"

      - name: Post Feedback Comment
        uses: thollander/actions-comment-pull-request@v2
        with:
          message: ${{ steps.aggregate.outputs.comment }}
```

---

With this setup, your repository will have a fully automated, AI-powered reviewer integrated directly into pull requests.

```

