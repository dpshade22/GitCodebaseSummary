from flask import Flask, request, jsonify
import os
import json
import base64
import requests
import mimetypes
from dotenv import load_dotenv

app = Flask(__name__)

declarativeSystemMessage = """Evaluate each function. Grade it from A-F and offer improvements without writing code. Use markdown formatting.
                            # <File Name>:
                            ---
                            ## <Function 1 Name>: <Grade>
                                - Pros:
                                    - <Pro 1>
                                    - <Pro 2>
                                - Cons:
                                    - <Con 1>
                                    - <Con 2>
                            ---
                            ## <Function 2 Name>: <Grade>
                                - Pros:
                                    - <Pro 1>
                                    - <Pro 2>
                                - Cons:
                                    - <Con 1>
                                    - <Con 2>
                            ---
                            ...
                            """


def get_repo_contents(user, repo, path='', token=''):
    headers = {'Authorization': f'token {token}'} if token else {}
    url = f'https://api.github.com/repos/{user}/{repo}/contents/{path}'
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


PROGRAMMING_EXTENSIONS = ['.py', '.js', '.java', '.c', '.cpp', '.go', '.rb', '.php', '.cs', '.m', '.r', '.swift', '.kt',
                          '.ts', '.scala', '.rs', '.hs', '.lua', '.groovy', '.pl', '.sh', '.html', '.css', '.sass', '.scss', 'Dockerfile', '.toml']


def is_programming_file(file_name):
    filename, extension = os.path.splitext(file_name)
    return extension in PROGRAMMING_EXTENSIONS or filename in PROGRAMMING_EXTENSIONS


def decode_content(file_contents):
    if 'content' in file_contents and file_contents['encoding'] == 'base64':
        return base64.b64decode(file_contents['content']).decode('utf-8')
    return None


def store_repo_paths(contents, user, repo, token=''):
    repo_dict = {}
    llm_responses_dict = {}
    messages = []
    for item in contents:
        if item['type'] == 'file':
            file_contents = get_repo_contents(user, repo, item['path'], token)
            file_type, _ = mimetypes.guess_type(file_contents['name'])

            if is_programming_file(file_contents['name']):
                repo_dict[item['path']] = {
                    'type': 'file',
                    'name': item['name'],
                    'content': decode_content(file_contents)
                }
                messages += [
                    {"role": "user", "content": repo_dict[item['path']]['content']}]

                systemMessage = declarativeSystemMessage
                llm_response = interact_with_llm(messages, systemMessage)
                llm_responses_dict[item['path']] = llm_response
                try:
                    create_markdown_file(
                        file_contents['name'], llm_response['choices'][0]['message']['content'])
                    messages += [{"role": "assistant",
                                  "content": llm_response['choices'][0]['message']['content']}]

                except Exception as e:
                    messages = messages[:-1]
                    print('error for: ', file_contents['name'])
                    print(e)
            else:
                print(file_contents['name'], file_type)
        elif item['type'] == 'dir':
            repo_dict[item['path']] = {
                'type': 'dir',
                'name': item['name']
            }
            dir_contents = get_repo_contents(user, repo, item['path'], token)
            sub_repo_dict, sub_llm_responses_dict, _ = store_repo_paths(
                dir_contents, user, repo, token)
            repo_dict.update(sub_repo_dict)
            llm_responses_dict.update(sub_llm_responses_dict)

    return repo_dict, llm_responses_dict, messages


def interact_with_llm(messages, systemMessage='Be precise and concise'):
    url = "https://api.perplexity.ai/chat/completions"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Bearer {os.getenv('PPLX_API_KEY')}"
    }
    payload = {
        "model": "codellama-34b-instruct",
        "messages": [
            {
                "role": "system",
                "content": systemMessage
            },
        ] + messages
    }

    response = requests.post(url, json=payload, headers=headers)
    return response.json()


def create_markdown_file(fullFile, llm_resp_content):
    filename, extension = os.path.splitext(fullFile)

    with open(f'mds/{filename}.md', 'w') as f:
        f.write(llm_resp_content)


def main():
    load_dotenv()
    user = 'dpshade22'
    repo = 'GoScriptureHono'
    token = os.getenv('GIT_PAT')
    contents = get_repo_contents(user, repo, token=token)
    repo_dict, llm_dict, messages = store_repo_paths(
        contents, user, repo, token)
    with open('repo_dict.json', 'w') as f:
        json.dump(repo_dict, f)

    with open('llm_responses.json', 'w') as f:
        json.dump(llm_dict, f)

    print(interact_with_llm(
        messages + [{'role': 'user', 'content': 'Summarize the codebase'}]))


@app.route('/summarize_codebase', methods=['GET'])
def summarize_codebase():
    user = request.args.get('user')
    repo = request.args.get('repo')
    token = request.args.get('token', os.getenv('GIT_PAT'))
    contents = get_repo_contents(user, repo, token=token)
    repo_dict, llm_dict, messages = store_repo_paths(
        contents, user, repo, token)
    summary = interact_with_llm(
        messages + [{'role': 'user', 'content': 'Summarize the codebase'}])
    return jsonify(summary)


if __name__ == "__main__":
    load_dotenv()
    app.run(debug=True)
