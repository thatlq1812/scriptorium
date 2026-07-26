---
name: python-env-bootstrap
description: Tạo/mở rộng MỘT venv Python dùng chung ở root repo (sibling `skills/`), kể cả trên máy CHƯA cài Python — dùng uv (Astral), một binary tĩnh tự tải Python chuẩn. Dùng khi một skill khác khai báo `requirements.txt` và cần được cài vào môi trường chạy chung. KHÔNG dùng để cài Python vào hệ thống vĩnh viễn hay thay thế trình quản lý gói của người dùng — chỉ quản lý venv dùng chung của repo.
license: MIT
compatibility: Cần tải/cài `uv` (script cài chính thức astral.sh, không cần Python có sẵn). Verify chạy sạch: Claude Code, Windows qua PowerShell thật (2026-07-26) — venv chung tại root cài thành công dependency của 3 skill (document-ai-structurer, office-doc-creator, image-generator-gemini), import chéo không xung đột. Chạy qua Git Bash/MSYS2 trên cùng máy Windows thất bại — xem cảnh báo trong thân bài. Chưa verify: macOS/Linux thật, OpenAI Codex CLI, Kimi Code CLI, Antigravity CLI.
metadata:
  domain: meta
  task_type: coordination
  risk_tier: N1
  source: self-authored
  elicited_from: "Owner (docs/archive/pre-spec-2026-07-26/note.md mục 3): ý tưởng một skill 'chứa đầy đủ một phiên bản python bên trong nó' để người dùng phổ thông chạy được skill cần Python phức tạp mà không cần tự cài đặt gì trước. Cập nhật 2026-07-26: owner yêu cầu chuyển từ venv-per-skill sang venv chung ở root — tránh trùng lặp dependency nặng (torch...) qua từng skill."
  version: 0.2.0
---

# python-env-bootstrap

Skill hạ tầng dùng chung: bootstrap/mở rộng MỘT venv Python dùng chung ở root repo (`<repo_root>/.venv`, sibling `skills/`) cho các skill khác cần Python, dựa trên `uv` — binary tĩnh ~15MB, tự tải Python portable, không yêu cầu máy đã có Python cài sẵn.

## Vì sao venv chung, không phải mỗi skill một venv

**Đổi hướng 2026-07-26 (owner)**: trước đây mỗi skill có `.venv` riêng bên trong thư mục skill — dẫn tới trùng lặp dependency nặng (vd `torch` ~2GB, đã bị cài lại nhiều lần cho nhiều skill khác nhau dùng chung stack ML). Venv chung ở root giải quyết việc đó: cài 1 lần, mọi skill Python dùng chung. Verify thật: `document-ai-structurer` + `office-doc-creator` + `image-generator-gemini` cùng cài vào 1 venv, import chéo không xung đột (`docling`, `python-docx/pptx`, `openpyxl`, `google-genai` cùng tồn tại sạch).

## Vì sao không dùng `venv` chuẩn của Python

`python -m venv` yêu cầu Python đã cài sẵn trên máy — không đúng giả định "người dùng phổ thông" mà owner đặt ra. `uv` giải quyết đúng khoảng trống này: cài `uv` (không cần Python) → `uv python install` tự tải Python chuẩn → `uv venv` + `uv pip install` như bình thường.

## Nguyên tắc — không commit venv (nhắc lại từ `docs/specs/STRATEGY_SPEC.md` §7.7)

Skill này KHÔNG tạo ra và KHÔNG commit bất kỳ venv nào vào git. Nó chỉ là logic bootstrap chạy tại thời điểm cần — venv luôn được tạo mới trên máy đang chạy, nằm trong `.gitignore` ở root repo.

## Dùng cho một skill khác

Skill đích phải có `requirements.txt` ở gốc thư mục của nó. Chạy (từ root repo):

```bash
# Unix/macOS thật (KHÔNG dùng qua Git Bash/MSYS2 trên Windows — xem cảnh báo dưới):
bash skills/python-env-bootstrap/scripts/bootstrap.sh skills/<skill_dich>/requirements.txt [python_version]

# Windows: LUÔN chạy qua PowerShell thật, không qua Git Bash:
.\skills\python-env-bootstrap\scripts\bootstrap.ps1 -Requirements skills\<skill_dich>\requirements.txt [-PyVersion 3.12]
```

Kết quả: `<repo_root>/.venv` sẵn sàng (tạo mới nếu chưa có, mở rộng nếu đã có), đúng version Python + dependency của skill vừa gọi được thêm vào — venv này dùng chung cho MỌI skill Python trong repo, không tạo venv mới cho mỗi lần gọi.

## Cảnh báo đã xác nhận bằng lỗi thật: không chạy `bootstrap.sh` từ Git Bash/MSYS2 trên Windows

Chạy `bootstrap.sh` bên trong Git Bash (MINGW64/MSYS2) trên Windows khiến `uv` **detect nhầm platform thành `linux-x86_64-gnu`** (do `uname` của MSYS2 trả về giá trị giống Linux) và tải một Python build Linux không dùng được — venv tạo ra có symlink trỏ tới đường dẫn không tồn tại (`/home/<user>/.local/share/uv/python/...`), lỗi "No such file" khi gọi. Trên Windows, phải chạy `bootstrap.ps1` qua PowerShell thật (không phải Git Bash gọi powershell.exe lồng nhau) để `uv` detect đúng `x86_64-pc-windows-msvc`. Đã tái hiện và fix thật ngày 2026-07-26 khi bootstrap `document-ai-structurer`.

## Giới hạn đã biết (v0.2.0)

- Venv chung nghĩa là MỌI skill Python dùng cùng version dependency — nếu 2 skill cần version khác nhau của cùng 1 package, xung đột thật (chưa gặp trường hợp này, nhưng cần theo dõi khi thêm skill Python mới).
- Verify chạy đúng trên Windows qua PowerShell thật. Script `.sh` viết theo chuẩn POSIX nhưng chưa test thật trên macOS/Linux thật.
- Cài `uv` lần đầu cần mạng (tải installer từ astral.sh) — không hoạt động hoàn toàn offline lần chạy đầu.
- Chưa qua stage 4 (quality eval ≥2 harness) và stage 5 (security audit).

## Skill đang phụ thuộc vào skill này

- `document-ai-structurer`, `office-doc-creator`, `image-generator-gemini` (xem `registry/skills.json`, field `dependencies`).
