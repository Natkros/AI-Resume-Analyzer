# ATS Best Practices

## Formatting
Applicant tracking systems parse resumes as text. Multi-column layouts, text
boxes, tables used for layout (not data), headers/footers, and graphics can
scramble or drop content during parsing. A single-column layout with standard
section headings is the safest choice.

## Section headings
Use conventional headings: "Experience" or "Work Experience" rather than
creative alternatives like "My Journey". ATS keyword matching and many human
recruiters scan for standard section names first.

## Keywords
Mirror the exact terminology used in the job description where truthful
(e.g. if the JD says "PostgreSQL", don't only write "Postgres" — include both
if genuinely used). Do not keyword-stuff; unnatural repetition is flagged by
both ATS relevance scoring and human reviewers.

## Contact information
Always include a plain-text email and phone number outside of any header/
footer element, since many parsers ignore header/footer content entirely.

## File format
Save as .docx or a text-based PDF (not a scanned image) unless the
application explicitly requests another format. Scanned/image PDFs require
OCR and are the single most common cause of a resume being parsed as blank.

## Bullet quality
Start bullets with a strong action verb, describe the action and its
context, and include a quantified outcome when one genuinely exists
("reduced latency by 35%" beats "worked on performance").
