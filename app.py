"""Local-only JobPilot UI. Not intended for Internet exposure."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit
from pathlib import Path
import html,json,os,secrets,sys
import jobpilot,career,intelligence

TOKEN=secrets.token_urlsafe(32);PROFILE=jobpilot.DATA/'profile.json';DEFAULT=jobpilot.BASE/'examples/profile.full.demo.json'
def read_profile():return career.normalize(json.loads((PROFILE if PROFILE.exists() else DEFAULT).read_text(encoding='utf8')))
def h(s):return html.escape(str(s),quote=True)
def shell(body):
 return '''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>JobPilot AI</title><style>body{font:16px system-ui;background:#f2f5fb;color:#172439;margin:0}header,main{max-width:1000px;margin:auto;padding:20px}header{display:flex;align-items:center;gap:22px;flex-wrap:wrap}a{color:#3159a5}nav{display:flex;gap:16px;flex-wrap:wrap}.card{background:#fff;border:1px solid #dce4f1;border-radius:14px;padding:20px;margin:14px 0}textarea,input,select{box-sizing:border-box;width:100%;padding:10px;border:1px solid #bac9dd;border-radius:8px;font:inherit}textarea{font:13px ui-monospace,monospace}button,.button{display:inline-block;background:#305ad6;color:#fff;border:0;border-radius:8px;padding:10px 16px;cursor:pointer;text-decoration:none}code,pre{white-space:pre-wrap;overflow-wrap:anywhere}small{color:#52647c}.badge{background:#e8efff;border-radius:20px;padding:4px 9px;font-size:13px}</style></head><body><header><strong>✦ JobPilot AI</strong><nav><a href="/">Inicio</a><a href="/profile">Mi perfil</a><a href="/jobs">Vacantes</a><a href="/sources">Buscar fuentes</a><a href="/add">Añadir vacante</a></nav></header><main>'''+body+'</main></body></html>'
def token():return '<input type="hidden" name="token" value="'+TOKEN+'">'
def read_form(handler):
 n=int(handler.headers.get('Content-Length','0'))
 if n>1024*1024:raise ValueError('Formulario demasiado grande')
 values=parse_qs(handler.rfile.read(n).decode('utf8'),keep_blank_values=True)
 if values.get('token',[''])[0]!=TOKEN:raise ValueError('Solicitud inválida')
 return {k:v[0] for k,v in values.items()}
def job_form(j):
 safe_url=j['url'] if urlsplit(j['url']).scheme=='https' else '#'
 return '<div class="card"><span class="badge">'+h(j['score'])+'/100 · '+h(j['source'])+'</span><h2>'+h(j['title'])+'</h2><p>'+h(j['company'])+' · '+h(j['location'])+'</p><p><a href="'+h(safe_url)+'" rel="noreferrer" target="_blank">Ver oferta original ↗</a></p><p>'+h(j['description'][:850])+'</p><p><a class="button" href="/job?id='+h(__import__('urllib.parse',fromlist=['quote']).quote(j['id'],safe=''))+'">Preparar candidatura</a></p></div>'
class Handler(BaseHTTPRequestHandler):
 def end(self,status,body,ctype='text/html; charset=utf-8'):
  data=body.encode('utf8');self.send_response(status);self.send_header('Content-Type',ctype);self.send_header('Content-Length',str(len(data)));self.send_header('X-Content-Type-Options','nosniff');self.send_header('Content-Security-Policy',"default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'");self.end_headers();self.wfile.write(data)
 def do_GET(self):
  try:
   parts=urlsplit(self.path);params=parse_qs(parts.query);path=parts.path
   if path=='/':
    jobs=jobpilot.rows('SELECT * FROM jobs');history=jobpilot.rows('SELECT * FROM applications');stats=intelligence.analytics(jobs,history)
    body='<h1>Tu búsqueda, con contexto</h1><p>Construye tu perfil, analiza una vacante y prepara una candidatura con evidencia.</p><div class="card"><h2>Resumen</h2><p>'+str(len(jobs))+' vacantes guardadas · '+str(len(history))+' intentos registrados</p><p><a class="button" href="/profile">Configurar mi perfil</a> <a href="/jobs">Revisar vacantes</a></p></div><div class="card"><h2>Perfil privado local</h2><p>El perfil se guarda en <code>data/profile.json</code> en esta computadora. El CV usa solo los datos que captures.</p></div>'
   elif path=='/profile':
    profile=read_profile();contact=profile.get('contact',{}) or {}
    def inp(name,label,value):return '<label>'+h(label)+'<input name="'+h(name)+'" value="'+h(value)+'"></label><p></p>'
    def area(name,label,value,rows=4):return '<label>'+h(label)+'<textarea name="'+h(name)+'" rows="'+str(rows)+'">'+h(value)+'</textarea></label><p></p>'
    def items(key):
     return '\n'.join(career.text_item(x) for x in profile.get(key,[]))
    fields=inp('name','Nombre completo',profile.get('name',''))+inp('headline','Título profesional',profile.get('headline',''))+area('summary','Resumen profesional',profile.get('summary',''))
    for key,label in [('location','Ubicación'),('email','Correo'),('phone','Teléfono'),('portfolio','Portafolio'),('linkedin','LinkedIn'),('github','GitHub')]:fields+=inp('contact_'+key,label,contact.get(key,'') or profile.get(key,''))
    fields+=area('skills','Tecnologías y habilidades, separadas por comas',', '.join(profile.get('skills',[])))
    for key,label in [('experience','Experiencia'),('projects','Proyectos'),('education','Educación'),('certifications','Certificaciones'),('languages','Idiomas')]: fields+=area(key,label+' (una entrada por línea)',items(key),5)
    body='<h1>Mi perfil</h1><p>Agrega tus datos una vez. Escribe cada experiencia y proyecto en una línea con puesto, empresa, fechas y logros; no incluyas contraseñas.</p><form method="post" action="/profile">'+token()+'<div class="card">'+fields+'<button>Guardar perfil local</button></div></form>'

   elif path=='/jobs':
    jobs=jobpilot.rows('SELECT * FROM jobs');profile=read_profile()
    for j in jobs:j['score']=jobpilot.score_job(j,profile)[0]
    jobs.sort(key=lambda x:(-x['score'],x['title']));body='<h1>Vacantes</h1><p>Las puntuaciones son orientativas; revisa ubicación y requisitos.</p>'+(''.join(job_form(j) for j in jobs) if jobs else '<div class="card">Aún no hay vacantes. Añade una o carga la demostración.</div>')+'<form method="post" action="/demo">'+token()+'<button>Cargar vacantes de ejemplo</button></form>'
   elif path=='/sources':
    body='<h1>Buscar en fuentes</h1><p>Consulta una bolsa pública. Lever, Greenhouse y Ashby necesitan el identificador de la empresa; Remotive no lo necesita.</p><form class="card" action="/fetch" method="post">'+token()+'<label>Fuente<select name="source"><option value="lever">Lever</option><option value="greenhouse">Greenhouse</option><option value="ashby">Ashby</option><option value="remotive">Remotive</option></select></label><p><label>Identificador de empresa<input name="board" placeholder="Ejemplo: trueml"></label></p><button>Buscar vacantes</button></form><p><small>La búsqueda consulta un servicio externo. Verifica elegibilidad y ubicación antes de postular.</small></p>'
   elif path=='/add':
    body='<h1>Añadir vacante</h1><p>Para empezar, pega el texto del anuncio y su enlace original.</p><form class="card" action="/add" method="post">'+token()+''.join('<label>'+label+'<input name="'+name+'" '+('required' if name in ('title','company','url') else '')+'></label><p></p>' for name,label in [('title','Puesto'),('company','Empresa'),('location','Ubicación'),('url','Enlace https')])+'<label>Descripción<textarea name="description" rows="12" required></textarea></label><p><button>Guardar vacante</button></p></form>'
   elif path in ('/job','/resume'):
    j=jobpilot.one(params.get('id',[''])[0]);profile=read_profile()
    if path=='/resume':return self.end(200,career.resume_html(profile,j))
    import urllib.parse
    jid=urllib.parse.quote(j['id'],safe='');gaps=intelligence.gap_report(j,profile)
    body='<h1>Preparar candidatura</h1>'+job_form(j)+'<div class="card"><h2>CV adaptado</h2><p>Ordena primero las habilidades encontradas en la vacante y conserva toda tu experiencia. Abre el CV e imprime a PDF desde el navegador.</p><a class="button" target="_blank" href="/resume?id='+h(jid)+'">Abrir CV imprimible</a></div><div class="card"><h2>Coincidencias y posibles brechas</h2><pre>'+h(json.dumps(gaps,ensure_ascii=False,indent=2))+'</pre></div><div class="card"><h2>Asistente de IA</h2><p>Requiere un proveedor configurado; enviará tu perfil y la vacante a ese proveedor. Revisa las respuestas.</p><form method="post" action="/ai">'+token()+'<input type="hidden" name="id" value="'+h(j['id'])+'"><select name="task"><option value="review">Analizar ajuste</option><option value="resume">Sugerir adaptación del CV</option><option value="interview">Preparar entrevista</option><option value="outreach">Preparar mensaje</option></select><p><button>Generar con IA</button></p></form></div><div class="card"><h2>Respuestas del formulario</h2><p>Escribe una pregunta por línea. Las desconocidas quedan pendientes de revisión.</p><form method="post" action="/answers">'+token()+'<input type="hidden" name="id" value="'+h(j['id'])+'"><textarea name="questions" rows="6" placeholder="Nombre completo&#10;Correo electrónico&#10;¿Necesitas patrocinio?"></textarea><p><button>Preparar respuestas</button></p></form></div>'
   else:return self.end(404,shell('<h1>No encontrado</h1>'))
   self.end(200,shell(body))
  except (ValueError,KeyError,OSError,json.JSONDecodeError) as exc:self.end(400,shell('<h1>No se pudo completar</h1><p>'+h(exc)+'</p>'))
 def do_POST(self):
  try:
   f=read_form(self)
   if self.path=='/profile':
    p=read_profile();p['name']=f.get('name','').strip();p['headline']=f.get('headline','').strip();p['summary']=f.get('summary','').strip();p['skills']=[x.strip() for x in f.get('skills','').split(',') if x.strip()]
    p['contact']={k:f.get('contact_'+k,'').strip() for k in ('location','email','phone','portfolio','linkedin','github')}
    for key in ('experience','projects','education','certifications','languages'):p[key]=[x.strip() for x in f.get(key,'').splitlines() if x.strip()]
    career.normalize(p);tmp=PROFILE.with_suffix('.tmp');tmp.write_text(json.dumps(p,ensure_ascii=False,indent=2),encoding='utf8');os.chmod(tmp,0o600);tmp.replace(PROFILE);dest='/profile' 
   elif self.path=='/demo':
    jobs=json.loads((jobpilot.BASE/'examples/jobs.demo.json').read_text(encoding='utf8'));jobpilot.save_jobs(jobs,read_profile());dest='/jobs'
   elif self.path=='/fetch':
    source=f.get('source','');board=f.get('board','').strip() or None
    if board and (not __import__('re').fullmatch(r'[A-Za-z0-9_-]{1,100}',board)):raise ValueError('Identificador de empresa inválido')
    jobs=jobpilot.fetch_source(source,board);count=jobpilot.save_jobs(jobs,read_profile())
    return self.end(200,shell('<h1>Búsqueda completada</h1><div class="card"><p>'+str(count)+' vacantes registradas o actualizadas de '+h(source)+'.</p><a class="button" href="/jobs">Ver vacantes</a></div>'))
   elif self.path=='/add':
    url=f.get('url','').strip();u=urlsplit(url)
    if u.scheme!='https' or not u.netloc:raise ValueError('La vacante necesita una URL https válida')
    if not all(f.get(k,'').strip() for k in ('title','company','description')):raise ValueError('Completa los campos obligatorios')
    import hashlib
    j={k:f.get(k,'').strip() for k in ('title','company','location','url','description')};j.update(id='manual:'+hashlib.sha256(url.encode()).hexdigest()[:20],source='manual');jobpilot.save_jobs([j],read_profile());dest='/jobs'
   elif self.path=='/ai':
    j=jobpilot.one(f.get('id','')); result=intelligence.ai_workflow(f.get('task',''),j,read_profile())
    return self.end(200,shell('<h1>Resultado de IA</h1><div class="card"><pre>'+h(json.dumps(result,ensure_ascii=False,indent=2))+'</pre><p>Comprueba cada dato antes de usarlo.</p></div>'))
   elif self.path=='/answers':
    jobpilot.one(f.get('id',''));questions=[x.strip() for x in f.get('questions','').splitlines() if x.strip()];result=career.form_answers(read_profile(),questions)
    return self.end(200,shell('<h1>Respuestas preparadas</h1><div class="card"><pre>'+h(json.dumps(result,ensure_ascii=False,indent=2))+'</pre><p>Revisa antes de copiar al formulario. No se envió una solicitud.</p></div>'))
   else: return self.end(404,shell('No encontrado'))
   self.send_response(303);self.send_header('Location',dest);self.end_headers()
  except (ValueError,KeyError,OSError,json.JSONDecodeError) as exc:self.end(400,shell('<h1>No se pudo completar</h1><p>'+h(exc)+'</p>'))
 def log_message(self,format,*args):pass
if __name__=='__main__':
 port=int(os.environ.get('JOBPILOT_PORT','8765'));print(f'JobPilot: http://127.0.0.1:{port}',flush=True);ThreadingHTTPServer(('127.0.0.1',port),Handler).serve_forever()
