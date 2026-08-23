import streamlit as st
import os
import time
import glob
import unicodedata
from gtts import gTTS
from PIL import Image

# Librería opcional para el juego "encuentra al ratón" (click sobre la imagen)
try:
    from streamlit_image_coordinates import streamlit_image_coordinates
    TIENE_COORDENADAS = True
except ImportError:
    TIENE_COORDENADAS = False

st.set_page_config(page_title="El Renacuajo Paseador - Audiocuento", page_icon="🐸", layout="centered")

# ---------------------------------------------------------------------------
# CONFIGURACIÓN GENERAL
# ---------------------------------------------------------------------------
try:
    os.mkdir("temp")
except FileExistsError:
    pass

# Carpeta donde debes poner las 3 imágenes del cuento (creala en tu repo)
IMG_DIR = "imagenes"
IMG_PARRAFO_1 = os.path.join(IMG_DIR, "parrafo1.jpg")   # Rinrín con sombrero, corbata, etc.
IMG_PARRAFO_2 = os.path.join(IMG_DIR, "parrafo2.jpg")   # Escena con el ratón (para encontrarlo)
IMG_PARRAFO_3 = os.path.join(IMG_DIR, "parrafo3.jpg")   # Ilustración final / abuela ratona

# Textos de los 3 párrafos del cuento
PARRAFOS = {
    1: ("El hijo de rana, Rinrín renacuajo, salió esta mañana muy tieso y muy majo, "
        "con pantalón corto, corbata a la moda, sombrero encintado y chupa de boda."
        "-¡Muchacho, no salgas!- le grita mamá pero él hace un gesto y orondo se va."),
    2: ("Halló en el camino, a un ratón vecino y le dijo: ¡amigo!"),
    3: ("-Venga usted conmigo, visitemos juntos a doña ratona y habrá francachela y habrá comilona."
        "A poco llegaron, y avanza ratón, estírase el cuello, coge el aldabón,"
        "da dos o tres golpes, preguntan: ¿quién es? -Yo, doña ratona, beso a usted los pies."),
}

# ---------------------------------------------------------------------------
# UTILIDADES
# ---------------------------------------------------------------------------
def quitar_acentos(texto):
    texto = texto.lower().strip()
    return "".join(
        c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn"
    )

def texto_a_audio(texto, lg, nombre_archivo):
    tts = gTTS(texto, lang=lg)
    ruta = f"temp/{nombre_archivo}.mp3"
    tts.save(ruta)
    return ruta

def mostrar_imagen_o_subir(ruta, etiqueta, key):
    """Muestra la imagen del repo si existe; si no, permite subirla (útil mientras pruebas)."""
    if os.path.exists(ruta):
        return Image.open(ruta)
    st.info(f"No encontré `{ruta}`. Súbela para probar, o colócala en la carpeta `{IMG_DIR}/` de tu repo.")
    archivo = st.file_uploader(etiqueta, type=["png", "jpg", "jpeg", "webp"], key=key)
    if archivo is not None:
        return Image.open(archivo)
    return None

def remove_files(n):
    mp3_files = glob.glob("temp/*mp3")
    if len(mp3_files) != 0:
        now = time.time()
        n_days = n * 86400
        for f in mp3_files:
            if os.stat(f).st_mtime < now - n_days:
                os.remove(f)

def bloque_audio(parrafo_num, lg):
    if st.button("🔊 Escuchar", key=f"audio_{parrafo_num}"):
        ruta = texto_a_audio(PARRAFOS[parrafo_num], lg, f"parrafo{parrafo_num}")
        with open(ruta, "rb") as f:
            st.audio(f.read(), format="audio/mp3")

# ---------------------------------------------------------------------------
# ESTADO DE LA SESIÓN
# ---------------------------------------------------------------------------
if "pagina" not in st.session_state:
    st.session_state.pagina = 1
if "puzzle1_ok" not in st.session_state:
    st.session_state.puzzle1_ok = False
if "puzzle2_ok" not in st.session_state:
    st.session_state.puzzle2_ok = False
if "puzzle3_ok" not in st.session_state:
    st.session_state.puzzle3_ok = False
if "maze_pos" not in st.session_state:
    st.session_state.maze_pos = [0, 0]  # fila, columna

# ---------------------------------------------------------------------------
# BARRA LATERAL
# ---------------------------------------------------------------------------
st.title("🐸 El Renacuajo Paseador — Audiocuento")
with st.sidebar:
    st.subheader("Cuento interactivo")
    st.write("Resuelve el reto de cada página para avanzar.")
    option_lang = st.selectbox("Idioma del audio", ("Español", "English"))
    lg = "es" if option_lang == "Español" else "en"
    st.progress(st.session_state.pagina / 3 if st.session_state.pagina <= 3 else 1.0)

remove_files(7)

# ---------------------------------------------------------------------------
# PÁGINA 1 — Puzzle: nombrar las prendas
# ---------------------------------------------------------------------------
if st.session_state.pagina == 1:
    st.header("Página 1")
    img1 = mostrar_imagen_o_subir(IMG_PARRAFO_1, "Sube la imagen del párrafo 1", "img1")
    if img1:
        st.image(img1, width=350)

    st.write(PARRAFOS[1])
    bloque_audio(1, lg)

    st.markdown("### 🧩 Reto: ¿qué prendas usa Rinrín?")
    st.caption("Escríbelas separadas por coma (ej: sombrero, corbata, pantalón, chupa).")
    respuesta = st.text_input("Tu respuesta:", key="resp1")

    palabras_clave = ["pantalon", "corbata", "sombrero", "chupa"]
    if st.button("Comprobar", key="check1"):
        respuesta_normalizada = quitar_acentos(respuesta)
        aciertos = sum(1 for palabra in palabras_clave if palabra in respuesta_normalizada)
        if aciertos >= 3:
            st.session_state.puzzle1_ok = True
            st.success("¡Muy bien! Rinrín llevaba pantalón, corbata, sombrero y chupa. 🎉")
        else:
            st.warning("Casi... revisa la descripción del párrafo y vuelve a intentar.")

    if st.session_state.puzzle1_ok:
        if st.button("Siguiente ▶", key="next1"):
            st.session_state.pagina = 2
            st.rerun()

