# 出力テンプレート

## Phase 1 完了報告

```
## 発見した問題（技術 + プロダクト視点）
### CRITICAL（N 件）
1. **問題名** - 詳細 / 影響 / ファイル
### HIGH（N 件）/ MEDIUM（N 件）
...
## 実行コントラクト
start_cmd: ...  test_cmd: ...  build_cmd: ...
## チーム構成
- 再帰的プランナー: 起動済み（/loop 5m）
- Advisory Browser Tester: 起動済み / 起動対象外
→ チームを編成して作業を開始します
```

## PR body

```
## Summary
<変更内容の要約>
Closes #<N>

## Changes
### CRITICAL（N 件）
### HIGH（N 件）

## Test Results
### Automated Tests
- Unit: X pass / Y fail
- Integration: X pass / Y fail
- Coverage: XX%

### Browser Test Summary
- Gate: PASS | FAIL | BLOCKED | NOT_REQUIRED
- Tested commit: `<sha>`
- Trigger: `frontend_changed=yes|no`, `browser_validation_requested=required|auto|skip`
- Scope / Depth / Scenarios: N run, N pass, N fail
- Evidence: see test comment below

### Known Issues
- <未解決の MEDIUM 等>

## Test Plan
- [ ] ...
```

## PR comment（Phase 4 詳細ログ）

```
## Phase 4 Browser Test Run #N
- Commit: `<sha>`
- Outcome: PASS | FAIL
- Scenario 1: <フロー名> - Status / Observation
- Console errors: none | <details>
- Screenshots: attached | <local path>
- Next action: Phase 5 proceed | return to Phase 3
```

## エスカレーション報告

```
## Escalation
- Gate status: FAIL
- Failed after: N browser test runs
- Blocking issue: <概要>
- Repro / Suspected cause / Ownership
- Recommendation: human review required before merge
```
