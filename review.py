import os
import requests
from github import Github

GROQ_API_KEY = os.environ["GROQ_API_KEY"]
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]

# GitHub context
REPO = os.environ["GITHUB_REPOSITORY"]
PR_NUMBER = int(os.environ["PR_NUMBER"])

def get_pr_diff():
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO)
    pr = repo.get_pull(PR_NUMBER)

    files = pr.get_files()

    diff_text = ""
    for f in files:
        if f.patch:
            diff_text += f"\n\nFile: {f.filename}\n{f.patch}"

    return diff_text


def review_code(diff):
    url = "https://api.groq.com/openai/v1/chat/completions"

    prompt = f"""
You are a senior software engineer performing a code review.

Review the following pull request diff:

{diff}

Focus on:
- Bugs
- Performance issues
- Security risks
- Code quality

Respond with clear, structured feedback.
"""

    response = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "llama3-70b-8192",
            "messages": [
                {"role": "system", "content": "You are an expert code reviewer."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3
        }
    )

    return response.json()["choices"][0]["message"]["content"]


def post_review(comment):
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO)
    pr = repo.get_pull(PR_NUMBER)

    pr.create_issue_comment(comment)


if __name__ == "__main__":
    diff = get_pr_diff()

    if not diff.strip():
        print("No diff found.")
        exit(0)

    review = review_code(diff)
    post_review(review)

print("Review posted successfully!")