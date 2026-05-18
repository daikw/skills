# 並列編集プロトコル

## 基本原則

ファイル単位の予約より**責務境界での分割**を優先。jj で並列編集を行う。

## jj の利用

```bash
# Coordinator がエージェントごとに workspace 作成
jj workspace add ../ws-<agent-name>
# bookmark: agent/<name>/<task-id>

# 統合: 各 change を integration change に rebase
jj rebase -s <agent-change> -d integration/<task-id>
# テスト実行 → 通ったもののみ統合

# グリーンになったら main へ反映
# ロールバック: jj op undo
```

## 競合時

1. エージェントが最新 integration change に rebase
2. 解決不可なら Coordinator が `jj resolve` で一元解消
3. 同一ホットスポットで繰り返す場合はファイル分割・責務分割を検討
