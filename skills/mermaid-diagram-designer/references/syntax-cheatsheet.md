# Mermaid — cheatsheet cú pháp theo loại diagram

Mọi diagram Mermaid là text thuần, đặt trong code fence ```` ```mermaid ```` (markdown) hoặc `<pre class="mermaid">` (HTML). Dòng đầu tiên luôn là từ khóa khai báo loại diagram.

## Flowchart — quy trình, luồng quyết định

```
flowchart TD
    A[Bắt đầu] --> B{Điều kiện?}
    B -->|Đúng| C[Xử lý A]
    B -->|Sai| D[Xử lý B]
    C --> E[Kết thúc]
    D --> E
```

Hướng: `TD`/`TB` (trên-xuống), `LR` (trái-phải), `BT`, `RL`. Hình dạng node: `[chữ nhật]`, `(bo tròn)`, `{hình thoi = quyết định}`, `((hình tròn))`, `[[subroutine]]`.

## Sequence diagram — tương tác qua thời gian giữa nhiều actor

```
sequenceDiagram
    participant User
    participant API
    User->>API: Gửi request
    API-->>User: Trả response
    Note over API: Xử lý async
```

`->>` = gọi đồng bộ (mũi tên đặc), `-->>` = trả lời (mũi tên đứt), `activate`/`deactivate` để vẽ lifeline.

## Class diagram — quan hệ giữa các class/entity

```
classDiagram
    class Skill {
        +String name
        +String description
        +run()
    }
    Skill <|-- DomainSkill
    Skill *-- Metadata
```

`<|--` kế thừa, `*--` composition, `o--` aggregation, `-->` association.

## State diagram — máy trạng thái

```
stateDiagram-v2
    [*] --> Draft
    Draft --> UnderReview: submit
    UnderReview --> Published: approve
    UnderReview --> Draft: reject
    Published --> [*]
```

## ER diagram — mô hình dữ liệu

```
erDiagram
    SKILL ||--o{ REGISTRY_ENTRY : has
    SKILL {
        string skill_id PK
        string version
    }
```

`||--o{` = one-to-many, `||--||` = one-to-one, `}o--o{` = many-to-many.

## Gantt — timeline dự án

```
gantt
    dateFormat YYYY-MM-DD
    section Phase 1
    Research :a1, 2026-07-01, 7d
    Design   :after a1, 5d
```

## Pie — tỷ lệ đơn giản (KHÔNG phải công cụ chính cho biểu đồ dữ liệu phức tạp)

```
pie title Phân bổ skill theo domain
    "meta" : 8
    "general" : 3
```

Với dữ liệu định lượng phức tạp hơn (nhiều series, trục, tương tác), dùng công cụ chart chuyên dụng (matplotlib/Recharts/D3), không ép Mermaid làm việc nó không mạnh.

## Journey / Mindmap / Timeline — trình bày trải nghiệm/ý tưởng phân nhánh

```
journey
    title Hành trình người dùng
    section Khám phá
      Tìm skill: 5: User
      Đọc SKILL.md: 4: User
```

```
mindmap
  root((Scriptorium))
    Pipeline
      skill-creator
      quality-eval
    Registry
```

## Lỗi cú pháp thường gặp (script `scripts/lint_mermaid.py` bắt được phần này)

- Thiếu từ khóa loại diagram ở dòng đầu.
- Ngoặc `[`, `(`, `{` không cân đối.
- Nhãn cạnh (`|text|`) không đóng.
- Trộn cú pháp `stateDiagram` cũ và `stateDiagram-v2` (dùng `-v2` cho mọi diagram mới, cú pháp phong phú hơn).
