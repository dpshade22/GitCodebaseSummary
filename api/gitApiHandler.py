
import requests


def get_repo_contents(user, repo, path='', token=''):
    headers = {'Authorization': f'token {token}'} if token else {}
    url = f'https://api.github.com/repos/{user}/{repo}/contents/{path}'
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()
