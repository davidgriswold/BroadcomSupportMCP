# Tech Stack

## Language & Runtime

- Python >= 3.10

## Frameworks & Libraries

- `fastmcp` >= 2.14.0: MCP サーバーフレームワーク
- `mcp[cli]` >= 1.23.0: MCP プロトコル実装
- `httpx` >= 0.27.0: 非同期 HTTP クライアント
- `beautifulsoup4` >= 4.12.0: HTML パーサー（記事取得・変換用）
- `pydantic` >= 2.0.0: データモデル・バリデーション

## Build System

- `hatchling`: ビルドバックエンド
- `uv`: パッケージ管理・仮想環境

## Dev Dependencies

- `pytest` >= 9.0.2: テストフレームワーク

## Common Commands

```bash
# 仮想環境の作成と依存関係インストール
uv venv .venv
uv pip install -e ".[dev]" -p .venv/bin/python

# テスト実行
.venv/bin/pytest tests/ -v

# サーバー起動（stdio トランスポート）
.venv/bin/broadcom-support-mcp-server
```

## Transport

stdio (JSON-RPC) で動作する。MCP クライアントからサブプロセスとして起動される。
