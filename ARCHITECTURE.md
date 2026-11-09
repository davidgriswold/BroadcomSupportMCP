# 技術仕様: Broadcom Support MCP Server

## 概要

Broadcom Support Portal のナレッジベース検索機能を MCP (Model Context Protocol) ツールとして提供するサーバー。
FastMCP フレームワークを使用し、stdio（デフォルト）および
Streamable HTTP トランスポートに対応する。

## アーキテクチャ

```
MCP Client
  │  stdio (JSON-RPC)
  ▼
server.py (FastMCP)
  │
  ▼
client.py (BroadcomClient)
  │
  ├─ POST support.broadcom.com/.../suRefreshToken  → JWT 取得
  │
  ├─ POST searchunify.broadcom.com/search/searchResultHL  → 検索
  │
  └─ GET  techdocs.broadcom.com/...  → 記事取得 + HTML→Markdown 変換
```

## Transport Architecture (English)

The server supports two MCP transports using FastMCP's native
transport implementations.

| Transport | Usage | Default |
|-----------|-------|---------|
| stdio | Local MCP clients | Yes |
| Streamable HTTP | Network-connected MCP clients | No |

### Request Flow

```text
Local MCP Client
    |
    | stdio (JSON-RPC)
    |
    +------------------+
                       |
Remote MCP Client      |
    |                  |
    | Streamable HTTP  |
    |                  |
    +------------------+
                       |
                       v
                 FastMCP Server
                       |
                       v
                 BroadcomClient
                       |
                 +-----+------+
                 |            |
                 v            v
          SearchUnify     Article Retrieval
```

### HTTP Configuration

HTTP mode is enabled using `--transport http`.

- Default bind address: `127.0.0.1`
- Default port: `8000`
- Default endpoint: `/mcp`
- Authentication: Not implemented by this application

The `--host` and `--port` arguments configure the listener.

The server binds to localhost by default to avoid unintentionally
exposing its tools to other network clients.

For remote deployment, access control must be provided separately.

### Compatibility

The stdio transport remains the default to preserve compatibility
with existing MCP client configurations.

Both transports expose the same `search_documentation` and
`read_documentation` tools.

Transport selection does not change the Broadcom Support API
integration or its dependency on undocumented SearchUnify endpoints.

## 検索 API の仕組み

Broadcom Support Portal の検索は SearchUnify というサードパーティの検索プラットフォームで実装されている。
ポータルのフロントエンドは SPA で、検索結果は JavaScript 実行後に API から非同期取得される。

### JWT トークン取得

検索 API の呼び出しには JWT トークン（authtoken）が必要。

- エンドポイント: `POST https://support.broadcom.com/web/ecx/search/-/searchUnify/suRefreshToken`
- Content-Type: `application/json`
- リクエストボディ:
  ```json
  {
    "user_id": "support_portal_su_user",
    "firstname": "support_portal_su_user",
    "loggedIn": false
  }
  ```
- レスポンス: JWT 文字列（RS256 署名、有効期限約60分）

JWT ペイロード例:
```json
{
  "firstname": "support_portal_su_user",
  "tokenFor": "search_results_ecx",
  "loggedIn": false,
  "aud": ["Broadcom Users"],
  "iss": "Broadcom",
  "sub": "Support Widget"
}
```

### 検索リクエスト

- エンドポイント: `POST https://searchunify.broadcom.com/search/searchResultHL`
- Content-Type: `application/json`
- 主要パラメータ:

| パラメータ | 値 | 説明 |
|-----------|-----|------|
| `searchString` | (動的) | 検索クエリ |
| `uid` | `d042dbba-f8c4-11ea-beba-0242ac12000b` | SearchUnify クライアント ID（固定） |
| `accessToken` | `b72cbbab2728563ec74e93aa3223a7dc` | API アクセストークン（固定） |
| `authtoken` | (動的) | 上記で取得した JWT |
| `resultsPerPage` | 10 | 1ページあたりの結果数 |
| `language` | `en` | 言語フィルタ |
| `aggregations` | `[{"type":"language","filter":["en"]}]` | ファセットフィルタ |

### 検索レスポンス

```json
{
  "statusCode": 200,
  "message": "Success",
  "result": {
    "total": 8124,
    "max_score": 505.2,
    "hits": [
      {
        "_id": "https://techdocs.broadcom.com/...",
        "_score": 505.2,
        "highlight": {
          "title.en": ["___su-highlight-start___Upgrading___su-highlight-end___ the vSAN Cluster"],
          "content.en": ["...highlighted snippet..."]
        }
      }
    ]
  }
}
```

- `_id`: 記事の URL
- `highlight.title.en`: ハイライト付きタイトル
- `highlight.content.en`: ハイライト付きスニペット
- ハイライトマーカー `___su-highlight-start___` / `___su-highlight-end___` はパース時に除去

## 記事取得

`read_documentation` ツールは通常の HTTP GET で記事ページを取得し、BeautifulSoup で HTML をパースして Markdown に変換する。
SearchUnify API は使用しない。

## ディレクトリ構成

```
broadcom-support-mcp-server/
├── broadcom_support_mcp_server/
│   ├── __init__.py       # エントリポイント (main)
│   ├── server.py         # FastMCP サーバー定義、ツール登録
│   ├── client.py         # HTTP クライアント (SearchUnify API + 記事取得)
│   ├── models.py         # Pydantic モデル
│   └── formatters.py     # Markdown フォーマッター
├── tests/
│   ├── test_models.py
│   └── test_formatters.py
├── pyproject.toml
└── README.md
```

## 依存関係

| パッケージ | 用途 |
|-----------|------|
| fastmcp | MCP サーバーフレームワーク |
| mcp[cli] | MCP プロトコル実装 |
| httpx | 非同期 HTTP クライアント |
| beautifulsoup4 | HTML パーサー |
| pydantic | データモデル |
