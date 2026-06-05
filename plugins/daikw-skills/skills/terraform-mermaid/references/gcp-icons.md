# GCP リソース → Mermaid ノードスタイル マッピング

Mermaid flowchart では画像埋め込みが限定的なため、emoji + サブグラフの色分けで表現する。

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

| 依存の種類 | Mermaid 記法 | 用途 |
|-----------|-------------|------|
| データフロー | `-->` | バケット参照、Pub/Sub 購読 |
| 認証/権限 | `-.->` | SA バインディング、KMS 鍵参照 |
| 構成依存 | `==>` | イメージ参照、環境変数注入 |
