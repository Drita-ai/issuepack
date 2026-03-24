import os
from github import Auth, Github

class GithubApiHelper:
    def __init__(self, repo):
        # Authentication
        auth = Auth.Token(os.environ.get("GITHUB_ACCESS_TOKEN"))
        self.g = Github(auth=auth)
        
        # Working Repo
        repo = self.g.get_repo(repo) 
        self.repo = repo
        
    def get_open_issues(self):
        """
        Returns open issues of the repo
        """
        open_issues = self.repo.get_issues(state='open')
        return self.to_issue_list(open_issues)
    
    def get_issue(self, issue_number):
        """
        Returns specific issue associated with the issue number
        """
        return self.repo.get_issue(number=issue_number)
    
    def get_first_n_issues(self, issues, n=10):
        return [issue for i, issue in enumerate(issues) if i < n]
    
    def to_issue_list(self, issues):
        """
        Converts PaginatedList to List
        """
        return [
            {  
                "number":issue.number,
                "title":issue.title,
                "body":issue.body or ""
            }
            for issue in issues
        ]