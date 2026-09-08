# /goalの対象インターフェース

このスキルの成果物は、ユーザーがCodex CLIへ貼り付ける `/goal <objective>` の文章である。
生成自体は、goalの作成・開始・状態変更を行わない。

pause/resume/clear、設定キー、lifecycle名、budget指定等を追加で案内するときは、対象のインストール済みCLIのhelp・同梱資料と、対応する公式仕様を確認する。
API、アプリ、CLIのgoal機能に同じ操作名があるとは限らない。
現在の実行環境にgoal用toolが見えているだけでは、CLIのslash command仕様の証拠にならない。

確認できない操作・設定方法は未知と示し、過去の記憶から実行例を作らない。
プロンプトを作るためにモデル、config、稼働中のgoalを変更しない。

公式の入口:

- [Codex CLI slash commands](https://developers.openai.com/codex/cli/slash-commands)
- [Codex use cases](https://developers.openai.com/codex/use-cases)

リンクは探索の入口であり、未取得のページを特定の機能の根拠として扱わない。
