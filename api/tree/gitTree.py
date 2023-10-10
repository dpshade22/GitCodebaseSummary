import os
import requests
import base64
from api.gitApiHandler import get_repo_contents
from dotenv import load_dotenv

load_dotenv()

PROGRAMMING_EXTENSIONS = ['.py', '.js', '.java', '.c', '.cpp', '.go', '.rb', '.php', '.cs', '.m', '.r', '.swift', '.kt',
                          '.ts', '.scala', '.rs', '.hs', '.lua', '.groovy', '.pl', '.sh', '.html', '.css', '.sass', '.scss', 'Dockerfile', '.toml']


def get_latest_commit_sha(user, repo, token=''):
    """ Fetches the SHA of the latest commit in a repository. """
    headers = {'Authorization': f'token {token}'} if token else {}
    url = f'https://api.github.com/repos/{user}/{repo}/commits'
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()[0]['sha']


def get_tree_contents(user, repo, token=''):
    """ Fetches the contents of a tree in a repository. """
    headers = {'Authorization': f'token {token}'} if token else {}
    tree_sha = get_latest_commit_sha(user, repo, token)
    url = f'https://api.github.com/repos/{user}/{repo}/git/trees/{tree_sha}?recursive=true'
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    return response.json()


def is_programming_file(file_name):
    filename, extension = os.path.splitext(file_name)
    return extension in PROGRAMMING_EXTENSIONS or filename in PROGRAMMING_EXTENSIONS


def decode_content(file_contents):
    if 'content' in file_contents and file_contents['encoding'] == 'base64':
        return base64.b64decode(file_contents['content']).decode('utf-8')
    return None


def traverse_repo(tree, user, repo, token=''):
    """ Traverses a repository non-recursively. """
    repo_dict = {}
    for item in tree['tree']:
        if item['type'] == 'blob':
            if is_programming_file(item['path']):
                file_contents = get_repo_contents(
                    user, repo, item['path'], token)
                repo_dict[item['path']] = {
                    'type': 'file',
                    'name': item['path'],
                    'content': decode_content(file_contents)
                }
        elif item['type'] == 'tree':
            repo_dict[item['path']] = {
                'type': 'dir',
                'name': item['path']
            }
    return repo_dict
