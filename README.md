# Investment

## Python 環境

Python 3.11 と [uv](https://docs.astral.sh/uv/) を使用します。依存パッケージは `pyproject.toml` で管理し、実際にインストールする全パッケージのバージョンとハッシュは `uv.lock` に固定しています。

環境の作成・同期:

```sh
uv sync --locked
```

## パッケージの更新

特定のパッケージを更新する場合は、パッケージ名を指定してロックを更新し、環境に反映します。

```sh
uv lock --upgrade-package pandas
uv sync --locked
```

すべての依存パッケージを更新する場合:

```sh
uv lock --upgrade
uv sync --locked
```

依存パッケージの追加・削除には `uv add <パッケージ名>` / `uv remove <パッケージ名>` を使ってください。コマンドで更新された `pyproject.toml` と `uv.lock` を両方コミットし、`uv.lock` は直接編集しないでください。
