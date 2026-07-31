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

// -- Density presets (NĐ 30/2020 Phụ lục I Mục I.3's margin ranges + Mục V's
//    footnote requiring Quốc hiệu/Tiêu ngữ/địa danh to move together as ONE
//    of 2 permitted size sets, "Quốc hiệu 12 + Tiêu ngữ/địa danh 13" or
//    "Quốc hiệu 13 + Tiêu ngữ/địa danh 14", never mixed -- see
//    references/nd30-2020-formatting.md and findings.md line 56, both
//    transcribed directly from the real PDF). The 3 named presets
//    (tiet_kiem_giay/tieu_chuan/trang_trong) and their concrete margin/
//    body-size/indent bundling are ported from a real prior production
//    system's DENSITY_PRESETS table (see SKILL.md metadata.elicited_from,
//    v0.5.0 entry) -- every value here stays within the legal ranges above;
//    `leading` (line-spacing) is this port's own technical mapping of that
//    system's line_spacing multiplier (1.0/1.5, capped at NĐ 30's 1.5 max)
//    onto Typst's own par-leading mechanism -- NOT itself a claim that NĐ
//    30 mandates a specific em value, only that it caps the multiplier.
//    `nd-setup`'s own hardcoded defaults (used when `density` is omitted)
//    are UNCHANGED from pre-v0.5.0 -- this knob is additive/opt-in only.
#let nd-density-presets = (
  tiet_kiem_giay: (quochieu: 12pt, tieungu: 13pt, body: 13pt, indent: 1cm, leading: 0.65em),
  tieu_chuan: (quochieu: 12pt, tieungu: 13pt, body: 13pt, indent: 1cm, leading: 0.975em),
  trang_trong: (quochieu: 13pt, tieungu: 14pt, body: 14pt, indent: 1.27cm, leading: 0.975em),
)

// State broadcasting the active size profile to every Ô-function below, set
// once by nd-setup() -- avoids threading an extra parameter through every
// existing function's call sites (backward-compatible with all 5 pre-
// v0.5.0 doc_kieu render paths).
#let nd-profile = state("nd-profile", (quochieu: 12pt, tieungu: 13pt, body: 13pt, indent: 1cm, leading: none))

#let nd-setup(margin-top: 20mm, margin-bottom: 20mm, margin-left: 30mm, margin-right: 15mm, density: none, body) = {
  let profile = if density != none { nd-density-presets.at(density) } else {
    (quochieu: 12pt, tieungu: 13pt, body: 13pt, indent: 1cm, leading: none)
  }
  nd-profile.update(profile)

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
  set text(font: "Times New Roman", size: profile.body)
  set par(first-line-indent: profile.indent, justify: true)
  if profile.leading != none {
    set par(leading: profile.leading)
  }
  body
}

// -- Ô 1: Quốc hiệu (in hoa 12-13 đứng đậm) + Tiêu ngữ (in thường 13-14 đứng đậm) --
#let nd-quochieu-tieungu() = context {
  let p = nd-profile.get()
  align(center)[
    #text(size: p.quochieu, weight: "bold")[CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM] \
    #text(size: p.tieungu, weight: "bold")[Độc lập - Tự do - Hạnh phúc]
    #v(2pt)
    #line(length: 3.5cm)
  ]
}

// -- Ô 2: Tên cơ quan (chủ quản: in hoa 12-13 đứng / ban hành: in hoa 12-13 đứng đậm) --
#let nd-coquan(chu-quan, ban-hanh) = context {
  let p = nd-profile.get()
  align(center)[
    #if chu-quan != "" [#text(size: p.quochieu)[#chu-quan] \ ]
    #text(size: p.quochieu, weight: "bold")[#ban-hanh]
    #v(2pt)
    #line(length: 2.5cm)
  ]
}

// -- Ô 3: Số, ký hiệu (in thường 13 đứng -- table gives a SINGLE fixed value
//    here, not a 12-13/13-14 range like the other ô, so this stays fixed
//    regardless of density preset) --
#let nd-sokyhieu(so-ky-hieu) = align(center)[
  #text(size: 13pt)[Số: #so-ky-hieu]
]

// -- Ô 4: Địa danh, ngày tháng năm (in thường 13-14 nghiêng -- paired with
//    Tiêu ngữ's size per the same consistency footnote) --
#let nd-diadanhngay(dia-danh, ngay, thang, nam) = context {
  let p = nd-profile.get()
  align(center)[
    #text(size: p.tieungu, style: "italic")[#dia-danh, ngày #ngay tháng #thang năm #nam]
  ]
}

// -- Ô 5a: Tên loại (in hoa 13-14 đứng đậm) + trích yếu (in thường 13-14 đứng đậm) --
#let nd-tenloai-trichyeu(ten-loai, trich-yeu) = context {
  let p = nd-profile.get()
  align(center)[
    #text(size: p.body + 1pt, weight: "bold")[#ten-loai]
    #v(2pt)
    #text(size: p.body + 1pt, weight: "bold")[#trich-yeu]
    #v(2pt)
    #line(length: 4cm)
  ]
}

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
#let nd-noidung(paragraphs) = context {
  let p = nd-profile.get()
  for para in paragraphs [
    #text(size: p.body)[#para]
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

// -- Công điện (Mẫu 1.6, Phụ lục III Mục II trang 10 của PDF gốc): "<tên cơ
//    quan/chức danh người đứng đầu> điện:" + danh sách nơi nhận điện --
//    string-concatenated, same reason as nd-kinhgui/nd-noinhan (avoid
//    Typst's "- " bullet-list markup parsing). --
#let nd-dien(nguoi-dung-dau, nguoi-nhan-dien) = {
  text(size: 13pt)[#nguoi-dung-dau điện:]
  linebreak()
  for r in nguoi-nhan-dien {
    text(size: 13pt)[#("- " + r + ";")]
    linebreak()
  }
}

// -- Giấy mời (Mẫu 1.7, Phụ lục III Mục II trang 11 của PDF gốc): "<cơ quan
//    ban hành> trân trọng kính mời: <người được mời>", "Tới dự <nội dung
//    cuộc họp>", "Chủ trì:", "Thời gian:", "Địa điểm:", rồi tùy chọn "các
//    vấn đề cần lưu ý" (ghi chú 8 của mẫu thật) --
#let nd-giaymoi-noidung(co-quan-ban-hanh, nguoi-duoc-moi, noi-dung-cuoc-hop, chu-tri, thoi-gian, dia-diem, luu-y: none) = {
  text(size: 13pt)[#co-quan-ban-hanh trân trọng kính mời: #nguoi-duoc-moi]
  parbreak()
  text(size: 13pt)[Tới dự #noi-dung-cuoc-hop]
  parbreak()
  text(size: 13pt)[Chủ trì: #chu-tri]
  linebreak()
  text(size: 13pt)[Thời gian: #thoi-gian]
  linebreak()
  text(size: 13pt)[Địa điểm: #dia-diem]
  if luu-y != none {
    parbreak()
    text(size: 13pt)[#luu-y]
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
