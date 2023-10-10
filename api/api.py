import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from api.llm.pplxApi import interact_with_llm, get_llm_responses
from api.tree.gitTree import get_tree_contents, is_programming_file, decode_content
from api.gitApiHandler import get_repo_contents
app = Flask(__name__)


def create_markdown_file(fullFile, llm_resp_content):
    filename, extension = os.path.splitext(fullFile)

    with open(f'mds/{filename}.md', 'w') as f:
        f.write(llm_resp_content)


@app.route('/summarize_codebase', methods=['GET'])
def summarize_codebase():
    user = request.args.get('user')
    repo = request.args.get('repo')
    token = request.args.get('token', os.getenv('GIT_PAT'))
    tree = get_tree_contents(user, repo, token)
    repo_dict = traverse_repo(tree, user, repo, token)
    llm_dict = get_llm_responses(repo_dict)

    return jsonify(llm_dict)


@app.route('/file_summary', methods=['GET'])
def get_file_summary():
    """
    Gets a summary of a file.
    """
    user = request.args.get('user')
    repo = request.args.get('repo')
    file_name = request.args.get('filepath')
    token = request.args.get('token', os.getenv('GIT_PAT'))
    contents = get_repo_contents(user, repo, file_name, token)
    if is_programming_file(contents['name']):
        file_content = decode_content(contents)
        summary = interact_with_llm(f"Summarize this file: {file_content}")
        return jsonify({'summary': summary})
    return jsonify({'error': 'File not found or not a programming file'}), 404


@app.route('/list_files', methods=['GET'])
def list_files():
    """ Lists all the files in a repository, including those nested within directories. """
    user = request.args.get('user')
    repo = request.args.get('repo')
    token = request.args.get('token', os.getenv('GIT_PAT'))
    tree = get_tree_contents(user, repo, token)
    files = [el['path'] for el in tree['tree'] if el['type'] == 'blob']
    folders = [el['path']
               for el in tree['tree'] if el['type'] == 'tree']

    return jsonify({'files': files, 'folders': folders})


@app.route('/get_tree', methods=['GET'])
def get_tree():
    """ Fetches a tree in a repository. """
    user = request.args.get('user')
    repo = request.args.get('repo')
    tree_sha = request.args.get('tree_sha')
    token = request.args.get('token', os.getenv('GIT_PAT'))
    tree = get_tree_contents(user, repo, tree_sha, token)
    return jsonify({'tree': tree})


if __name__ == "__main__":
    load_dotenv()
    app.run(debug=True)