# ---------------------------------------------------------------------------
# PÁGINA 2 — Puzzle: encuentra al ratón
# ---------------------------------------------------------------------------
elif st.session_state.pagina == 2:
    st.header("Página 2")
    st.write(PARRAFOS[2])
    bloque_audio(2, lg)

    st.markdown("### 🧩 Reto: encuentra al ratón en la imagen")

    if TIENE_COORDENADAS and os.path.exists(IMG_PARRAFO_2):
        # --- Ajusta este cuadro (x1, y1, x2, y2) a la posición real del ratón en tu imagen ---
        CAJA_RATON = (80, 260, 300, 660)
        st.caption("Haz clic sobre el ratón en la imagen.")
        coords = streamlit_image_coordinates(IMG_PARRAFO_2, key="click_raton")
        if coords is not None:
            x, y = coords["x"], coords["y"]
            if CAJA_RATON[0] <= x <= CAJA_RATON[2] and CAJA_RATON[1] <= y <= CAJA_RATON[3]:
                st.session_state.puzzle2_ok = True
                st.success("¡Lo encontraste! 🐭")
            else:
                st.warning("Ahí no está... ¡sigue buscando!")
    else:
        if not TIENE_COORDENADAS:
            st.info("Para el juego de 'clic sobre la imagen' instala `streamlit-image-coordinates` "
                     "(agrégalo a requirements.txt). Mientras tanto, responde aquí:")
        img2 = mostrar_imagen_o_subir(IMG_PARRAFO_2, "Sube la imagen del párrafo 2", "img2")
        if img2:
            st.image(img2, width=350)
        opcion = st.radio(
            "¿Dónde está el ratón?",
            ["Esquina superior izquierda", "Centro de la imagen", "Junto a la puerta", "Abajo a la derecha"],
            key="radio_raton",
        )
        if st.button("Comprobar", key="check2"):
            if opcion == "Junto a la puerta":
                st.session_state.puzzle2_ok = True
                st.success("¡Correcto, el ratón estaba junto a la puerta! 🐭")
            else:
                st.warning("No es ahí, ¡inténtalo de nuevo!")

    if st.session_state.puzzle2_ok:
        if st.button("Siguiente ▶", key="next2"):
            st.session_state.pagina = 3
            st.rerun()

# ---------------------------------------------------------------------------
# PÁGINA 3 — Puzzle: laberinto hasta la abuela ratona
# ---------------------------------------------------------------------------
elif st.session_state.pagina == 3:
    st.header("Página 3")
    st.write(PARRAFOS[3])
    bloque_audio(3, lg)

    st.markdown("### 🧩 Reto: guía al renacuajo hasta la casa de la abuela ratona")
    st.caption("Usa los botones de flechas para moverte (⬛ = pared, 🐸 = tú, 👵 = meta).")

    FILAS, COLUMNAS = 5, 5
    PAREDES = {(1, 1), (1, 2), (2, 3), (3, 1), (3, 3)}
    META = (4, 4)

    def mover(dr, dc):
        f, c = st.session_state.maze_pos
        nf, nc = f + dr, c + dc
        if 0 <= nf < FILAS and 0 <= nc < COLUMNAS and (nf, nc) not in PAREDES:
            st.session_state.maze_pos = [nf, nc]
            if tuple(st.session_state.maze_pos) == META:
                st.session_state.puzzle3_ok = True

    col_izq, col_centro, col_der = st.columns([1, 1, 1])
    with col_centro:
        if st.button("⬆️", key="arriba"):
            mover(-1, 0)
    col_izq, col_centro, col_der = st.columns([1, 1, 1])
    with col_izq:
        if st.button("⬅️", key="izquierda"):
            mover(0, -1)
    with col_der:
        if st.button("➡️", key="derecha"):
            mover(0, 1)
    col_izq, col_centro, col_der = st.columns([1, 1, 1])
    with col_centro:
        if st.button("⬇️", key="abajo"):
            mover(1, 0)

    # Dibujar el laberinto como grilla de emojis
    tablero = ""
    for f in range(FILAS):
        fila_str = ""
        for c in range(COLUMNAS):
            if [f, c] == st.session_state.maze_pos:
                fila_str += "🐸"
            elif (f, c) == META:
                fila_str += "👵"
            elif (f, c) in PAREDES:
                fila_str += "⬛"
            else:
                fila_str += "⬜"
        tablero += fila_str + "\n\n"
    st.markdown(f"<div style='font-size:32px; line-height:1.4'>{tablero}</div>", unsafe_allow_html=True)

    if st.session_state.puzzle3_ok:
        st.success("¡Llegaste a la casa de la abuela ratona! 🎉")
        img3 = mostrar_imagen_o_subir(IMG_PARRAFO_3, "Sube la imagen final", "img3")
        if img3:
            st.image(img3, width=350)
        st.balloons()
        st.markdown("## 🎊 ¡Fin del cuento! 🎊")
        if st.button("Volver a empezar"):
            st.session_state.pagina = 1
            st.session_state.puzzle1_ok = False
            st.session_state.puzzle2_ok = False
            st.session_state.puzzle3_ok = False
            st.session_state.maze_pos = [0, 0]
            st.rerun()
