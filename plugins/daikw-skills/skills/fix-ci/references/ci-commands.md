# CI情報の取得

URLとremoteから特定した対象に、インストール済みCLIの対応コマンドを使う。
引数や機能差があればそのCLIのhelpを確認する。ログは必要部分に絞り、秘密を含む行を応答や成果物へ転載しない。

## GitHub

```sh
gh pr checks <pr-number> --repo <owner/repo>
gh run list --repo <owner/repo> --branch <branch>
gh run view <run-id> --repo <owner/repo> --log-failed
gh run watch <run-id> --repo <owner/repo>
```

PR/MRのheadとrunのhead SHAを照合する。対象commitと別のrunを混同しない。

## GitLab

```sh
glab ci view
glab ci trace <job-id>
```

GitLabのremoteが設定された対象repoで実行する。pipelineとjob、commitの関係は取得したmetadataで確認する。
CLIに必要なmetadataが出なければ、認証済みの読み取りAPIで対象IDを指定して取得する。

## ローカル再現

workflow / pipeline定義とpackage managerの既存scriptから実コマンドを確認する。
CI専用のサービスやsecretがなければローカル再現を省略した理由を示し、実行可能な代替検証を選ぶ。
エミュレータ導入や有料runnerの追加起動を、単なる確認コマンドの代わりに自動で始めない。
