from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from agent.agent import root_agent

import logging
logging.basicConfig(level=logging.INFO)

app = FastAPI()

session_service = InMemorySessionService()
runner = Runner(
    agent=root_agent,
    app_name="cotizador_seguros",
    session_service=session_service,
)

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