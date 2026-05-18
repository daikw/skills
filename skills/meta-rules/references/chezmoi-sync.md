# dotfile manager 同期 (chezmoi を例に)

`~/.claude/` 配下を chezmoi 等の dotfile manager で管理している場合、
スキル / ルール / agent を編集したら source 側も同期させる必要がある。
片側だけ編集して放置すると、次回の `apply` で巻き戻る。

このドキュメントは chezmoi を例にしているが、他の dotfile manager でも同じ手順で同期できる。

## チェックリスト

- [ ] 編集対象が dotfile manager の管理下か確認 (`chezmoi managed <path>` 等)
- [ ] 編集後、source/destination の乖離を確認 (`chezmoi status` 等)
- [ ] 通常ファイルは source 側に逆流 (`chezmoi re-add <path>` 等)
- [ ] templated (`.tmpl`) ファイルは source 側を直接編集
- [ ] 解消後、source の git repo で commit（push は別途承認）

## templated ファイルの注意 (chezmoi 固有)

`.tmpl` 拡張子は host-specific gating (`{{ if eq .chezmoi.hostname ... }}`) や
変数展開を含む。`chezmoi re-add` は templating を壊すので、必ず source の `.tmpl`
を直接編集する。`chezmoi execute-template < <(...)` で動作確認できる。

他の dotfile manager（stow, yadm, dotbot 等）を使っている場合は、それぞれの
template / hook 機構に応じて読み替えること。
