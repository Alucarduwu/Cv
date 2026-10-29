"""Structured candidate profile, evidence-based forms and printable resume."""
import html, json, re, hashlib
from pathlib import Path
from typing import Any

def esc(value): return html.escape(str(value or ''), quote=True)
def normalize(profile):
    if not isinstance(profile,dict): raise ValueError('El perfil debe ser un objeto JSON')
    if not isinstance(profile.get('name'),str) or not profile['name'].strip(): raise ValueError('El nombre es obligatorio')
    for key in ('skills','experience','projects','education','certifications','languages'):
        if key in profile and not isinstance(profile[key],list): raise ValueError(f'{key} debe ser una lista')
    return profile

def text_item(x):
    if isinstance(x,str): return x
    if not isinstance(x,dict): return ''
    return ' | '.join([str(x[k]) for k in ('role','company','dates','title','institution','name','level','description') if x.get(k)] + [str(v) for v in x.get('highlights',[]) if v])

def text_matches(text,values):
    t=text.casefold();return [v for v in values if isinstance(v,str) and v and re.search(r'(?<!\w)'+re.escape(v.casefold())+r'(?!\w)',t)]

def resume_html(profile,job):
    p=normalize(profile);skills=p.get('skills',[]);matched=text_matches(job.get('description','')+' '+job.get('title',''),skills)
    order=matched+[s for s in skills if s not in matched]
    heading=p.get('headline','Profesional de tecnología');contact=p.get('contact',{})
    if not isinstance(contact,dict):contact={}
    info=' · '.join(str(contact.get(k,'')) for k in ('location','email','phone') if contact.get(k))
    links=' · '.join(str(contact.get(k) or p.get(k,'')) for k in ('portfolio','linkedin','github') if contact.get(k) or p.get(k))
    blocks=[]
    summary=p.get('summary','')
    if summary:blocks.append('<h2>Perfil profesional</h2><p>'+esc(summary)+'</p>')
    if order: blocks.append('<h2>Habilidades</h2><p>'+esc(', '.join(order))+'</p>')
    labels=[('experience','Experiencia profesional'),('projects','Proyectos'),('education','Educación'),('certifications','Certificaciones'),('languages','Idiomas')]
    for key,label in labels:
        entries=p.get(key,[])
        if not entries:continue
        part='<h2>'+esc(label)+'</h2>'
        for item in entries:
            if isinstance(item,dict):
                title=' · '.join(str(item[k]) for k in ('role','company','title','institution','name','dates','level') if item.get(k))
                part+='<div class="item"><strong>'+esc(title)+'</strong>'
                desc=item.get('description','')
                if desc:part+='<p>'+esc(desc)+'</p>'
                bullets=item.get('highlights',[])
                if isinstance(bullets,list) and bullets:part+='<ul>'+''.join('<li>'+esc(x)+'</li>' for x in bullets)+'</ul>'
                part+='</div>'
            else:part+='<p>'+esc(text_item(item))+'</p>'
        blocks.append(part)
    return '''<!doctype html><html lang="es"><head><meta charset="utf-8"><title>CV - '''+esc(p['name'])+'''</title><style>@page{size:letter;margin:18mm}body{font:10.5pt Arial,sans-serif;color:#162335;line-height:1.35;margin:0}h1{font-size:21pt;margin:0}h2{font-size:11pt;color:#1d4b70;text-transform:uppercase;border-bottom:1px solid #a7bdd0;margin:14px 0 5px}.meta{font-size:9pt}p{margin:4px 0}.item{margin:7px 0;break-inside:avoid}ul{margin:3px 0;padding-left:18px}</style></head><body><h1>'''+esc(p['name'])+'</h1><p>'+esc(heading)+'</p><p class="meta">'+esc(info)+'</p><p class="meta">'+esc(links)+'</p>'+''.join(blocks)+'</body></html>'

def form_answers(profile,questions):
    p=normalize(profile);c=p.get('contact') or {};c=c if isinstance(c,dict) else {}; result=[]
    # Only exact, evidence-grounded fields. Sensitive/ambiguous questions remain unanswered.
    patterns=[(r'^(full name|nombre completo|name)$',p.get('name'),'name'),(r'^(email|correo|correo electrónico|email address)$',c.get('email'),'contact.email'),(r'^(phone|teléfono|telefono|phone number)$',c.get('phone'),'contact.phone'),(r'^(linkedin|linkedin url|perfil de linkedin)$',c.get('linkedin'),'contact.linkedin'),(r'^(portfolio|portafolio|website)$',c.get('portfolio') or p.get('portfolio'),'contact.portfolio'),(r'^(city|ciudad|location|ubicación|ubicacion)$',c.get('location'),'contact.location')]
    for q in questions:
        question=str(q).strip();answer=None;evidence=None
        for pattern,value,source in patterns:
            if re.fullmatch(pattern,question.casefold()) and value:answer=str(value);evidence=source;break
        result.append({'question':question,'answer':answer,'source':evidence,'status':'known' if answer else 'needs_review'})
    return result

