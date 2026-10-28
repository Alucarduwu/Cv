'use strict';
let profile=null, plan=null, active=null;
const file=document.getElementById('file'), preview=document.getElementById('preview'), apply=document.getElementById('apply'), status=document.getElementById('status'), items=document.getElementById('items');
file.addEventListener('change',async()=>{plan=null;apply.disabled=true;items.replaceChildren();try{const f=file.files[0];if(!f||f.size>1024*1024)throw Error('Selecciona un JSON de menos de 1 MB.');const p=JSON.parse(await f.text());if(!p||typeof p!=='object'||typeof p.name!=='string'||typeof p.contact!=='object')throw Error('El archivo no es un perfil de JobPilot válido.');profile=p;preview.disabled=false;status.textContent='Perfil listo para revisar.'}catch(e){profile=null;preview.disabled=true;status.textContent=e.message}});
// Serialized by chrome.scripting; does not submit, click, or read hidden fields.
function inspectAndFill(profile,approved){
 const norm=s=>(s||'').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/[^a-z0-9]+/g,' ').trim();
 const values={name:profile.name,email:profile.contact.email,phone:profile.contact.phone,linkedin:profile.contact.linkedin,portfolio:profile.contact.portfolio,location:profile.contact.location};
 const aliases={name:['full name','nombre completo','nombre y apellidos'],email:['email','email address','correo','correo electronico'],phone:['phone','phone number','telefono','numero de telefono'],linkedin:['linkedin','linkedin url','linkedin profile','perfil de linkedin'],portfolio:['portfolio','portfolio url','portafolio','sitio web'],location:['city','location','ciudad','ubicacion']};
 const autocompletes={'name':'name','email':'email','tel':'phone','address-level2':'location'};
 const candidates=Array.from(document.querySelectorAll('input,textarea')).filter(e=>{const t=(e.type||'text').toLowerCase();return !e.disabled&&!e.readOnly&&!e.value&&e.getClientRects().length>0&&!['hidden','password','file','checkbox','radio','submit','button','number','date'].includes(t)});
 const found=[];
 for(const el of candidates){
  const labels=[...Array.from(el.labels||[]).map(x=>x.innerText),el.getAttribute('aria-label'),el.placeholder].map(norm).filter(Boolean);
  const ac=(el.getAttribute('autocomplete')||'').trim().toLowerCase();let keys=Object.keys(aliases).filter(k=>labels.some(l=>aliases[k].includes(l)));if(autocompletes[ac])keys.push(autocompletes[ac]);keys=[...new Set(keys)];if(keys.length!==1)continue;
  const key=keys[0],value=values[key];if(typeof value!=='string'||!value.trim())continue;
  const index=Array.from(document.querySelectorAll('input,textarea')).indexOf(el);found.push({index,key,label:labels[0]||ac,value:value.trim()});
 }
 if(!approved)return found;
 let filled=0;
 for(const item of approved){const match=found.find(x=>x.index===item.index&&x.key===item.key&&x.value===item.value&&x.label===item.label);if(!match)continue;const el=document.querySelectorAll('input,textarea')[item.index];const proto=el.tagName==='TEXTAREA'?HTMLTextAreaElement.prototype:HTMLInputElement.prototype;Object.getOwnPropertyDescriptor(proto,'value').set.call(el,item.value);el.dispatchEvent(new Event('input',{bubbles:true}));el.dispatchEvent(new Event('change',{bubbles:true}));filled++}
 return {filled,skipped:approved.length-filled};
}
preview.addEventListener('click',async()=>{try{const [tab]=await chrome.tabs.query({active:true,currentWindow:true});if(!tab?.id||!tab.url?.startsWith('https://'))throw Error('Abre una vacante HTTPS en la pestaña activa.');const [{result}]=await chrome.scripting.executeScript({target:{tabId:tab.id},func:inspectAndFill,args:[profile,null]});active={id:tab.id,url:tab.url};plan=result;items.replaceChildren();for(const p of plan){const li=document.createElement('li');li.textContent=p.label+': '+p.value;items.append(li)}status.textContent=plan.length?new URL(tab.url).hostname+' · '+plan.length+' campos encontrados':'No encontré campos básicos vacíos y reconocibles.';apply.disabled=!plan.length}catch(e){status.textContent='No se pudo previsualizar: '+e.message;apply.disabled=true}});
apply.addEventListener('click',async()=>{try{const [tab]=await chrome.tabs.query({active:true,currentWindow:true});if(!active||tab.id!==active.id||tab.url!==active.url)throw Error('La página cambió. Vuelve a previsualizar.');const [{result}]=await chrome.scripting.executeScript({target:{tabId:tab.id},func:inspectAndFill,args:[profile,plan]});status.textContent=`${result.filled} campos rellenados; ${result.skipped} omitidos. Revisa y envía tú.`;apply.disabled=true;plan=null}catch(e){status.textContent='No se pudo rellenar: '+e.message;apply.disabled=true}});
