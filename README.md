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


## Streamable HTTP Transport (English)

In addition to the default stdio transport, the server supports
Streamable HTTP for network-connected MCP clients.

### Starting the server

Install dependencies from the repository root:

```bash
uv sync
```

Start with the default stdio transport:

```bash
uv run broadcom-support-mcp-server
```

Start with Streamable HTTP:

```bash
uv run broadcom-support-mcp-server --transport http
```

The default HTTP endpoint is:

`http://127.0.0.1:8000/mcp`

To configure the listening interface and port:

```bash
uv run broadcom-support-mcp-server \
  --transport http \
  --host 127.0.0.1 \
  --port 8080
```

### Connecting remote MCP clients

Configure an MCP client that supports Streamable HTTP to connect to
the server's `/mcp` endpoint.

The server must be reachable from the MCP client. Binding to
`127.0.0.1` allows local connections only.

### Security

HTTP mode does not configure client authentication.

Do not expose an unauthenticated MCP server directly to the
internet. For remote access, use an appropriately secured network
and an authenticated reverse proxy or other access-control layer.

The server also relies on undocumented Broadcom SearchUnify
interfaces, which may change without notice.

### Running tests

```bash
uv run pytest -q
```

The CLI tests verify transport selection, configuration, and
argument validation without starting a network listener.

## ライセンス

Apache License 2.0
