# Broadcom Support MCP Server

Broadcom Support Portal のナレッジベース記事を検索・取得するための MCP サーバーです。
VMware、Tanzu、Cybersecurity など Broadcom 製品群のドキュメントにアクセスできます。

## Kiro での設定

`.kiro/settings/mcp.json` に以下を追加してください。

### ローカル開発版を使う場合

```bash
# 依存関係のインストール
uv venv broadcom-support-mcp-server/.venv
uv pip install -e broadcom-support-mcp-server -p broadcom-support-mcp-server/.venv/bin/python
```

```json
{
  "mcpServers": {
    "broadcom-support": {
      "command": "/path/to/broadcom-support-mcp-server/.venv/bin/broadcom-support-mcp-server",
      "args": [],
      "disabled": false,
      "autoApprove": [
        "search_documentation",
        "read_documentation"
      ]
    }
  }
}
```

`/path/to/` は実際のパスに置き換えてください。

## 提供するツール

### `search_documentation`

Broadcom Support のナレッジベースを検索します。

| パラメータ | 型 | 必須 | デフォルト | 説明 |
|-----------|------|------|-----------|------|
| `query` | string | ✅ | - | 検索クエリ |
| `segment` | string | - | `all` | 製品セグメント |

### `read_documentation`

指定 URL のドキュメント記事を取得し、Markdown 形式で返します。

| パラメータ | 型 | 必須 | 説明 |
|-----------|------|------|------|
| `url` | string | ✅ | 記事の URL |

## 使用例

Kiro のチャットで以下のように質問できます:

- 「vSphere のアップグレード手順を検索して」
- 「ESXi のネットワーク設定について調べて」
- 「Tanzu Kubernetes のトラブルシューティング記事を探して」

## 開発

```bash
# venv作成と依存関係のインストール
uv venv broadcom-support-mcp-server/.venv
uv pip install -e "broadcom-support-mcp-server[dev]" -p broadcom-support-mcp-server/.venv/bin/python

# テストの実行
broadcom-support-mcp-server/.venv/bin/pytest broadcom-support-mcp-server/tests/ -v
```

## 技術仕様

SearchUnify API の仕組みや内部アーキテクチャについては [ARCHITECTURE.md](./ARCHITECTURE.md) を参照してください。

## ライセンス

Apache License 2.0
