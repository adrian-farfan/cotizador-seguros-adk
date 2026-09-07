import re
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.cloud import logging as cloud_logging
from google.genai import types

from agent.agent import root_agent

import logging
logging.basicConfig(level=logging.INFO)

PRECIO_ENTRADA_POR_MILLON = 0.30   # USD, Gemini 2.5 Flash
PRECIO_SALIDA_POR_MILLON = 2.50    # USD, Gemini 2.5 Flash
PATRON_FINOPS = re.compile(r"tokens_entrada=(\d+) - tokens_salida=(\d+)")

app = FastAPI()

session_service = InMemorySessionService()
runner = Runner(
    agent=root_agent,
    app_name="cotizador_seguros",
    session_service=session_service,
)
cliente_logging = cloud_logging.Client()

WEB_DIR = Path(__file__).parent / "web"

app.mount("/asistente", StaticFiles(directory=WEB_DIR, html=True), name="asistente")


class SolicitudCotizacion(BaseModel):
    edad: int
    tiene_auto: bool
    condiciones: list[str]


@app.get("/")
def read_root():
    return {"mensaje": "API del cotizador de seguros funcionando"}


@app.post("/cotizar")
async def cotizar(solicitud: SolicitudCotizacion):
    session = await session_service.create_session(
        app_name="cotizador_seguros",
        user_id="usuario_api",
    )

    mensaje = (
        f"Tengo {solicitud.edad} años, "
        f"{'tengo' if solicitud.tiene_auto else 'no tengo'} auto, "
        f"y mis condiciones de salud son: {solicitud.condiciones or 'ninguna'}."
    )
    contenido = types.Content(role="user", parts=[types.Part(text=mensaje)])

    respuesta_final = ""
    tokens_entrada = 0
    tokens_salida = 0
    async for evento in runner.run_async(
        user_id="usuario_api",
        session_id=session.id,
        new_message=contenido,
    ):
        if evento.usage_metadata:
            tokens_entrada += evento.usage_metadata.prompt_token_count or 0
            tokens_salida += evento.usage_metadata.candidates_token_count or 0
        if evento.is_final_response():
            respuesta_final = evento.content.parts[0].text

    logging.info(f"[FinOps] /cotizar - sesion={session.id} - tokens_entrada={tokens_entrada} - tokens_salida={tokens_salida}")

    return {"recomendacion": respuesta_final}


class MensajeChat(BaseModel):
    mensaje: str = Field(min_length=1)
    session_id: str = Field(min_length=1)


@app.post("/chat")
async def chat(payload: MensajeChat):
    session = await session_service.get_session(
        app_name="cotizador_seguros",
        user_id="usuario_web",
        session_id=payload.session_id,
    )
    if session is None:
        session = await session_service.create_session(
            app_name="cotizador_seguros",
            user_id="usuario_web",
            session_id=payload.session_id,
        )

    contenido = types.Content(role="user", parts=[types.Part(text=payload.mensaje)])

    respuesta_final = ""
    tokens_entrada = 0
    tokens_salida = 0
    async for evento in runner.run_async(
        user_id="usuario_web",
        session_id=session.id,
        new_message=contenido,
    ):
        if evento.usage_metadata:
            tokens_entrada += evento.usage_metadata.prompt_token_count or 0
            tokens_salida += evento.usage_metadata.candidates_token_count or 0
        if evento.is_final_response():
            respuesta_final = evento.content.parts[0].text

    logging.info(f"[FinOps] /chat - sesion={session.id} - tokens_entrada={tokens_entrada} - tokens_salida={tokens_salida}")

    return {"respuesta": respuesta_final}


@app.get("/finops", response_class=HTMLResponse)
def finops():
    filtro = (
        'resource.type="cloud_run_revision" '
        'resource.labels.service_name="cotizador-seguros" '
        'textPayload:"[FinOps]"'
    )

    total_entrada = 0
    total_salida = 0
    total_llamadas = 0

    for entrada in cliente_logging.list_entries(filter_=filtro, page_size=1000):
        coincidencia = PATRON_FINOPS.search(entrada.payload or "")
        if coincidencia:
            total_entrada += int(coincidencia.group(1))
            total_salida += int(coincidencia.group(2))
            total_llamadas += 1

    costo_entrada = total_entrada / 1_000_000 * PRECIO_ENTRADA_POR_MILLON
    costo_salida = total_salida / 1_000_000 * PRECIO_SALIDA_POR_MILLON
    costo_total = costo_entrada + costo_salida

    return f"""
    <html>
      <head><title>FinOps - Cotizador de Seguros</title></head>
      <body style="font-family: sans-serif; max-width: 600px; margin: 40px auto;">
        <h1>Consumo del agente (Gemini 2.5 Flash)</h1>
        <table style="border-collapse: collapse; width: 100%;">
          <tr><td>Llamadas al agente</td><td>{total_llamadas}</td></tr>
          <tr><td>Tokens de entrada</td><td>{total_entrada:,}</td></tr>
          <tr><td>Tokens de salida</td><td>{total_salida:,}</td></tr>
          <tr><td><b>Costo estimado</b></td><td><b>${costo_total:.4f} USD</b></td></tr>
        </table>
        <p style="color: gray; font-size: 0.9em;">
          Datos leídos en vivo desde Cloud Logging. Precios de Gemini 2.5 Flash:
          $0.30 / 1M tokens entrada, $2.50 / 1M tokens salida.
        </p>
      </body>
    </html>
    """
