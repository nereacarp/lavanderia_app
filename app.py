import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# ========================
# Idioma / Language selector (top-right)
# ========================
if "lang" not in st.session_state:
    st.session_state["lang"] = "ES"

# Top bar with language toggle on the right
_top_left, _top_right = st.columns([1, 0.35])
with _top_right:
    lang = st.radio("", ["ES", "EN"], index=(0 if st.session_state["lang"]=="ES" else 1), horizontal=True)
    st.session_state["lang"] = lang

def tr(es_text: str, en_text: str) -> str:
    return es_text if st.session_state.get("lang", "ES") == "ES" else en_text

archivo_reservas = "reservas.csv"

# Cargar reservas existentes
try:
    reservas = pd.read_csv(archivo_reservas)
except FileNotFoundError:
    reservas = pd.DataFrame(columns=["habitacion","fecha","franja","maquina"])
    reservas.to_csv(archivo_reservas, index=False)
except pd.errors.EmptyDataError:
    reservas = pd.DataFrame(columns=["habitacion","fecha","franja","maquina"])
    reservas.to_csv(archivo_reservas, index=False)

# Asegurar columna 'maquina' exista para compatibilidad hacia atrás
if "maquina" not in reservas.columns:
    reservas["maquina"] = 1
    reservas.to_csv(archivo_reservas, index=False)

st.title(tr("Reserva Lavandería", "Laundry Booking"))

# ========================
# Normas / Información
# ========================
st.subheader(tr("Normas", "Rules"))
st.markdown(tr(
    "- Cada habitación puede reservar **solo 1 franja (2 lavadoras)** por semana.  \n- Excepción: en la semana actual, si aún quedan huecos libres, se puede reservar una franja extra de las que quedan libres.  \n- La franja de **00:00 a 08:00** está libre y **no requiere reserva**.",
    "- Each room can book **only 1 time slot (max 2 washers)** per week.  \n- Exception: in the current week, if there are free slots left, one extra slot from the remaining free ones can be booked.  \n- The **00:00 to 08:00** time range is free to use and **does not require booking**."
))

# ========================
# Utilidades de semana
# ========================
Hoy = datetime.today().date()
# Lunes de esta semana (isoweekday: lunes=1)
start_semana1 = Hoy - timedelta(days=Hoy.isoweekday() - 1)
start_semana2 = start_semana1 + timedelta(days=7)
semana1 = [start_semana1 + timedelta(days=i) for i in range(7)]
semana2 = [start_semana2 + timedelta(days=i) for i in range(7)]
fechas_disponibles = semana1 + semana2

# ========================
# Formulario de reserva
# ========================
with st.form("reserva_form"):
    habitacion = st.text_input(tr("Número de habitación", "Room number"))
    fecha = st.selectbox(tr("Elige fecha", "Choose date"), fechas_disponibles)
    franjas = ["08:00 - 12:00","12:00 - 16:00","16:00 - 20:00","20:00 - 00:00"]
    franja = st.selectbox(tr("Elige franja", "Choose time slot"), franjas)
    maquina = st.radio(tr("Lavadora", "Washer"), [1, 2, 3], horizontal=True)
    submit = st.form_submit_button(tr("Reservar", "Book"))

if submit:
    # Semana objetivo vs actual
    semana_objetivo = fecha.isocalendar()[1]
    semana_actual = Hoy.isocalendar()[1]

    # Subconjunto de reservas de la misma habitación y semana
    reservas["_sem"] = pd.to_datetime(reservas["fecha"]).dt.isocalendar().week
    mismasemana = reservas[(reservas["habitacion"].astype(str)==str(habitacion)) & (reservas["_sem"]==semana_objetivo)]

    # Contar reservas totales (cada lavadora cuenta 1) ya hechas por la habitación en esa semana
    num_reservas_semana = len(mismasemana)

    # Límite semanal de reservas: 2 si es semana actual, si no 1
    max_reservas_semana = 2 if semana_objetivo == semana_actual else 1

    # ¿Hay hueco en la franja seleccionada? (menos de 3 máquinas ocupadas)
    cupo = reservas[(reservas["fecha"]==str(fecha)) & (reservas["franja"]==franja)]
    hay_hueco_en_franja = len(cupo) < 3

    # Validación de límite semanal por número de reservas
    if num_reservas_semana >= max_reservas_semana:
        if semana_objetivo == semana_actual:
            st.warning(tr("Has alcanzado las 2 reservas semanales para esta semana.", "You have reached 2 weekly bookings for this week."))
        else:
            st.warning(tr("Has alcanzado la 1 reserva semanal para la próxima semana.", "You have reached 1 weekly booking for next week."))
    else:
        # Bloquear múltiples lavadoras para la misma habitación en la misma fecha+franja según semana
        misma_franja_habitacion = reservas[
            (reservas["habitacion"].astype(str)==str(habitacion)) &
            (reservas["fecha"]==str(fecha)) &
            (reservas["franja"]==franja)
        ]
        limite_lavadoras_misma_franja = 2 if semana_objetivo == semana_actual else 1
        if len(misma_franja_habitacion) >= limite_lavadoras_misma_franja:
            if semana_objetivo == semana_actual:
                st.warning(tr("Ya tienes 2 lavadoras en esta franja.", "You already have 2 washers in this slot."))
            else:
                st.warning(tr("En la semana siguiente solo puedes 1 lavadora por franja.", "Next week you can only book 1 washer per slot."))
        else:
            # Validar que la lavadora seleccionada esté libre en esa fecha y franja
            ocupado_maquina = reservas[
                (reservas["fecha"]==str(fecha)) &
                (reservas["franja"]==franja) &
                (reservas["maquina"]==int(maquina))
            ]
            if len(ocupado_maquina) > 0:
                st.warning(tr("Esa lavadora ya está reservada en esa franja.", "That washer is already booked for this slot."))
            elif not hay_hueco_en_franja:
                st.warning(tr("Esta franja ya está completa.", "This slot is already full."))
            else:
                nuevas = pd.DataFrame([[habitacion,str(fecha),franja,int(maquina)]], columns=["habitacion","fecha","franja","maquina"])
                reservas = pd.concat([reservas.drop(columns=["_sem"], errors="ignore"), nuevas], ignore_index=True)
                reservas.to_csv(archivo_reservas,index=False)
                st.success(tr(
                    f"Turno reservado para {fecha} {franja} (Lavadora {maquina}) ✔️",
                    f"Booking confirmed for {fecha} {franja} (Washer {maquina}) ✔️"
                ))

