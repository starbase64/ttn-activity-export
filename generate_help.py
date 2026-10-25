"""Rebuild embedded/HTML help from the bilingual Markdown manuals; no dependencies."""
from pathlib import Path
import re,html
root=Path(__file__).resolve().parent
# Small build-time renderer: no additional runtime dependency. Handles the manual's
# headings, paragraphs, fenced code, lists, links and pipe tables.
def inline(s):
 s=html.escape(s,quote=False)
 s=re.sub(r'`([^`]+)`',r'<code>\1</code>',s)
 s=re.sub(r'\*\*([^*]+)\*\*',r'<b>\1</b>',s)
 def link(m):
  target=m[2]
  if not target.startswith(('https://','http://','#')):target='https://github.com/starbase64/ttn-activity-export/blob/main/docs/'+target
  return '<a href="'+html.escape(target,quote=True)+'">'+m[1]+'</a>'
 return re.sub(r'\[([^]]+)\]\(([^)]+)\)',link,s)
def render(s):
 out=[];lines=s.splitlines();i=0
 while i<len(lines):
  line=lines[i]
  if line.startswith('```'):
   block=[];i+=1
   while i<len(lines) and not lines[i].startswith('```'):block.append(lines[i]);i+=1
   out.append('<pre>'+html.escape('\n'.join(block))+'</pre>')
  elif line.startswith('#'):
   m=re.match(r'(#+) (.*)',line)
   if m:
    heading=m[2];anchor=re.sub(r'[^\w\- ]','',heading.lower()).replace(' ','-');out.append(f'<h{len(m[1])} id="{anchor}">'+inline(heading)+f'</h{len(m[1])}>')
  elif line.startswith('|'):
   rows=[]
   while i<len(lines) and lines[i].startswith('|'):
    parts=lines[i].strip('|').split('|')
    if not all(re.fullmatch(r'[ :\-]+',x) for x in parts):rows.append('<tr>'+''.join('<td>'+inline(x.strip())+'</td>' for x in parts)+'</tr>')
    i+=1
   out.append('<table border="1" cellspacing="0" cellpadding="6">'+''.join(rows)+'</table>');continue
  elif re.match(r'^(- |\d+\. )',line):
   ordered=line[0].isdigit();tag='ol' if ordered else 'ul';parts=[]
   while i<len(lines) and re.match(r'^(- |\d+\. )',lines[i]):
    parts.append('<li>'+inline(re.sub(r'^(- |\d+\. )','',lines[i]))+'</li>');i+=1
   out.append('<'+tag+'>'+''.join(parts)+'</'+tag+'>');continue
  elif line.strip():out.append('<p>'+inline(line)+'</p>')
  i+=1
 return '\n'.join(out)
help={}
for lang,name in [('de','ANLEITUNG.md'),('en','USER_GUIDE.md')]:
 body=render((root/'docs'/name).read_text());help[lang]=body
 (root/'docs'/f'guide-{lang}.html').write_text(f'<!doctype html><html lang="{lang}"><meta charset="utf-8"><title>TTN Activity Export</title><body>{body}</body></html>')
(root/'help_content.py').write_text('"""Bilingual manual, generated from docs/ANLEITUNG.md and docs/USER_GUIDE.md."""\nHELP = '+repr(help)+'\n')
