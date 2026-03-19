# Project Structure

```
BroadcomSupportMCPServer-main/
├── broadcom_support_mcp_server/   # メインパッケージ
│   ├── __init__.py                # エントリポイント (main 関数)
│   ├── server.py                  # FastMCP サーバー定義・ツール登録
│   ├── client.py                  # HTTP クライアント (SearchUnify API + 記事取得)
│   ├── models.py                  # Pydantic モデル
│   └── formatters.py              # HTML→Markdown フォーマッター
├── tests/
│   ├── test_models.py
│   └── test_formatters.py
├── pyproject.toml
├── README.md
└── ARCHITECTURE.md
```

## 各モジュールの役割

- `server.py`: MCP ツール (`search_documentation`, `read_documentation`) を定義・登録する。ここがエントリポイントに近い層。
- `client.py`: 外部 API との通信を担当。JWT 取得 → SearchUnify 検索 → 記事 HTML 取得の流れを実装。
- `models.py`: API レスポンスや内部データ構造を Pydantic で定義。
- `formatters.py`: BeautifulSoup で HTML をパースし Markdown に変換するロジック。

## 規約

- 新しい外部 API 通信は `client.py` に追加する
- データモデルは `models.py` で Pydantic を使って定義する
- フォーマット・変換ロジックは `formatters.py` に集約する
- テストは `tests/` 以下に配置し、pytest で実行する
