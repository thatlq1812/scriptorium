# LaTeX + tiếng Việt — thiết lập đúng ngay từ đầu

Bài học rút từ một dự án LaTeX thật (chương trình sách giáo khoa `D:/elix/researches/textbooks`, dùng thật trong sản xuất, không phải lý thuyết): **luôn dùng XeLaTeX, không dùng pdfLaTeX + gói `vietnamese` babel** cho tài liệu tiếng Việt nghiêm túc.

## Vì sao XeLaTeX

- **pdfLaTeX + `babel[vietnamese]`**: dùng font 8-bit encoding cũ, dễ lỗi dấu thanh/dấu mũ khi kết hợp với font chữ hiện đại, giới hạn lựa chọn font hỗ trợ đầy đủ bộ Unicode tiếng Việt.
- **XeLaTeX + `fontspec` + `polyglossia`**: xử lý Unicode trực tiếp (UTF-8 native), dùng được bất kỳ font TrueType/OpenType nào cài trên hệ thống (Times New Roman, Noto Sans, Google Fonts...) miễn font đó có glyph tiếng Việt — không cần font LaTeX chuyên biệt.

## Preamble tối thiểu đúng chuẩn

```latex
\documentclass[11pt]{book}
\usepackage{fontspec}
\usepackage{polyglossia}
\setmainlanguage{vietnamese}
\setmainfont{Noto Serif}       % hoặc bất kỳ font Unicode có sẵn trên máy
\setsansfont{Noto Sans}
```

Biên dịch bằng `xelatex`, KHÔNG dùng `pdflatex` — hai engine không tương thích với `fontspec`.

## Bibliography — dùng biber, không dùng bibtex

`biblatex` + `biber` xử lý Unicode tốt hơn `bibtex` cổ điển (vốn cũng giới hạn 8-bit như pdfLaTeX). Thứ tự build chuẩn cho tài liệu có bibliography:

```
xelatex main.tex   # pass 1: sinh .aux, .bcf
biber main          # đọc .bcf, sinh .bbl từ bibliography.bib
xelatex main.tex   # pass 2: nhúng citation
xelatex main.tex   # pass 3: chốt cross-reference (mục lục, số trang, \ref)
```

4 lệnh, không phải 1 — bỏ qua bất kỳ pass nào cũng có thể ra file thiếu citation hoặc mục lục sai trang.

## Lỗi thường gặp

- Quên đổi `pdflatex` sang `xelatex` khi copy template cũ → lỗi `fontspec requires xetex or luatex`.
- Font chọn trong `\setmainfont` không có trên máy build → lỗi "Font not found", cần cài font hoặc đổi tên font khác đã cài (`fc-list` trên Linux/Mac, hoặc kiểm Fonts trong Windows Settings).
- Dùng `\usepackage[utf8]{inputenc}` (không cần với XeLaTeX, engine đã UTF-8 native — thêm vào không lỗi nhưng thừa, dấu hiệu copy nhầm template pdfLaTeX).
