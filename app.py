
        # Apply PDF page selection / rotation / crop
        if ext == ".pdf":
            try:
                page_start = max(
                    1, int(request.form.get("page_start", "1") or 1)
                )
                page_end_text = request.form.get("page_end", "").strip()

                with fitz.open(source_path) as pdf_doc:
                    total_pages = len(pdf_doc)

                if total_pages == 0:
                    raise ValueError("PDF खाली है।")

                page_end = (
                    int(page_end_text) if page_end_text else total_pages
                )

                if (
                    page_start > total_pages
                    or page_end < page_start
                    or page_end > total_pages
                ):
                    raise ValueError("PDF Page Range सही नहीं है।")

                pages_text = f"{page_start}-{page_end}"

                rotate = int(
                    request.form.get("pdf_rotate", "0") or 0
                ) % 360

                if rotate not in {0, 90, 180, 270}:
                    rotate = 0

                crop_mm = max(
                    0,
                    min(20, float(request.form.get("pdf_crop_mm", "0") or 0))
                )

                if pages_text or rotate or crop_mm:
                    edited_path = UPLOAD_DIR / (order_id + "-edited.pdf")

                    process_pdf(
                        source_path,
                        edited_path,
                        pages_text,
                        rotate,
                        crop_mm
                    )

                    source_path.unlink(missing_ok=True)
                    source_path = edited_path
                    stored = edited_path.name

            except Exception as exc:
                source_path.unlink(missing_ok=True)
                flash("PDF Edit लागू नहीं हो पाया: " + str(exc))
                return redirect(url_for("upload_page"))
