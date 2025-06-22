from flask import Flask, request

app = Flask(__name__)

@app.route('/github/webhook', methods=['POST'])
def github_webhook():
    data = request.json
    if 'commits' in data:
        print(f"[{data['repository']['full_name']}] Nouveaux commits :")
        for commit in data['commits']:
            print(f"{commit['author']['name']} → {commit['message']}")
    return '', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
