# Coding Agent Spec Report

Date: <確認時点>
Targets: <依頼された製品・version・CLI/アプリ等のsurface>
Topics: <仕様上の問い>

## Summary

問いへの回答と、互換性や実装判断に影響する点。

## Agent Details

対象ごとに該当トピックのみ記載する。

| 論点 | 確認する内容 |
|---|---|
| Hooks | イベント、入力schema、出力制御、exit code、対象version |
| Config | 設定元、読み込み順、override、schema |
| MCP | 設定と接続、利用可能な能力、権限、制限 |
| CLI | 正確なコマンド・フラグ、入力・出力、version |
| Extensions | skill/agentの発見、適用、参照、仕様差 |
| Sessions | 保存と再開の範囲、既存sessionへの適用 |

## Cross-Agent Comparison

比較依頼のときに使い、列は実際の対象だけにする。

| Feature | <Agent A / version> | <Agent B / version> | 根拠・条件 |
|---|---|---|---|
| <依頼された比較軸> | … | … | … |

## Assumptions

公式記載・実装・実測から推測した部分を区別する。

## Unknown / Needs Verification

不明な論点、調べた範囲、確定に必要な証拠。

## Sources

URLまたは実装箇所、version/確認時点、どの主張を支えるか。
