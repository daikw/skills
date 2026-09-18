---
name: release
description: "GitHub リリースのノートを過去のスタイルと対象コミットから作成し、依頼に応じて下書き保存・公開を行う。バージョン番号はユーザーが指定し、自動算出しない。単純な gh release create だけで足りる場合には使わない。"
user-invocable: true
argument-hint: "[バージョンタグ (省略時: ノートを準備して確認)]"
allowed-tools:
  - Bash
  - Read
  - Write
  - AskUserQuestion
---

# GitHub リリース

対象 repo・タグ・commit と公開範囲を揃え、レビューできるリリースノートを作る。
公開は「リリースして」「公開して」等で明示された範囲だけ行う。ノート作成・下書きの依頼から公開を推定しない。既に同じ対象の公開を許可されていれば聞き直さない。

## バージョンと対象

- `$ARGUMENTS` や会話で指定されたバージョンを使う。タグ名を検証し、勝手に bump・prefix 変更しない。
- バージョンがなければ自動算出しない。許可された repo の過去リリースと対象履歴を調べてノートの下書きを進め、タグ作成や公開に必要な番号だけ確認する。
- 対象 repo は依頼・remote・GitHub 側の identity を照合し、以後の `gh release` 操作には `--repo` を明示する。認証情報を含む remote URL を出力しない。
- 対象 commit は会話・repo の release 方針・指定ブランチから確定し、完全な SHA に解決する。現在 checkout 中のブランチや `HEAD` を自動採用しない。候補が複数あり内容が変わる場合は、独立した準備を進めつつ対象を確認する。
- 同名タグ・release の存在を調べる。既存タグは annotated tag を含めて指す commit を解決し、意図した SHA と一致することを確認する。既存タグの移動・削除や、既存 release の上書きで不一致を解消しない。

## ノートを準備する

対象 repo の過去リリースの本文を読み、対象 commit に対する比較元タグを選ぶ。初回リリースや prerelease では、単に最新の日付のタグを比較元にしない。
必要な ref がローカルにない場合だけ取得し、比較元から確定した SHA までの履歴・差分を確認する。独立した読み取りは並列にできるが、対象確定とそれに依存する履歴収集は順に行う。

コミットを利用者に意味のある変更単位でまとめ、過去の言語・形式を踏襲する。prefix だけで内容を決めず、破壊的変更や必要な移行を実際の差分から確認する。
比較元がある場合は実在する repo/tag の Full Changelog リンクを付ける。新しいタグが未作成なら公開後にリンクを照合する。

本文はローカルの Markdown ファイルに保存する。既存ファイルの用途を確認してから書き、本文をシェル文字列・command substitution へ埋め込まない。
公開前に repo、タグ、SHA、ノート、draft/prerelease と添付物の有無をレビューできる形にする。依頼されていない添付・discussion・latest 指定を追加しない。

## 作成と公開

使用版の `gh release create --help` で必要な flag を確認する。以下は値を確定し、許可範囲を確認した後の形。変数の値は検証して引用し、コマンドとして再解釈しない。

リモートの既存タグが意図した SHA を指す場合:

```bash
gh release create "$release_tag" \
  --repo "$release_repo" \
  --verify-tag \
  --title "$release_tag" \
  --notes-file "$release_notes_file"
```

新しいタグを作ることまで許可されている場合は、存在しないことを直前に確認し、`--verify-tag` の代わりに `--target "$release_commit_sha"` を指定する。既存タグでは `--target` がタグを付け替える手段になると考えない。
GitHub 上の下書き作成を依頼された場合は `--draft`、prerelease を依頼された場合は `--prerelease` を付ける。ローカルでノートを準備するだけなら create を呼ばない。

作成がタイムアウトした場合は、同名 release とタグの現在状態を先に確認する。不明なまま作成を再実行しない。

## 完了確認

`gh release view "$release_tag" --repo "$release_repo"` で対象 URL、本文、draft/prerelease、添付物を再取得して照合する。リモートタグが意図した SHA を指すことも確認する。`targetCommitish` の表示だけでは既存タグの参照先確認を代替できない。

URL、タグ、SHA、下書き/公開状態と検証結果を返す。ノートだけを作成した場合はファイルと未確定事項を返し、公開済みと報告しない。
