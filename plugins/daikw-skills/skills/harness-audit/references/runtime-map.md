# 読込経路の確認

以下は候補の位置。指定されたハーネスの欄だけ参照し、実際の loader・現在のツールから編集元を確かめる。
各 root を列挙したことは、全内容の読み込み許可ではない。

## Codex

- グローバル指示と、cwd に適用される AGENTS.md / override / fallback 文書。
- user/repo の skill root と、設定された plugin marketplace が指す編集元・installed path。
- `config.toml` はまず存在・メタデータを確認し、必要な model/profile/skills/plugin/hook/permission 項目だけを抽出する。
- plugin cache と source checkout を区別する。使える plugin CLI の list/詳細で有効な配布先を確かめる。
- memory はそのセッションで指定された index と更新口を起点に、現在の問いに関係する entry を辿る。

## Claude Code

- user と project の CLAUDE.md、適用される rules、user/repo の skill root。
- skills/commands/agents と plugin source/install path の関係。
- settings の hooks・permissions・enabledPlugins など、必要な項目だけを抽出する。
- plugin registry は有効な名前・source・install path・version の範囲を読む。認証や環境を出力しない。
- project memory は対象 project の index を起点にする。他 project へ広げる理由が必要。

## 確認の際の注意

- path・mtime・存在は filesystem の証拠で、読込や挙動の証拠とは異なる。
- シェルを使う場合は `rg --files` 等で名前を絞り、必要なファイル・設定項目だけ読む。
- plugin や hook の list/health と、実作業の完了は区別する。
- 個人の disabled 設定、archived 状態、過去の拒否や停止理由を、無断で修復すべき欠陥としない。
- 新しい process/thread で読込を確かめる。現在走っている session の振る舞いを、適用後の証拠にしない。
