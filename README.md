# JobPilot AI

Asistente de búsqueda de empleo hecho en Python para un portafolio de desarrollo. Descubre vacantes de APIs públicas, calcula una puntuación explicable, prepara borradores con o sin IA y registra envíos para evitar duplicados. Incluye un conjunto de demostración ficticio; no contiene CV, contraseñas ni datos reales.

## Demostración en dos minutos

Requiere Python 3.10 o posterior; usa únicamente la biblioteca estándar.

```bash
python3 jobpilot.py demo
python3 jobpilot.py list
python3 jobpilot.py draft demo:001
python3 -m unittest discover -s tests -v
```

La puntuación es una heurística (coincidencias de habilidades, remoto, región y nivel), no una predicción de contratación. Una mención de México o remoto no demuestra elegibilidad: lee siempre la descripción completa. Para borrar únicamente datos de prueba, elimina la carpeta `data`.

## Usar tu perfil y buscar vacantes

Copia `examples/profile.demo.json` a `profile.private.json`, edítalo con tus datos reales y habilidades verificables y usa `--profile profile.private.json` **antes** del subcomando. El perfil privado y CV están excluidos de Git.

```bash
python3 jobpilot.py --profile profile.private.json fetch lever trueml
python3 jobpilot.py --profile profile.private.json fetch greenhouse outsetmedical
python3 jobpilot.py --profile profile.private.json list
python3 jobpilot.py --profile profile.private.json draft 'lever:trueml:ID_REAL' --output draft.json
```

Los identificadores de empresa deben corresponder a bolsas públicas existentes; los resultados reales necesitan red y dependen de las fuentes. También puedes importar JSON con `import-json examples/jobs.demo.json`. La clave única por vacante actualiza los registros existentes sin duplicarlos.

## Borrador de IA opcional

Configura un proveedor compatible con Chat Completions y su endpoint HTTPS, modelo y clave en variables de entorno locales:

```bash
export JOBPILOT_AI_URL='https://TU-PROVEEDOR/v1/chat/completions'
export JOBPILOT_AI_MODEL='TU-MODELO'
export JOBPILOT_AI_KEY='TU-CLAVE'
python3 jobpilot.py --profile profile.private.json draft 'lever:trueml:ID_REAL' --ai --output propuesta.json
```

Esta opción transmite el perfil y la descripción al proveedor configurado y puede tener costo. El resultado incluye habilidades coincidentes, brechas y sugerencias para adaptar el CV; revísalo porque la IA puede equivocarse. Este prototipo no genera automáticamente un PDF ATS ni verifica afirmaciones por sí mismo.

## Envío de correo tras revisión

El envío no es automático: prepara un archivo de texto con el mensaje revisado, selecciona el PDF adaptado y verifica que el destinatario corresponde a la vacante. Configura un servidor SMTP con STARTTLS, usuario y credencial apropiada (consulta la documentación de tu proveedor; no uses tu contraseña normal si requiere una contraseña de aplicación). No incluyas credenciales en el código ni en capturas.

```bash
export JOBPILOT_SMTP_HOST='smtp.tu-proveedor.com'
export JOBPILOT_SMTP_PORT=587
export JOBPILOT_SMTP_USER='tu-correo@ejemplo.com'
export JOBPILOT_SMTP_PASSWORD='TU-CREDENCIAL'
python3 jobpilot.py --profile profile.private.json send 'ID_REAL' --to 'reclutamiento@empresa.com' --subject 'Postulación' --body mensaje.txt --cv CV_adaptado.pdf --confirm-send
python3 jobpilot.py history
```

Un envío aceptado por SMTP no garantiza entrega o entrevista. Cada intento reserva la vacante antes de enviar y bloquea reintentos automáticos; si falla, queda `uncertain`, ya que el servidor pudo aceptar el mensaje. Verifica en correos enviados antes de corregir el historial. Nunca automatiza CAPTCHAs, LinkedIn ni portales sin autorización. No lee ni rellena preguntas de formularios automáticamente; abre el enlace oficial para terminar la solicitud.

## Estructura y decisiones

- `jobpilot.py`: extracción, clasificación, SQLite, borradores y correo.
- `examples/`: perfil y vacantes ficticias para mostrar el proyecto sin datos personales.
- `tests/`: pruebas con bases temporales y SMTP simulado.
- `data/jobpilot.db`: historial privado local, creado al ejecutar.
- APIs oficiales: [Lever Postings API](https://github.com/lever/postings-api) y [Greenhouse Job Board API](https://developers.greenhouse.io/job-board.html).

Ideas para evolución: interfaz web, adaptador de CV PDF, métricas de conversión, conectores permitidos por cada plataforma y evaluación de extracción/precisión con conjunto etiquetado.

## Flujos de inteligencia y datos

```bash
python3 jobpilot.py gaps demo:001
python3 jobpilot.py analytics
python3 jobpilot.py workflow review demo:001
python3 jobpilot.py workflow resume demo:001 --output propuesta.json
python3 jobpilot.py workflow interview demo:001
python3 jobpilot.py workflow outreach demo:001
```

`gaps` y `analytics` funcionan sin servicios externos: detectan menciones de habilidades y muestran métricas únicamente de vacantes importadas. No son modelos predictivos ni sustituyen revisión. Los cuatro comandos `workflow` usan el proveedor configurado para generar análisis de ajuste, propuestas para adaptar el CV, preparación de entrevista y mensajes personalizados. Requieren las tres variables de IA documentadas arriba, transmiten perfil y vacante al proveedor, y sus resultados deben verificarse. No crean PDF ni envían mensajes por sí solos. Las citas de evidencia las genera el modelo y no están verificadas automáticamente.

## Cómo presentarlo en una entrevista

JobPilot es un prototipo construido con Python y asistencia de IA. Integra APIs públicas de empleo, almacenamiento en SQLite, procesamiento de texto con reglas transparentes, una interfaz CLI, flujos opcionales de modelos de lenguaje y una capa de seguridad contra envíos duplicados. Las pruebas simulan SMTP; no requieren credenciales. La integración de IA debe configurarse con un proveedor externo y revisar cada resultado. Los datos y ejemplos del repositorio son ficticios.

El archivo de automatización de GitHub Actions ejecuta pruebas y una demostración en Python 3.10 y 3.12 en cada cambio. Para ejecutar localmente:

```bash
python -m unittest discover -s tests -v
```
