import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

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

st.title("Reserva Lavandería")

# ========================
# Normas / Información
# ========================
st.subheader("Normas")
st.markdown("- Solo se puede reservar 1 franja por habitación a la semana (salvo semana actual si quedan huecos).\n- De 00:00 a 08:00 se puede usar sin necesidad de reservar.")

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
    habitacion = st.text_input("Número de habitación")
    fecha = st.selectbox("Elige fecha", fechas_disponibles)
    franjas = ["08:00 12:00","12:00 16:00","16:00 20:00","20:00 00:00"]
    franja = st.selectbox("Elige franja", franjas)
    maquina = st.radio("Lavadora", [1, 2, 3], horizontal=True)
    submit = st.form_submit_button("Reservar")

if submit:
    # Validar máximo 1 reserva por semana por habitación con excepción: semana actual si hay huecos
    semana_objetivo = fecha.isocalendar()[1]
    semana_actual = Hoy.isocalendar()[1]
    reservas_semana = pd.to_datetime(reservas["fecha"]).dt.isocalendar().week
    habitaciones_str = reservas["habitacion"].astype(str)
    ya_tiene_semana = ((habitaciones_str==str(habitacion)) & (reservas_semana==semana_objetivo)).any()

    # ¿Hay hueco en la franja seleccionada? (menos de 3 máquinas ocupadas)
    cupo = reservas[(reservas["fecha"]==str(fecha)) & (reservas["franja"]==franja)]
    hay_hueco_en_franja = len(cupo) < 3

    if ya_tiene_semana and not (semana_objetivo == semana_actual and hay_hueco_en_franja):
        st.warning("Ya has reservado lavadora esta semana")
    else:
        # Validar que la lavadora seleccionada esté libre en esa fecha y franja
        ocupado_maquina = reservas[
            (reservas["fecha"]==str(fecha)) &
            (reservas["franja"]==franja) &
            (reservas["maquina"]==int(maquina))
        ]
        if len(ocupado_maquina) > 0:
            st.warning("Esa lavadora ya está reservada en esa franja.")
        else:
            nuevas = pd.DataFrame([[habitacion,str(fecha),franja,int(maquina)]], columns=["habitacion","fecha","franja","maquina"])
            reservas = pd.concat([reservas,nuevas], ignore_index=True)
            reservas.to_csv(archivo_reservas,index=False)
            st.success(f"Turno reservado para {fecha} {franja} (Lavadora {maquina}) ✔️")

# ========================
# Modo administrador
# ========================
st.subheader("Modo Administradora")

admin_pass = st.text_input("Contraseña de administradora", type="password")
if admin_pass == "1503004505455":   
    st.success("Acceso de administradora concedido ✅")

    with st.form("borrar_form"):
        habitacion_borrar = st.text_input("Habitación a borrar")
        fecha_borrar = st.date_input("Fecha a borrar")
        franja_borrar = st.selectbox("Franja a borrar", franjas)
        maquina_borrar = st.selectbox("Lavadora a borrar", [1,2,3])
        borrar_submit = st.form_submit_button("Borrar reserva")
        
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
                st.warning("No se encontró esa reserva.")
            else:
                reservas = nuevas_reservas
                reservas.to_csv(archivo_reservas,index=False)
                st.success(f"Reserva de habitación {habitacion_borrar} eliminada ✅")
else:
    if admin_pass:
        st.error("Contraseña incorrecta ❌")

# ========================
# Tablas semanales lunes-domingo (2 semanas)
# ========================
franjas = ["08:00 12:00","12:00 16:00","16:00 20:00","20:00 00:00"]

def render_semana(fechas_semana, titulo):
    dias_nombres = ["Lun","Mar","Mié","Jue","Vie","Sáb","Dom"]
    dias_labels = [f"{dias_nombres[i]} {fechas_semana[i].day:02d}" for i in range(7)]
    st.subheader(titulo)
    filas = []
    for fr in franjas:
        fila = {"Franja": fr}
        for idx, f in enumerate(fechas_semana):
            cupo = reservas[(reservas["fecha"]==str(f)) & (reservas["franja"]==fr)]
            por_maquina = {}
            for m in [1,2,3]:
                res_m = cupo[cupo["maquina"]==m]
                if len(res_m) > 0:
                    por_maquina[m] = str(res_m.iloc[0]["habitacion"])  # una por máquina
                else:
                    por_maquina[m] = "Libre"
            # Forzar multilínea con HTML <br>
            fila[dias_labels[idx]] = "<br>".join([por_maquina[1], por_maquina[2], por_maquina[3]])
        filas.append(fila)
    df = pd.DataFrame(filas, columns=["Franja"] + dias_labels)
    html = df.to_html(escape=False, index=False)
    st.markdown(html, unsafe_allow_html=True)

render_semana(semana1, "Semana actual (L-D)")
render_semana(semana2, "Semana siguiente (L-D)")