def career_fact_answers(profile,questions):
    """Basic fields plus user-curated question/answer pairs, never guess."""
    import unicodedata
    result=form_answers(profile,questions)
    def key(s):
        s=unicodedata.normalize('NFKC',str(s)).casefold()
        return ' '.join(re.sub(r'[^\w\s]',' ',s).split())
    known=profile.get('answers',[])
    if not isinstance(known,list):known=[]
    for item in result:
        if item['status']=='known':continue
        found=[x for x in known if isinstance(x,dict) and key(x.get('question',''))==key(item['question']) and x.get('answer')]
        if len(found)==1:item.update(answer=str(found[0]['answer']),source='answers: '+str(found[0]['question']),status='known')
    return result

def experience_fingerprint(profile):
    payload=json.dumps(profile.get('experience',[]),sort_keys=True,ensure_ascii=False,separators=(',',':'))
    return hashlib.sha256(payload.encode('utf8')).hexdigest()

def reviewed_experience(profile,overrides):
    original=profile.get('experience',[]);candidate=overrides.get('experience')
    if overrides.get('experience_fingerprint') != experience_fingerprint(profile): return original
    if not isinstance(candidate,list) or len(candidate)!=len(original): return original
    if not all(isinstance(x,str) and x.strip() for x in candidate): return original
    return candidate

def tailored_profile(profile,overrides):
    """Only these explicitly reviewed fields can be customized per job."""
    p=dict(normalize(profile));p['contact']=dict(profile.get('contact') or {})
    for key in ('headline','summary'):
        if key in overrides:p[key]=str(overrides[key]).strip()
    p['experience']=reviewed_experience(profile,overrides)
    return p

def resume_pdf(profile,job,overrides=None):
    """Generate an ATS-friendly searchable PDF using ReportLab, if installed."""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        import io
    except ImportError as exc:raise ValueError('Para generar PDF instala reportlab: python -m pip install -r requirements.txt') from exc
    p=tailored_profile(profile,overrides or {});buf=io.BytesIO();normal='Helvetica';bold='Helvetica-Bold'
    font=Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf');font_b=Path('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf')
    if font.exists() and font_b.exists():
        pdfmetrics.registerFont(TTFont('JPFont',str(font)));pdfmetrics.registerFont(TTFont('JPBold',str(font_b)));normal='JPFont';bold='JPBold'
    styles={'name':ParagraphStyle('name',fontName=bold,fontSize=16,leading=20,spaceAfter=6),'section':ParagraphStyle('section',fontName=bold,fontSize=10,leading=14,spaceBefore=9,spaceAfter=4),'body':ParagraphStyle('body',fontName=normal,fontSize=9,leading=13,spaceAfter=4)}
    story=[]
    def add(value,style='body'):story.append(Paragraph(esc(value).replace('\n','<br/>'),styles[style]))
    add(p['name'],'name');add(p.get('headline',''));contact=p.get('contact') or {};add(' | '.join(str(contact.get(k)) for k in ('location','email','phone') if contact.get(k)))
    add(' | '.join(str(contact.get(k) or p.get(k)) for k in ('portfolio','linkedin','github') if contact.get(k) or p.get(k)))
    if p.get('summary'):add('PERFIL','section');add(p['summary'])
    skills=p.get('skills',[]);matches=text_matches(job.get('title','')+' '+job.get('description',''),skills);ordered=matches+[x for x in skills if x not in matches]
    if ordered:add('HABILIDADES','section');add(', '.join(ordered))
    for key,label in [('experience','EXPERIENCIA'),('projects','PROYECTOS'),('education','EDUCACIÓN'),('certifications','CERTIFICACIONES'),('languages','IDIOMAS')]:
        if not p.get(key):continue
        add(label,'section')
        for entry in p[key]:add(text_item(entry))
    SimpleDocTemplate(buf,pagesize=letter,leftMargin=42,rightMargin=42,topMargin=40,bottomMargin=40,title='CV - '+p['name']).build(story)
    return buf.getvalue()
