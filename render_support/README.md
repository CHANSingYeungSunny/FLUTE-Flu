# Rendering fonts

These bundled fonts support the local Latin and Chinese DOCX/PDF renderings. Use the font licences shipped with the files. The class-derived English PDF uses LaTeX fonts and does not depend on this font bundle. Run `python render_support/write_fontconfig.py` to generate fonts.conf using this extracted project path, then set `FONTCONFIG_FILE="$PWD/render_support/fonts.conf"` before the DOCX renderer or LibreOffice. Font substitution can change Word pagination.
