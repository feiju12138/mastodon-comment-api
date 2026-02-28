from fastapi import FastAPI, Request, HTTPException
import requests
import os

app = FastAPI()

@app.get("/")
def read_root():
    return "ok"

@app.get("/api")
def get_item(request: Request):

    # 读取环境变量
    mastodon_token = os.getenv("MASTODON_TOKEN")
    mastodon_account = os.getenv("MASTODON_ACCOUNT")
    akismet_token = os.getenv("AKISMET_TOKEN")
    akismet_blog_url = os.getenv("AKISMET_BLOG_URL")
    if not mastodon_token or not mastodon_account:
        raise HTTPException(
            status_code=500,
            detail="env error"
        )

    # 获取请求参数
    param_str = request.query_params
    toot_id = param_str.get("toot_id")
    current_url = param_str.get("current_url")
    if not toot_id or not current_url:
        raise HTTPException(
            status_code=400,
            detail="param error"
        )

    # 发送请求 根据toot_id获取评论列表
    comment_result = get_mastodon_comments(mastodon_token, mastodon_account, toot_id)

    # 合规判定
    if akismet_token and akismet_blog_url:
        # 垃圾评论索引
        to_delete_indices = []
        for index, descendant in enumerate(comment_result["descendants"]):
            # 提取内容
            comment_content = descendant.content
            comment_author = descendant.account.username
            blog_lang = descendant.language
            # 发送请求 假别是否是垃圾评论
            result = check_akismet_spam(akismet_token, akismet_blog_url, blog_lang, comment_author, comment_content)
            if result:
                to_delete_indices.append(index)
        # 删除垃圾评论
        for index in reversed(to_delete_indices):
            del comment_result["descendants"][index]

    return comment_result


def get_mastodon_comments(mastodon_token, mastodon_account, toot_id):

    return requests.get(
        url=f"https://mastodon.social/api/v1/statuses/{toot_id}/context",
        params={
            "acct": mastodon_account
        },
        headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {mastodon_token}"
        },
        timeout=10
    ).json()


def check_akismet_spam(akismet_token, akismet_blog_url, blog_lang, comment_author, comment_content):

    res = requests.post(
        url="https://rest.akismet.com/1.1/comment-check",
        data={
            "api_key": akismet_token,
            "blog": akismet_blog_url,
            "user_ip": "0.0.0.0",
            "comment_type": "comment",
            "comment_author": comment_author,
            "comment_content": comment_content,
            "blog_lang": blog_lang
        },
        timeout=10
    ).text

    return res.strip().lower() == "true"
