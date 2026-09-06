# Cotizador de Seguros con IA

Agente conversacional que recomienda productos de seguro (vida, auto, salud) según la situación de una persona: edad, si tiene vehículo propio, y condiciones de salud. Proyecto personal para practicar Google ADK, FastAPI y despliegue en GCP.

## Cómo funciona

El agente conversa con el usuario hasta completar 3 datos (edad, si tiene auto, condiciones de salud). Una vez los tiene, consulta un catálogo de productos de seguro y devuelve solo los que aplican a esa situación, sin inventar productos ni precios.

## Stack técnico

- **Google ADK (Agent Development Kit)**: define el agente (`root_agent`), su instrucción y sus herramientas.
- **Gemini 2.5 Flash** (vía Vertex AI): el modelo que razona y decide qué responder.
- **FastAPI + Uvicorn**: exponen el agente como una API REST.
- **Docker + Google Cloud Run**: empaquetan y despliegan la API en la nube, sin servidores que administrar a mano.

## Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/` | Healthcheck, confirma que la API está corriendo |
| POST | `/cotizar` | Recibe `{edad, tiene_auto, condiciones}` y devuelve `{recomendacion}` |
| POST | `/chat` | Recibe `{mensaje, session_id}`, mantiene una conversación de varios turnos, devuelve `{respuesta}` |
| GET | `/asistente` | Interfaz web de chat que consume `/chat` |
| GET | `/docs` | Documentación interactiva autogenerada por FastAPI (Swagger) |

## Cómo correrlo en local

```bash
git clone https://github.com/adrian-farfan/cotizador-seguros-adk.git
cd cotizador-seguros-adk
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Crea un archivo `.env` en la raíz con:

```
GOOGLE_GENAI_USE_VERTEXAI=True
GOOGLE_CLOUD_PROJECT=tu-proyecto-de-gcp
GOOGLE_CLOUD_LOCATION=us-central1
```

Y corre:

```bash
uvicorn main:app --reload
```

## Despliegue

Se despliega en Google Cloud Run con:

```bash
gcloud run deploy cotizador-seguros \
  --source . \
  --project=agente-cotizador-seguros-adk \
  --region=us-central1 \
  --allow-unauthenticated \
  --set-env-vars=GOOGLE_GENAI_USE_VERTEXAI=True,GOOGLE_CLOUD_PROJECT=agente-cotizador-seguros-adk,GOOGLE_CLOUD_LOCATION=us-central1
```

**Demo en vivo:** https://cotizador-seguros-preview-402274301854.us-central1.run.app/asistente/

---

Proyecto personal de Adrián Farfán, estudiante de Ingeniería de Sistemas en la Universidad de Lima.