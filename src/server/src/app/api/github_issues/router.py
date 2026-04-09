from fastapi import APIRouter

from .service import GithubApiHelper


router = APIRouter(tags=["github-issues"])

@router.get("/github-issues/repo/{org}/{repo}")
def fetch_github_issues(org: str, repo: str):
    try:
        issues = GithubApiHelper(f'{org}/{repo}').get_open_issues()
        
        return {"issues": issues}
    except Exception as e:
        print(e)