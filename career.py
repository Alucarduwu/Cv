"""Structured candidate profile, evidence-based forms and printable resume."""
import html, json, re
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
