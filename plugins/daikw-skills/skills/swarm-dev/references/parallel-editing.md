# 並列編集プロトコル

## 基本原則

ファイル単位の予約より **責務境界での分割** を優先する。jj を使って並列編集を行う。

## jj の利用

```bash
# Coordinator がエージェントごとに workspace を作成
jj workspace add ../ws-<agent-name>
# 各エージェントは自分の change で作業
# bookmark: agent/<name>/<task-id>

# 統合: 各エージェント change を integration change に順次 rebase
jj rebase -s <agent-change> -d integration/<task-id>
# → テスト実行 → 通ったもののみ統合

# 統合 change がグリーンになったら main へ反映
# ロールバックは jj op undo で直前操作を戻す
```

## 競合が起きたら

1. エージェントが最新の integration change に rebase
2. 解決できなければ Coordinator が `jj resolve` で一元解消
3. 同じホットスポットで競合が繰り返す場合はファイル分割・責務分割を検討