# ========================
# Modo administrador
# ========================
st.subheader(tr("Modo Administrador", "Admin Mode"))

admin_pass = st.text_input(tr("Contraseña de administrador", "Admin password"), type="password")
if admin_pass == "1503004505455":   
    st.success(tr("Acceso de administrador concedido ✅", "Admin access granted ✅"))

    with st.form("borrar_form"):
        habitacion_borrar = st.text_input(tr("Habitación a borrar", "Room to delete"))
        fecha_borrar = st.date_input(tr("Fecha a borrar", "Date to delete"))
        franja_borrar = st.selectbox(tr("Franja a borrar", "Time slot to delete"), franjas)
        maquina_borrar = st.selectbox(tr("Lavadora a borrar", "Washer to delete"), [1,2,3])
        borrar_submit = st.form_submit_button(tr("Borrar reserva", "Delete booking"))
        
        if borrar_submit:
            fechas_reservas_date = pd.to_datetime(reservas["fecha"]).dt.date
            coincide = (
                reservas["habitacion"].astype(str) == str(habitacion_borrar)
            ) & (
                fechas_reservas_date == fecha_borrar
            ) & (
                reservas["franja"] == franja_borrar
            ) & (
                reservas["maquina"] == int(maquina_borrar)
            )

            mask_mantener = ~coincide
            nuevas_reservas = reservas[mask_mantener]
            if len(nuevas_reservas) == len(reservas):
                st.warning(tr("No se encontró esa reserva.", "Reservation not found."))
            else:
                reservas = nuevas_reservas
                reservas.to_csv(archivo_reservas,index=False)
                st.success(tr(
                    f"Reserva de habitación {habitacion_borrar} eliminada ✅",
                    f"Room {habitacion_borrar} reservation deleted ✅"
                ))
else:
    if admin_pass:
        st.error(tr("Contraseña incorrecta ❌", "Incorrect password ❌"))

# ========================
# Tablas semanales lunes-domingo (2 semanas)
# ========================
franjas = ["08:00 - 12:00","12:00 - 16:00","16:00 - 20:00","20:00 - 00:00"]

def render_semana(fechas_semana, titulo_es, titulo_en):
    dias_nombres_es = ["Lun","Mar","Mié","Jue","Vie","Sáb","Dom"]
    dias_nombres_en = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
    dias_nombres = dias_nombres_es if st.session_state["lang"] == "ES" else dias_nombres_en
    dias_labels = [f"{dias_nombres[i]} {fechas_semana[i].day:02d}" for i in range(7)]
    st.subheader(tr(titulo_es, titulo_en))

    # Construir matriz: filas=franjas (índice), columnas=días
    filas = []
    for fr in franjas:
        fila = {}
        for idx, f in enumerate(fechas_semana):
            cupo = reservas[(reservas["fecha"]==str(f)) & (reservas["franja"]==fr)]
            por_maquina = {}
            for m in [1,2,3]:
                res_m = cupo[cupo["maquina"]==m]
                if len(res_m) > 0:
                    por_maquina[m] = str(res_m.iloc[0]["habitacion"])  # una por máquina
                else:
                    por_maquina[m] = tr("Libre", "Free")
            # Forzar multilínea con HTML <br>
            fila[dias_labels[idx]] = "<br>".join([por_maquina[1], por_maquina[2], por_maquina[3]])
        filas.append(fila)

    df = pd.DataFrame(filas, columns=dias_labels)
    df.index = franjas
    df.index.name = ""
    html = df.to_html(escape=False, index=True)
    st.markdown(html, unsafe_allow_html=True)

render_semana(semana1, "Semana actual (L-D)", "Current week (Mon-Sun)")
render_semana(semana2, "Semana siguiente (L-D)", "Next week (Mon-Sun)")
