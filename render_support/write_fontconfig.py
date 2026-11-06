from pathlib import Path
from html import escape
p = Path(__file__).resolve().parent
xml = '<?xml version="1.0"?><!DOCTYPE fontconfig SYSTEM "fonts.dtd"><fontconfig><include ignore_missing="yes">/etc/fonts/fonts.conf</include><dir>' + escape(str(p / 'fonts')) + '</dir></fontconfig>'
(p / 'fonts.conf').write_text(xml)
print(p / 'fonts.conf')
