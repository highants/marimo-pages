import marimo

__generated_with = "0.17.8"
app = marimo.App(width="medium")

with app.setup:
    import marimo as mo
    from atproto import Client
    from datetime import datetime, timezone

@app.cell
def _():
    # Blueskyクライアント設定
    bsky_id = mo.ui.text(
        label="ユーザーハンドル：",
        value="",
        placeholder="your-hundle.bsky.social"
    )
    bsky_pw = mo.ui.text(
        label="アプリパスワード：",
        value="",
        placeholder="xxxx-xxxx-xxxx-xxxx",
        kind="password"
    )

    mo.md(f"""  
    {bsky_id}  
    {bsky_pw}
    """)

    return Client, bsky_id, bsky_pw, datetime, mo, timezone


@app.cell
def _(Client, bsky_id, bsky_pw, mo):
    # Blueskyクライアント初期化
    client = Client()
    client.login(bsky_id.value, bsky_pw.value)
    user_prof = client.get_profile(bsky_id.value) 

    mo.md(f"""
    <div style="display: flex; align-items: center;">
        <img src="{user_prof.avatar}" width="50" height="50" style="border-radius: 50%; margin-right: 10px;">
        <span>{user_prof.display_name}</span>
    </div>
    """)
    return (client,)


@app.cell
def _(datetime):
    def timestamp(created_at_str: str) -> str:
        """
        Blueskyのタイムスタンプ文字列をローカルタイムゾーンのYYYY/MM/DD HH:MM形式に変換します。

        Args:
            created_at_str: Blueskyの投稿から取得したISO 8601形式のタイムスタンプ文字列。
                            例: "2023-10-27T10:00:00.000Z"

        Returns:
            フォーマットされたローカルタイムの文字列。例: "2023/10/27 19:00"
        """
        # 'Z' を '+00:00' に置換して、datetime.fromisoformatがUTCとして正しく解析できるようにする
        dt_object_utc = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))

        # システムのローカルタイムゾーンに変換
        dt_object_local = dt_object_utc.astimezone()

        # 任意のフォーマットで文字列に再変換
        formatted_time = dt_object_local.strftime("%Y/%m/%d %H:%M")

        return formatted_time
    return (timestamp,)


@app.function
def uri_to_bluesky_link(uri: str) -> str:
    """
    BlueskyのURIを、BlueskyのWebインターフェースへのリンクに変換します。
    例: at://did:plc:example/app.bsky.feed.post/abcdefg
    -> <a href="https://bsky.app/profile/did:plc:example/post/abcdefg" target="_blank">投稿を見る</a>
    """
    parts = uri.split('/')
    if len(parts) >= 5 and parts[0] == 'at:' and parts[3] == 'app.bsky.feed.post':
        did = parts[2]
        rkey = parts[4] # 投稿ID
        link = f"https://bsky.app/profile/{did}/post/{rkey}"
        return link
    return uri


@app.cell
def _(datetime, mo):
    # 検索用インターフェイス

    search_keyword = mo.ui.text(
        label="検索ワード",
        value="",
        placeholder=""
    )

    search_user_handle = mo.ui.text(
        label="ユーザー指定",
        value="",
        placeholder="user.bsky.social"
    )

    search_mention_user = mo.ui.checkbox(
        label="メンション",
        value=False
    )

    search_start_datetime = mo.ui.datetime(
        label="期間指定：～から",
        value=datetime.now()
    )

    search_end_datetime = mo.ui.datetime(
        label="～まで",
        value=datetime.now()
    )

    lang_ja = mo.ui.checkbox(
        label="日本語のみ",
    )

    max_pages_setting = mo.ui.number(
        label="表示ページ数：",
        start=1,
        step=1
    )

    mo.md(f"""
        ## 投稿検索
        {search_keyword}  {search_user_handle} {search_mention_user}  
        {search_start_datetime}  {search_end_datetime}  {lang_ja}  
        {max_pages_setting}（1ページ20件）
    """)
    return (
        lang_ja,
        max_pages_setting,
        search_end_datetime,
        search_keyword,
        search_mention_user,
        search_start_datetime,
        search_user_handle,
    )


@app.cell
def _(
    client,
    lang_ja,
    max_pages_setting,
    mo,
    search_end_datetime,
    search_keyword,
    search_mention_user,
    search_start_datetime,
    search_user_handle,
    timestamp,
    timezone,
):
    def search_post():
            # 検索クエリ文字列を構築
            query_string = f"{search_keyword.value}"
    
            # メンション検索のみの場合の条件分岐
            if search_mention_user.value and search_user_handle.value:
                query_string += f" mentions:{search_user_handle.value}"
            elif search_user_handle.value: # ユーザー指定のみの場合
                query_string += f" from:{search_user_handle.value}"

            # ローカルタイムゾーンの日時をUTCに変換
            utc_start_dt = search_start_datetime.value.astimezone(timezone.utc)
            utc_end_dt = search_end_datetime.value.astimezone(timezone.utc)
    
            # UTCの日時をISO 8601形式（Z付き）でフォーマット
            start_date_str = utc_start_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
            end_date_str = utc_end_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

            # 検索クエリ文字列に日付範囲を追加
            query_string += f" since:{start_date_str} until:{end_date_str}"

            # チェックボックスの値に基づいて言語パラメータを設定
            lang_param = "ja" if lang_ja.value else ""

            posts_elements = []
            current_cursor = None
            page_count = 0
            max_pages = max_pages_setting.value

            while page_count < max_pages:
                res = client.app.bsky.feed.search_posts({"q": query_string, "lang": lang_param, "limit": 20, "cursor": current_cursor})

                if not res.posts:
                    break

                page_posts = []
                for post_view in res.posts:
                    created_at_str = post_view.record.created_at
                    post_uri = post_view.uri # 投稿URIを取得

                    # 投稿に埋め込み画像があるかチェック
                    embed_html = ""
                    if post_view.embed and hasattr(post_view.embed, 'images') and post_view.embed.images:
                        # 画像を横一列に並べるためのコンテナを追加
                        embed_html += '<div style="display: flex; overflow-x: auto; gap: 10px;">'
                        for image in post_view.embed.images:
                            embed_html += f'<a href="{image.fullsize}" target="_blank"><img src="{image.thumb}" style="max-height: 300px; object-fit: contain;"></a>'
                        embed_html += '</div>'

                    page_posts.append(mo.md(f"""
                    <div style="display: flex; align-items: center;">
                        <img src="{post_view.author.avatar}" width="50" height="50" style="border-radius: 50%; margin-right: 10px;">
                        <span><b>{post_view.author.display_name}</b>　{post_view.author.handle}</span>
                        <span style="margin-left: 10px;">| {timestamp(created_at_str)}</span>
                        <a href="{uri_to_bluesky_link(post_uri)}" target="_blank" style="margin-left: auto;">投稿を見る</a>
                    </div> 
                    <div style="font-family: 'Noto Sans JP'; font-weight: 350; font-size: 1.02em; color: black;">{mo.as_html(post_view.record.text)}</div>  
                    {embed_html}
                    """))

                posts_elements.append(mo.accordion(
                    {f"ページ {page_count + 1}": mo.vstack(page_posts)}
                ))

                current_cursor = res.cursor
                page_count += 1
                if current_cursor is None:
                    break

            return mo.vstack(posts_elements)
    search_post()
    return


if __name__ == "__main__":
    app.run()
