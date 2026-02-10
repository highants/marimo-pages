import marimo

__generated_with = "0.19.4"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Blueskyツールセット
    """)
    return


@app.cell(hide_code=True)
def _():
    import marimo as mo
    import micropip
    await micropip.install("atproto")
    from atproto import Client, models, client_utils
    return Client, mo


@app.cell
def _(mo):
    mo.md(r"""
    ## ログイン
    """)
    return


@app.cell
def _(mo):
    # Blueskyログイン
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
    mo.vstack([
        bsky_id,
        bsky_pw
    ])
    return bsky_id, bsky_pw


@app.cell
def _(Client, bsky_id, bsky_pw, mo):
    # Blueskyクライアント初期化 & ログインユーザーの表示
    client = Client()
    client.login(bsky_id.value, bsky_pw.value)
    user_prof = client.get_profile(bsky_id.value) 

    mo.vstack([
        mo.md("### ログイン中のユーザー"),
        mo.hstack([ 
            mo.image(user_prof.avatar).style({
                "width": "50px", 
                "height": "50px", 
                "border-radius": "50%", 
                "margin-right" : "10px",
                "overflow": "auto"
            }),
            mo.md(f"{user_prof.display_name} ({user_prof.handle})"),
        ], justify="start", align="center")
    ])
    return


if __name__ == "__main__":
    app.run()
