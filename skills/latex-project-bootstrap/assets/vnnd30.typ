// vnnd30.typ -- Vietnamese administrative-document formatting per Nghị định
// 30/2020/NĐ-CP. Ported from the original vnnd30.sty (XeLaTeX) to Typst
// (2026-07-27) for portability -- a single ~50MB static binary instead of a
// ~5GB TeX distribution, the same reason a sibling project (D:/elix/
// praxis_csc) made the identical switch for its own document export. Font/
// size/style values are UNCHANGED from the LaTeX version -- see
// references/nd30-2020-formatting.md for the grounding table both
// implementations enforce identically.
//
// This file is a formatting layer only -- it does not decide document
// content. scripts/render_nd30_document.py fills these functions from a
// caller-supplied, mechanically-validated content JSON; it never invents
// text.

#let nd-setup(margin-top: 20mm, margin-bottom: 20mm, margin-left: 30mm, margin-right: 15mm, body) = {
  set page(
    paper: "a4",
    margin: (top: margin-top, bottom: margin-bottom, left: margin-left, right: margin-right),
    header: context {
      // Số trang: Ả Rập, cỡ 13, đứng, canh giữa lề trên, KHÔNG hiện ở trang đầu.
      if counter(page).get().first() > 1 {
        align(center, text(size: 13pt)[#counter(page).display()])
      }
    },
  )
  set text(font: "Times New Roman", size: 13pt)
  set par(first-line-indent: 1cm, justify: true)
  body
}

// -- Ô 1: Quốc hiệu (in hoa 12-13 đứng đậm) + Tiêu ngữ (in thường 13-14 đứng đậm) --
#let nd-quochieu-tieungu() = align(center)[
  #text(size: 12pt, weight: "bold")[CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM] \
  #text(size: 13pt, weight: "bold")[Độc lập - Tự do - Hạnh phúc]
  #v(2pt)
  #line(length: 3.5cm)
]

// -- Ô 2: Tên cơ quan (chủ quản: in hoa 12-13 đứng / ban hành: in hoa 12-13 đứng đậm) --
#let nd-coquan(chu-quan, ban-hanh) = align(center)[
  #if chu-quan != "" [#text(size: 12pt)[#chu-quan] \ ]
  #text(size: 12pt, weight: "bold")[#ban-hanh]
  #v(2pt)
  #line(length: 2.5cm)
]

// -- Ô 3: Số, ký hiệu (in thường 13 đứng) --
#let nd-sokyhieu(so-ky-hieu) = align(center)[
  #text(size: 13pt)[Số: #so-ky-hieu]
]

// -- Ô 4: Địa danh, ngày tháng năm (in thường 13-14 nghiêng) --
#let nd-diadanhngay(dia-danh, ngay, thang, nam) = align(center)[
  #text(size: 13pt, style: "italic")[#dia-danh, ngày #ngay tháng #thang năm #nam]
]

// -- Ô 5a: Tên loại (in hoa 13-14 đứng đậm) + trích yếu (in thường 13-14 đứng đậm) --
#let nd-tenloai-trichyeu(ten-loai, trich-yeu) = align(center)[
  #text(size: 14pt, weight: "bold")[#ten-loai]
  #v(2pt)
  #text(size: 14pt, weight: "bold")[#trich-yeu]
  #v(2pt)
  #line(length: 4cm)
]

// -- Ô 5b: Trích yếu công văn, "V/v ..." (in thường 12-13 đứng) --
#let nd-trichyeu-congvan(trich-yeu) = align(center)[
  #text(size: 13pt)[V/v #trich-yeu]
]

// -- Kính gửi (công văn) -- string-concatenated, NOT markup "- " (which
//    Typst would otherwise parse as a bullet-list marker, rendering "•"
//    instead of the literal dash the real mẫu uses). --
#let nd-kinhgui(recipients) = {
  text(size: 13pt)[Kính gửi:]
  linebreak()
  for r in recipients {
    text(size: 13pt)[#("- " + r + ";")]
    linebreak()
  }
}

