# Investment

## Python 環境

Python 3.11 と [uv](https://docs.astral.sh/uv/) を使用します。依存パッケージは `pyproject.toml` で管理し、実際にインストールする全パッケージのバージョンとハッシュは `uv.lock` に固定しています。

環境の作成・同期:

```sh
uv sync --locked
```

## Lint

Ruff でPythonコードをチェックします。

```sh
uv run --locked ruff check .
```

## 依存パッケージの脆弱性チェック

既知の脆弱性がないか確認するには、プロジェクトの仮想環境で `pip-audit` を実行します。

```sh
uv run --locked pip-audit
```

脆弱性が見つかった場合は、影響を受けるパッケージと修正版の情報が表示されます。修正する場合は、対象パッケージを更新してから再度チェックしてください。

GitHub Actions でも、push・pull request 時および毎週月曜日に自動実行します。利用する Actions は full commit SHA で固定しています。

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
