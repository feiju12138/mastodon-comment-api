from http.server import BaseHTTPRequestHandler
import urllib.parse, os, json

class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type","text/plain")
        self.end_headers()
        self.wfile.write("ok".encode("utf-8"))
        return

    def do_POST(self):
        # 读取环境变量
        mastodon_token = os.getenv("MASTODON_TOKEN")
        mastodon_account = os.getenv("MASTODON_ACCOUNT")
        akismet_token = os.getenv("AKISMET_TOKEN")
        akismet_blog_url = os.getenv("AKISMET_BLOG_URL")
        if not mastodon_token or not mastodon_account:
            self.send_response(500)
            self.send_header("Content-type","text/plain")
            self.send_header("Access-Control-Allow-Origin","*")
            self.end_headers()
            self.wfile.write("env error".encode("utf-8"))
            return

        # 获取请求参数
        content_length = int(self.headers.get("Content-Length", 0))
        post_body = self.rfile.read(content_length)
        json_params = json.loads(post_body.decode("utf-8"))
        toot_id = json_params.get("toot_id", "")
        current_url = json_params.get("current_url", "")
        if not toot_id or not current_url:
            self.send_response(400)
            self.send_header("Content-type","text/plain")
            self.send_header("Access-Control-Allow-Origin","*")
            self.end_headers()
            self.wfile.write("param error".encode("utf-8"))
            return

        # 发送请求 根据tootid获取评论列表
        comment_result = self.get_mastodon_comments(mastodon_token, mastodon_account)

        # 合规判定
        if akismet_token and akismet_blog_url:
            # 垃圾评论索引
            to_delete_indices = []
            for index, descendant in enumerate(comment_result.descendants):
                # 提取内容
                comment_content = descendant.content
                comment_author = descendant.account.username
                blog_lang = descendant.language
                # 发送请求 假别是否是垃圾评论
                result = self.check_akismet_spam(akismet_token, akismet_blog_url, blog_lang, comment_author, comment_content)
                if result:
                    to_delete_indices.append(index)
            # 删除垃圾评论
            for index in reversed(to_delete_indices):
                comment_result.descendants = comment_result.descendants[:index] + comment_result.descendants[index + 1:]

        # 构造响应（Vercel 要求返回固定格式的字典）
        self.send_response(200)
        self.send_header("Content-type","application/json")
        self.send_header("Access-Control-Allow-Origin","*")
        self.end_headers()
        self.wfile.write(json.dumps(comment_result).encode("utf-8"))
        return

    def get_mastodon_comments(self, mastodon_token, mastodon_account):
        base_url = "https://mastodon.social/api/v1/accounts/lookup"
        encoded_params = urllib.parse.urlencode({
            "acct": mastodon_account
        })
        full_url = f"{base_url}?{encoded_params}"

        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {mastodon_token}"
        }

        req = urllib.request.Request(
            url=full_url,
            headers=headers,
            method="GET"
        )

        with urllib.request.urlopen(req, context=self._get_ssl_context()) as response:
            return json.loads(response.read().decode("utf-8"))

    def check_akismet_spam(self, akismet_token, akismet_blog_url, blog_lang, comment_author, comment_content):
        akismet_data = {
            "api_key": akismet_token,
            "blog": akismet_blog_url,
            "user_ip": "0.0.0.0",
            "comment_type": "comment",
            "comment_author": comment_author,
            "comment_content": comment_content,
            "blog_lang": blog_lang
        }
        encoded_data = urllib.parse.urlencode(akismet_data).encode("utf-8")

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Content-Length": str(len(encoded_data))
        }

        req = urllib.request.Request(
            url="https://rest.akismet.com/1.1/comment-check",
            data=encoded_data,
            headers=headers,
            method="POST"
        )

        with urllib.request.urlopen(req, context=self._get_ssl_context()) as response:
            return response.read().decode("utf-8").strip().lower() == "true"
