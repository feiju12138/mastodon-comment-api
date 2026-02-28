import json
import requests
import os


def handler(event, context):
    """
    读取环境变量
    """
    mastodon_token = os.environ.get("MASTODON_TOKEN")
    mastodon_account = os.environ.get("MASTODON_ACCOUNT")
    akismet_token = os.environ.get("AKISMET_TOKEN")
    akismet_blog_url = os.environ.get("AKISMET_BLOG_URL")
    if not mastodon_token or not mastodon_account:
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "text/plain",
                "Access-Control-Allow-Origin": "*"
            },
            "body": "env error"
        }

    """
    获取请求参数
    """
    toot_id = event["queryStringParameters"].get("toot_id")
    current_url = event["queryStringParameters"].get("current_url")
    if not toot_id or not current_url:
        return {
            "statusCode": 400,
            "headers": {
                "Content-Type": "text/plain",
                "Access-Control-Allow-Origin": "*"
            },
            "body": "param error"
        }

    # 根据tootid获取评论列表
    comment_result = requests.get(
        "https://mastodon.social/api/v1/accounts/lookup",
        headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {mastodon_token}"
        },
        params={
            "acct": mastodon_account
        }).json()

    # 合规判定
    if akismet_token and akismet_blog_url:
        # 不合规的评论索引
        to_delete_indices = []
        for index, descendant in enumerate(comment_result.descendants):
            # 提取内容
            comment_content = descendant.content
            comment_author = descendant.account.username
            blog_lang = descendant.language
            # 找出不合规的评论
            akismet_data = {
                "api_key": akismet_token,
                "blog": akismet_blog_url,
                "user_ip": "0.0.0.0",
                "comment_type": "comment",
                "comment_author": comment_author,
                "comment_content": comment_content,
                "blog_lang": blog_lang
            }
            result = requests.post("https://rest.akismet.com/1.1/comment-check", data=akismet_data).text
            if result == "true":
                to_delete_indices.append(index)
        # 删除不合规的评论
        for index in reversed(to_delete_indices):
            comment_result.descendants = comment_result.descendants[:index] + comment_result.descendants[index + 1:]

    # 构造响应（Vercel 要求返回固定格式的字典）
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps(comment_result)
    }
