import zipfile, re, sys
sys.stdout.reconfigure(encoding='utf-8')
z = zipfile.ZipFile(r'C:\Users\Asus\Desktop\FYP code\MLFlu\old_wrong_reports\MIFlu_导师五大疑问_回复报告.docx')
xml = z.read('word/document.xml').decode('utf-8')
text = re.sub(r'<[^>]+>', ' ', xml)
text = re.sub(r'\s+', ' ', text)
# Find the section about Aggregation Policy / plotting
for keyword in ['Aggregation', 'aggregation', '融合机制', 'plot', 'graph', '图', 'step=0', 'step 0', 'denormaliz', '去归一化']:
    idx = text.find(keyword)
    if idx >= 0:
        print(f"=== Found '{keyword}' at {idx} ===")
        print(text[max(0,idx-200):idx+2000])
        print()
