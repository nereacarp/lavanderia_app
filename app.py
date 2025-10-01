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
# Formulario de reserva
# ========================
with st.form("reserva_form"):
    habitacion = st.text_input("Número de habitación")
    hoy = datetime.today().date()
    fechas_disponibles = [hoy + timedelta(days=i) for i in range(14)]
    fecha = st.selectbox("Elige fecha", fechas_disponibles)
    franjas = ["08:00-12:00","12:00-16:00","16:00-20:00","20:00-00:00"]
    franja = st.selectbox("Elige franja", franjas)
    maquina = st.radio("Lavadora", [1, 2, 3], horizontal=True)
    submit = st.form_submit_button("Reservar")

if submit:
    # Validar máximo 1 reserva por semana por habitación
    semana = fecha.isocalendar()[1]
    reservas_semana = pd.to_datetime(reservas["fecha"]).dt.isocalendar().week
    habitaciones_str = reservas["habitacion"].astype(str)
    if ((habitaciones_str==str(habitacion)) & (reservas_semana==semana)).any():
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
# Mostrar calendario visual
# ========================
st.subheader("Disponibilidad de los próximos 14 días (3 huecos por franja)")
tabla = []

for f in fechas_disponibles:
    fila = {"Fecha": f}
    for fr in franjas:
        cupo = reservas[(reservas["fecha"]==str(f)) & (reservas["franja"]==fr)]
        # Construir vista por máquina 1..3
        por_maquina = {}
        for m in [1,2,3]:
            res_m = cupo[cupo["maquina"]==m]
            if len(res_m) > 0:
                por_maquina[m] = str(res_m.iloc[0]["habitacion"])  # una por máquina
            else:
                por_maquina[m] = "Libre"
        fila[fr] = " | ".join([por_maquina[1], por_maquina[2], por_maquina[3]])
    tabla.append(fila)

st.table(pd.DataFrame(tabla))
st.caption("Cada franja muestra Lavadora 1 | Lavadora 2 | Lavadora 3. 'Libre' indica hueco disponible.")
