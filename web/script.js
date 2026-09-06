const SESSION_ID = crypto.randomUUID();

const botonesPestana = document.querySelectorAll(".tab-btn");
const panelesPestana = document.querySelectorAll(".panel-tab");

function activarPanel(nombre) {
  botonesPestana.forEach((b) => b.classList.toggle("activo", b.dataset.panel === nombre));
  panelesPestana.forEach((p) => p.classList.toggle("activo", p.id === `panel-${nombre}`));
}

botonesPestana.forEach((boton) => {
  boton.addEventListener("click", () => activarPanel(boton.dataset.panel));
});

document.querySelectorAll(".btn-cotizar-card").forEach((boton) => {
  boton.addEventListener("click", () => activarPanel(boton.dataset.panel));
});

const elementoMensajes = document.getElementById("chat-mensajes");
const elementoCargando = document.getElementById("chat-cargando");
const elementoError = document.getElementById("chat-error");
const formulario = document.getElementById("chat-formulario");
const input = document.getElementById("chat-input");
const boton = document.getElementById("chat-boton");

function agregarMensaje(texto, emisor) {
  const burbuja = document.createElement("div");
  burbuja.classList.add("burbuja", emisor === "usuario" ? "burbuja-usuario" : "burbuja-agente");
  burbuja.textContent = texto;
  elementoMensajes.appendChild(burbuja);
  elementoMensajes.scrollTop = elementoMensajes.scrollHeight;
}

function ponerCargando(mostrar) {
  elementoCargando.hidden = !mostrar;
  boton.disabled = mostrar;
  input.disabled = mostrar;
}

function mostrarError(mostrar) {
  elementoError.hidden = !mostrar;
}

formulario.addEventListener("submit", async (evento) => {
  evento.preventDefault();

  const texto = input.value.trim();
  if (!texto) {
    return;
  }

  mostrarError(false);
  agregarMensaje(texto, "usuario");
  input.value = "";
  ponerCargando(true);

  try {
    const respuesta = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        mensaje: texto,
        session_id: SESSION_ID,
      }),
    });

    if (!respuesta.ok) {
      throw new Error(`Respuesta no exitosa: ${respuesta.status}`);
    }

    const datos = await respuesta.json();
    agregarMensaje(datos.respuesta, "agente");
  } catch (error) {
    console.error("Error al hablar con el asistente:", error);
    mostrarError(true);
  } finally {
    ponerCargando(false);
    input.focus();
  }
});

agregarMensaje(
  "Hola, cuéntame tu edad, si tienes auto propio y si tienes alguna condición de salud, y te recomiendo el seguro que más te conviene.",
  "agente"
);
