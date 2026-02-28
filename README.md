
# Mastodon + Akismet = Comments

- [x] 无需科学

- [x] 垃圾评论过滤

- [x] 允许使用`mastodon.social`实例

## Vercel Environment Variables

> `MASTODON_DOMAIN`：形如`mastodon.social`的Mastodon实例域名，缺省值为`mastodon.social`
>
> `MASTODON_TOKEN`：Mastodon实例获取的令牌
>
> `MASTODON_ACCOUNT`：形如`feiju@mastodon.social`的用户名
>
> `AKISMET_TOKEN`：[Akismet](https://akismet.com/)获取的令牌，用于删除垃圾评论，可选
>
> `AKISMET_BLOG_URL`：[Akismet](https://akismet.com/)API发送请求时携带的`blog`参数（[API文档](https://akismet.com/developers/detailed-docs/comment-check/)），可选（如果`AKISMET_TOKEN`没有传递，则`AKISMET_BLOG_URL`无需传递，反之必须传递）

## Example

> `toot_id`：嘟文编号

```http request
GET https://my-mastodon-comment-api.vercel.app/api?toot_id=116146779087003500
```

## Error

- `env error`：Vercel环境变量缺少`MASTODON_TOKEN`或`MASTODON_ACCOUNT`
- `param error`：请求参数param缺少`toot_id`