// -- Nội dung văn bản (in thường 13-14 đứng, justify) --
#let nd-noidung(paragraphs) = {
  for p in paragraphs [
    #text(size: 13pt)[#p]
    #parbreak()
  ]
}

// -- "THẨM QUYỀN BAN HÀNH" -- real heading in Mẫu 1.1/1.2/1.3 before "Căn cứ ...;" --
#let nd-thamquyenbanhanh() = align(center)[
  #text(size: 13pt, weight: "bold")[THẨM QUYỀN BAN HÀNH]
]

// -- Điều (quyết định-style), tiêu đề đậm cỡ lời văn --
#let nd-dieu(so, noi-dung) = {
  v(6pt)
  text(weight: "bold")[Điều #so.] + [ ] + noi-dung
  parbreak()
}

// -- Chữ ký: quyền hạn/chức vụ (in hoa 13-14 đậm) / họ tên (in thường 13-14 đậm) --
#let nd-nguoiky(quyen-han, chuc-vu, ho-ten) = align(center)[
  #if quyen-han != "" [#text(size: 14pt, weight: "bold")[#quyen-han #chuc-vu]] else [#text(size: 14pt, weight: "bold")[#chuc-vu]]
  #v(2.2cm)
  #text(size: 14pt, weight: "bold")[#ho-ten]
]

// -- Chữ ký thay mặt tập thể: quyền hạn+tên tập thể 1 dòng, chức vụ dòng riêng --
#let nd-nguoiky-tapthe(quyen-han, tap-the, chuc-vu, ho-ten) = align(center)[
  #text(size: 14pt, weight: "bold")[#quyen-han #tap-the] \
  #text(size: 14pt, weight: "bold")[#chuc-vu]
  #v(2.2cm)
  #text(size: 14pt, weight: "bold")[#ho-ten]
]

// -- Nơi nhận: "Nơi nhận:" nghiêng đậm 12, danh sách đứng 11 -- string-
//    concatenated, same reason as nd-kinhgui (avoid Typst's "- " bullet-list
//    markup parsing). --
#let nd-noinhan(recipients) = {
  text(size: 12pt, weight: "bold", style: "italic")[Nơi nhận:]
  linebreak()
  for r in recipients {
    text(size: 11pt)[#("- " + r + ";")]
    linebreak()
  }
}

// -- Biên bản (Mẫu 1.9): thời gian/địa điểm/thành phần/chủ trì/thư ký lines --
#let nd-bienban-info(bat-dau, dia-diem, thanh-phan, chu-tri, thu-ky) = {
  [Thời gian bắt đầu: #bat-dau] + linebreak()
  [Địa điểm: #dia-diem] + linebreak()
  [Thành phần tham dự: #thanh-phan] + linebreak()
  v(4pt)
  [Chủ trì (chủ toạ): #chu-tri] + linebreak()
  [Thư ký (người ghi biên bản): #thu-ky]
  parbreak()
}

// -- Biên bản: 2 cột chữ ký ngang hàng (THƯ KÝ trái / CHỦ TỌA phải) --
#let nd-bienban-chuky(thu-ky-ten, chu-toa-ten) = grid(
  columns: (1fr, 1fr),
  column-gutter: 1em,
  align(center)[
    #text(size: 14pt, weight: "bold")[THƯ KÝ]
    #v(2.2cm)
    #text(size: 14pt, weight: "bold")[#thu-ky-ten]
  ],
  align(center)[
    #text(size: 14pt, weight: "bold")[CHỦ TỌA]
    #v(2.2cm)
    #text(size: 14pt, weight: "bold")[#chu-toa-ten]
  ],
)

// -- Khối 2 cột đầu/cuối trang: trái = cơ quan/nơi nhận, phải = quốc hiệu/chữ ký --
#let nd-2col(left-content, right-content) = grid(
  columns: (1fr, 1fr),
  column-gutter: 1em,
  left-content, right-content,
)
