# GCP リソース → Mermaid ノードスタイル マッピング

既存図のスタイルを踏襲する場合の対応表。emojiと色は補助とし、ラベル・形状でも意味を区別する。

## リソースカテゴリとアイコン

| カテゴリ | GCP リソース | Emoji | Mermaid ノード形状 |
|----------|-------------|-------|-------------------|
| Compute | Cloud Run | 🚀 | 角丸四角 `([ ])` |
| Database | Firestore | 🗄️ | 円筒 `[( )]` |
| Messaging | Pub/Sub | 📨 | 六角形 `{{ }}` |
| Storage | GCS | 📦 | 四角 `[ ]` |
| Security | KMS | 🔐 | ひし形 `{ }` |
| Security | Cloud Armor | 🛡️ | ひし形 `{ }` |
| Registry | Artifact Registry | 🏗️ | 四角 `[ ]` |
| Network | Load Balancer | 🌐 | 円 `(( ))` |
| Auth | IAP | 🔑 | ひし形 `{ }` |
| AI | Vertex AI | 🧠 | 角丸四角 `([ ])` |

## サブグラフの色分け（classDef）

```mermaid
classDef compute fill:#4285F4,stroke:#1967D2,color:#fff
classDef database fill:#F4B400,stroke:#E37400,color:#fff
classDef messaging fill:#0F9D58,stroke:#0B8043,color:#fff
classDef storage fill:#DB4437,stroke:#C5221F,color:#fff
classDef security fill:#AB47BC,stroke:#8E24AA,color:#fff
classDef registry fill:#FF7043,stroke:#E64A19,color:#fff
classDef external fill:#9E9E9E,stroke:#616161,color:#fff
```

## 接続線の種別

線種は根拠となる宣言の意味に合わせる。単なる値の参照を実データフローとして描かない。

| 依存の種類 | Mermaid 記法 | 用途 |
|-----------|-------------|------|
| データフロー | `-->` | 入出力や購読設定で方向を確かめた接続 |
| 認証/権限 | `-.->` | SA バインディング、KMS 鍵参照 |
| 構成依存 | `==>` | イメージ参照、環境変数注入 |
