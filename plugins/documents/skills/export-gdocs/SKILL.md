---
name: export-gdocs
description: "마크다운 기술 문서를 Google Docs로 변환·생성한다. 서식이 지정된 HTML을 Google Drive 파일 생성 도구(text/html)로 업로드하면 Drive가 Google Docs로 자동 변환하는 방식이다. 'google docs로 만들어줘', 'gdocs 생성', '구글 문서로 변환' 요청 시 이 스킬을 사용할 것. 기존 생성본의 서식 수정·재생성 요청에도 사용."
---

# Google Docs 생성 스킬 (export-gdocs)

마크다운 기술 문서를 Google Docs 문서로 변환한다. 2026-09-03에 실제 서비스 문서로 여러 차례 시험하여 확정한 규칙이며, Drive의 HTML → Docs 변환기가 지원하는 속성만 사용한다.

## 이식 전제 조건 (다른 에이전트에서 사용할 때)

- **Google Drive에 파일을 생성하는 도구가 필요하다.** HTML 본문(텍스트)과 MIME 타입(text/html)을 함께 전달할 수 있어야 한다. Claude Code의 Google Drive MCP에서는 create_file(textContent + contentMimeType)이고, Drive API 직접 호출이라면 files.create 업로드에서 변환 대상 MIME을 application/vnd.google-apps.document로 지정하는 것에 해당한다.
- 생성 결과를 텍스트로 읽어 오는 도구(read_file_content 상당)가 있으면 검증 단계까지 수행할 수 있다. 없으면 사용자에게 육안 확인을 요청한다.
- 같은 폴더의 example.html이 규칙 전체가 적용된 검증 완료 예시다. 새 문서를 만들 때는 이 예시의 마크업 패턴을 그대로 따른다.

**유일하게 동작하는 전달 경로는 HTML 업로드다.** HTML 전문을 text/html로 업로드하면 Google Docs로 자동 변환된다. DOCX base64는 도구 파라미터가 잘려 전달이 불가능했고, markdown 업로드는 서식 제어가 전혀 안 된다.

## Step 1: 원본 전처리

마크다운 원본의 내용을 HTML로 옮기면서 다음을 변환한다. 내용(문장, 표 데이터)은 바꾸지 않는다.

