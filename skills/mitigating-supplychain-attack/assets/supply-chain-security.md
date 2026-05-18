# Supply Chain Security

## 目的

AI エージェントが依存追加・一時実行・ベースイメージ変更を通じて、サプライチェーン攻撃を誘発・拡大しないことを最優先とする。

## 基本原則

- 依存追加・更新・ベースイメージ変更は、新しい第三者コードに実行権を与える行為として扱う。
- 既存依存、標準ライブラリ、既存の社内イメージで解決できるなら新規依存を増やさない。
- 推測でパッケージ名、Docker イメージ名、インストール手順を生成しない。
- 不明な場合は fail closed。安全性を確認できない依存は追加しない。
- `security.md` の一般セキュリティ要件に加えて、本ルールを独立に適用する。

## 禁止事項

- `npx`, `bunx`, `pnpm dlx`, `uvx` など、一回限りの外部コード実行ランチャーの使用
- `latest`, `*`, `x`, `^`, `~`, 範囲指定、Git URL、GitHub shorthand、HTTP(S) URL を使った外部依存追加
- `package.json` / `pyproject.toml` だけを変更し、対応する lockfile を更新しないこと
- `--ignore-scripts=false`, `npm_config_ignore_scripts=false`, `enableScripts=true` など install script 保護の緩和
- `FROM node:22`, `FROM ubuntu:latest` のような tag-only / latest / implicit latest の Docker ベースイメージ指定
- `curl | sh` やリモート install script の無検証実行

## Node.js 依存追加ルール

1. 依存追加は `pnpm add --save-exact <pkg>@<version>` を優先する
2. pnpm 移行前で npm を使う場合でも `npm install --save-exact <pkg>@<version>` を使う
3. `package.json` と `pnpm-lock.yaml` または `package-lock.json` を同一変更で更新する
4. 同一パッケージ配下で lockfile を混在させない
5. `packageManager` フィールドは固定し、意図なく変更しない

依存を追加する前に、必ず以下を確認すること:

- パッケージ名は公式ドキュメントまたは公式 registry 上の正確な名前と一致している
- 目的の有名パッケージに対する typo ではない
- 公式リポジトリ URL、メンテナ、公開期間、更新履歴に不自然な点がない
- 既存依存で代替できない理由がある

## Python 依存追加ルール

1. 依存追加は `uv add '<pkg>==<version>'` を優先する
2. `pyproject.toml` と `uv.lock` を同一変更で更新する
3. VCS / URL / path 依存は、既存方針として必要な場合を除いて追加しない
4. PyPI 上の公式 URL、公開者、更新履歴を確認する
5. バージョン指定は固定 (`==`) を原則とする

## install script / lifecycle script

- `preinstall`, `install`, `postinstall`, `prepare` は高リスクとして扱う
- install script を通すために保護設定を緩めない
- 新規依存に lifecycle script がある場合は、何が実行されるかを確認する
- script 実行が不可避な場合のみ、その必要性と影響範囲を説明する

## Docker ルール

- 外部ベースイメージは必ず `tag@sha256:<digest>` で固定する
- `latest` とタグ省略は禁止
- build stage / runtime stage の両方を個別に digest pinning する
- `FROM ${BASE_IMAGE}` のような変数展開は、コミットされた値が digest pinning 済みと確認できる場合のみ許可する
- 公式または組織管理のイメージを優先する
- Dockerfile 内でリモートスクリプトを実行する場合は、同じ変更で checksum または signature 検証を入れる

## lockfile 整合性

- manifest と lockfile は常に整合していなければならない
- install / lock 更新が失敗した場合、manifest 変更だけを残して終了してはいけない
- 依存を削除・更新した場合も lockfile を必ず更新する

## エージェントの完了条件

依存追加・更新、または Docker ベースイメージ変更を行った場合、完了条件は以下:

- 新規依存または新規イメージの理由を説明できる
- 固定バージョンまたは digest pinning が入っている
- lockfile が更新されている
- 未確認事項がある場合は `UNKNOWN` として明示している
