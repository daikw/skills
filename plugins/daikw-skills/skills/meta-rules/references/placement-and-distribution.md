# 配置・移行・配布

配置は公開性、ハーネス中立性、機微性で決める。依頼と既存構成から決まることはそのまま採用する。
公開範囲や運用が変わり、既存指示では判断できない場合は、作業可能な部分を進めつつ確認する。

| 系統 | 正本と配布 |
|---|---|
| Public | この repo の `plugins/daikw-skills/skills/<name>/`。機微情報なし。manifest が指す各ハーネスの plugin として配布 |
| Private | chezmoi の `dot_agents/skills/<name>/` と `dot_claude/skills/<name>/`。生成先はそれぞれ `~/.agents/skills/` と `~/.claude/skills/` |
| Repo-local | 当該 repo のハーネスが読む skill root。プロジェクト固有の運用を user-global に重複させない |
| 検証中 | 検証プロジェクトの discovery 外（例: `tmp-skills/`）。配置だけで有効化済みとしない |

Public と Private は片方専用の明示指示がなければ両ハーネスを対象とする。
Private の両コピーには必要な同梱資料も配布し、Codex の `agents/openai.yaml` は共通/Codex 側だけに置く。
既存の意図的な差分や片側専用の連携を、名前の一致だけで統一・増設しない。
公開 skill の内容を chezmoi へコピーせず、chezmoi は bootstrap と私有内容を所有する。

変更前に manifest、installed path、remote URL、archive 状態、直近 commit から active source を確認する。
cache・生成物・古い checkout は正本にしない。distribution 更新は実際の plugin/chezmoi の更新経路で行う。
配布後に名前が見えること、適切な依頼で選択されること、参照と実行が成功することを別々に確認する。

## リネーム・移行・削除

- 呼び出し元、他 skill/rules の参照、既存の呼称を対象を絞って確認する。
- 有効な呼び方を変える場合は移行先を示し、必要なら実在する alias 機構を使う。架空の alias を作らない。
- 第三者由来の本文・catalog・素材は出典とライセンスを維持する。ユーザー管理の入口と upstream データを区別する。
- 削除対象を同定し、適用される退避方針に従って復元可能にする。
- 名前の類似、古い mtime、無効化状態だけで不要と判定しない。
- 同じ知識の複数配布と、二つの異なる技能の重複を区別する。

## 公開と適用

公開 source に実機IP・内部hostname・個人情報・組織固有ID・秘密を含めない。例は匿名化し、実値は private/repo-local へ置く。
script の呼出しは loader が示した skill root または現在読んだ SKILL.md の親を基準に解決する。
plugin の固定cache版や特定ハーネスの user-level パスを正本扱いしない。

対象だけを適用し、無関係な destination drift を保全する。既存の invocation policy と permission は本文編集で暗黙に変更しない。
source の commit と、各ハーネスの再読込・新規セッション検証を区別して報告する。
