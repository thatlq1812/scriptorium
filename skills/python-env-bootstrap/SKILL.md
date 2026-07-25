---
name: python-env-bootstrap
description: Tạo venv Python reproducible cho một skill khác cần chạy code Python, kể cả trên máy CHƯA cài Python — dùng uv (Astral), một binary tĩnh tự tải Python chuẩn. Dùng khi một skill khác khai báo `requirements.txt` và cần một môi trường chạy sạch, cùng version. KHÔNG dùng để cài Python vào hệ thống vĩnh viễn hay thay thế trình quản lý gói của người dùng — chỉ tạo venv cục bộ trong thư mục skill đó.
license: MIT
compatibility: Cần tải/cài `uv` (script cài chính thức astral.sh, không cần Python có sẵn). Verify chạy sạch: Claude Code, Windows qua PowerShell thật (2026-07-26, dùng để bootstrap lại `document-ai-structurer`; chạy qua Git Bash/MSYS2 trên cùng máy Windows thất bại — xem cảnh báo trong thân bài). Chưa verify: macOS/Linux thật, OpenAI Codex CLI, Kimi Code CLI, Antigravity CLI.
metadata:
  domain: meta
  task_type: coordination
  risk_tier: N1
  source: self-authored
  elicited_from: "Owner (docs/archive/pre-spec-2026-07-26/note.md mục 3): ý tưởng một skill 'chứa đầy đủ một phiên bản python bên trong nó' để người dùng phổ thông chạy được skill cần Python phức tạp mà không cần tự cài đặt gì trước"
  version: 0.1.0
---

# python-env-bootstrap

Skill hạ tầng dùng chung: bootstrap một venv Python cho MỘT skill khác (không phải cho chính nó), dựa trên `uv` — binary tĩnh ~15MB, tự tải Python portable, không yêu cầu máy đã có Python cài sẵn (khác `python -m venv`, vốn cần Python đã tồn tại).

## Vì sao không dùng `venv` chuẩn của Python

`python -m venv` yêu cầu Python đã cài sẵn trên máy — không đúng giả định "người dùng phổ thông" mà owner đặt ra. `uv` giải quyết đúng khoảng trống này: cài `uv` (không cần Python) → `uv python install` tự tải Python chuẩn → `uv venv` + `uv pip install` như bình thường.

## Nguyên tắc — không commit venv (nhắc lại từ `docs/specs/STRATEGY_SPEC.md` §7.7)

Skill này KHÔNG tạo ra và KHÔNG commit bất kỳ venv nào vào git. Nó chỉ là logic bootstrap chạy tại thời điểm cần — venv luôn được tạo mới trên máy đang chạy, nằm trong `.gitignore` của skill đích.

## Dùng cho một skill khác

Skill đích phải có `requirements.txt` ở gốc thư mục của nó (vd `skills/document-ai-structurer/requirements.txt`). Chạy:

```bash
# Unix/macOS thật (KHÔNG dùng qua Git Bash/MSYS2 trên Windows — xem cảnh báo dưới):
bash skills/python-env-bootstrap/scripts/bootstrap.sh skills/<skill_dich> [python_version]

# Windows: LUÔN chạy qua PowerShell thật, không qua Git Bash:
.\skills\python-env-bootstrap\scripts\bootstrap.ps1 -SkillDir skills\<skill_dich> [-PyVersion 3.12]
```

Kết quả: `<skill_dich>/.venv` sẵn sàng, đúng version Python + dependency đã pin trong `requirements.txt`.

## Cảnh báo đã xác nhận bằng lỗi thật: không chạy `bootstrap.sh` từ Git Bash/MSYS2 trên Windows

Chạy `bootstrap.sh` bên trong Git Bash (MINGW64/MSYS2) trên Windows khiến `uv` **detect nhầm platform thành `linux-x86_64-gnu`** (do `uname` của MSYS2 trả về giá trị giống Linux) và tải một Python build Linux không dùng được — venv tạo ra có symlink trỏ tới đường dẫn không tồn tại (`/home/<user>/.local/share/uv/python/...`), lỗi "No such file" khi gọi. Trên Windows, phải chạy `bootstrap.ps1` qua PowerShell thật (không phải Git Bash gọi powershell.exe lồng nhau) để `uv` detect đúng `x86_64-pc-windows-msvc`. Đã tái hiện và fix thật ngày 2026-07-26 khi bootstrap `document-ai-structurer`.

## Giới hạn đã biết (v0.1.0)

- Verify chạy đúng trên Windows qua PowerShell thật. Script `.sh` viết theo chuẩn POSIX nhưng chưa test thật trên macOS/Linux thật (chỉ mới phát hiện nó SAI khi chạy nhầm qua Git Bash trên Windows — xem cảnh báo trên).
- Cài `uv` lần đầu cần mạng (tải installer từ astral.sh) — không hoạt động hoàn toàn offline lần chạy đầu.
- Chưa qua stage 4 (quality eval ≥2 harness) và stage 5 (security audit).

## Skill đang phụ thuộc vào skill này

- `document-ai-structurer` (xem `registry/skills.json`, field `dependencies`).