| 원본 요소 | 변환 방법 |
|---|---|
| 상대 링크(../, ./) | 저장소(또는 원본 위치)의 절대 URL로 교체 |
| 이미지 임베드 | 인라인 임베드 불가. "다이어그램: [파일명(링크)](...) · 원본 [원본 파일](...)" 형태의 회색 링크 문단으로 교체 |
| 문서 내부 앵커(#섹션) | Docs에서 동작하지 않음. `"○○" 절 참고` 형태의 일반 텍스트로 교체 |
| 이스케이프(\\*, \\<) | HTML에서는 원래 문자로 되돌린다(\< → &lt;) |
| 코드 블록(```) | 1행 1열 표로 교체(Step 2의 코드 블록 규칙) |

원본이 2단계 이상 중첩 불릿을 쓰면 변환 품질이 떨어진다. 가능하면 원본 단계에서 불릿을 1단계로 정리한 뒤 변환한다.

## Step 2: 서식 규칙 (확정값)

**문서 골격**

```html
<html><head><meta charset="utf-8"><style>@page{margin:2.54cm 1.27cm}td{vertical-align:middle;padding:3.6pt;line-height:1}th{vertical-align:middle;line-height:1}td p{margin:0;line-height:1}th p{margin:0;line-height:1}</style></head><body>
...
</body></html>
```

**제목** — 인라인으로 지정한다. 글꼴은 지정하지 않는다(사용자가 Docs에서 "내 기본 스타일 사용"을 적용할 수 있게).

| 요소 | 크기 | 아래 여백 | 마크업 |
|---|---|---|---|
| H1 | 18pt bold | 10.8pt | `<h1 style="font-size:18pt;font-weight:bold;line-height:1.4;margin-bottom:10.8pt">` |
| H2 | 14pt bold | 7.2pt | `<h2 style="font-size:14pt;font-weight:bold;line-height:1.4;margin-bottom:7.2pt">` |
| H3 | 12pt bold | 3.6pt | `<h3 style="font-size:12pt;font-weight:bold;line-height:1.4;margin-bottom:3.6pt">` |

**본문 문단** — `<p style="line-height:1.4;margin-bottom:15pt">`. 회색 메타 문단(상위 문서 링크, 다이어그램 링크)은 `color:#666666`을 추가하고, 경고 인용 문단은 `margin-left:18pt`를 추가한다.

**불릿 목록** — 변환기가 li의 간격 속성을 전부 무시하므로, 불릿 하나를 항목 1개짜리 목록으로 만들고 사이에 작은 빈 문단을 끼운다. 이것이 유일하게 동작하는 방법이다.

```html
<ul style="margin:0"><li style="line-height:1.4">항목 내용</li></ul>
<p style="font-size:4pt;line-height:1">&nbsp;</p>
```

**번호 목록** — 실제 ol을 사용하지 않는다(분리하면 start 속성이 무시되어 번호가 전부 1로 표시된다). 번호를 텍스트로 포함한 문단으로 쓴다.

```html
<p style="line-height:1.4;margin-bottom:7.2pt">1. <b>제목:</b> 내용</p>
<p style="line-height:1.4;margin-bottom:15pt">2. <b>제목:</b> 내용(마지막 항목은 15pt)</p>
```

**표** — 열 너비는 내용 길이에 비례하여 %로 배분한다. 표 바로 뒤에는 빈 문단을 넣어 간격을 만든다(표 자체의 아래 여백은 지정해도 무시된다).

```html
<table style="width:100%;border-collapse:collapse">
<tr><th valign="middle" style="width:NN%;background-color:#f3f3f3;font-weight:bold;padding:3.6pt;line-height:1">헤더</th>...</tr>
<tr><td valign="middle" style="line-height:1">내용</td>...</tr>
</table>
<p style="line-height:1.4">&nbsp;</p>
```

**코드 블록** — Docs의 네이티브 코드 블록은 변환으로 만들 수 없다. 1행 1열 표로 대체하고, 줄바꿈은 `<br>`, 정렬용 공백은 `&nbsp;`로 넣는다. 뒤에 빈 문단을 붙인다.

```html
<table style="width:100%;border-collapse:collapse"><tr><td style="background-color:#f8f9fa;padding:7.2pt;font-family:'Courier New',monospace;font-size:10pt;line-height:1.4">명령1<br>명령2<br><br>명령3</td></tr></table>
<p style="line-height:1.4">&nbsp;</p>
```

## 변환기 지원/미지원 속성 (2026-09-03 실측 확정)

| 구분 | 속성 |
|---|---|
| 지원 | p의 margin-bottom·margin-left, font-size, font-weight, line-height, color, th의 width(%)·background-color, 링크, &lt;br&gt;(셀 안 줄바꿈), &amp;nbsp; |
| 무시 | li의 margin·padding(전부), li 안에 중첩한 p의 margin, ol의 start 속성, text-indent(내어쓰기), 표의 margin-bottom, @page 여백(불확실) |
| 불확실 | 셀의 vertical-align·padding·내부 문단 여백(스타일 블록 방식 병행, 완전 보장 없음) |
| 불가 | 이미지 인라인 임베드, 문서 내부 앵커 링크, Docs 네이티브 코드 블록 |

## Step 3: 생성과 검증

1. 같은 문서를 재생성할 때는 기존 Google Docs를 먼저 휴지통으로 보낸다(제목이 같은 문서가 중복 생성되는 것을 막기 위함이다). 권한 오류가 나면 사용자에게 직접 삭제를 요청한다.
2. 파일 생성 도구 호출: 문서 제목, MIME 타입 text/html, 본문에 HTML 전문.
3. 생성 직후 내용을 읽어 반드시 검증한다. 확인 항목: 마지막 섹션까지 내용이 온전한가, 불릿이 목록 구조(`- `)로 유지되는가, 번호 문단의 번호가 순서대로인가, 표 행 수가 원본과 같은가.
4. 사용자에게 문서 URL을 전달하면서 다음을 안내한다: 글꼴 통일이 필요하면 서식 > 단락 스타일 > 옵션 > "내 기본 스타일 사용"을 한 번 적용한다. 좌우 여백이 1인치로 보이면 파일 > 페이지 설정에서 좌우 1.27cm로 바꾼다.

## 주의사항

- **HTML 파일을 로컬에 먼저 만들 필요가 없다.** 도구의 본문 파라미터에 직접 작성한다. 다만 사용자가 HTML 원본을 요청하면 같은 내용을 파일로 저장해 전달한다.
- 원본 문서가 바뀌면 Google Docs를 새로 생성한다(부분 수정 API는 없다).
- 이 스킬은 변환만 담당한다. 원본 문서의 품질 규칙(불릿 단계 제한, 이모지·인라인 백틱 정리 등)은 원본 작성 단계에서 보장하는 것이 좋다.
