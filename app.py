import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

archivo_reservas = "reservas.csv"

# Cargar reservas existentes
try:
    reservas = pd.read_csv(archivo_reservas)
except:
    reservas = pd.DataFrame(columns=["habitacion","fecha","franja"])
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
    submit = st.form_submit_button("Reservar")

if submit:
    # Validar máximo 1 reserva por semana por habitación
    semana = fecha.isocalendar()[1]
    reservas_semana = pd.to_datetime(reservas["fecha"]).dt.isocalendar().week
    habitaciones_str = reservas["habitacion"].astype(str)
    if ((habitaciones_str==str(habitacion)) & (reservas_semana==semana)).any():
        st.warning("Ya has reservado lavadora esta semana")
    else:
        # Validar que haya menos de 3 reservas en esa fecha y franja
        cupo = reservas[(reservas["fecha"]==str(fecha)) & (reservas["franja"]==franja)]
        if len(cupo) >= 3:
            st.warning("Esta franja ya está completa.")
        else:
            nuevas = pd.DataFrame([[habitacion,str(fecha),franja]], columns=["habitacion","fecha","franja"])
            reservas = pd.concat([reservas,nuevas], ignore_index=True)
            reservas.to_csv(archivo_reservas,index=False)
            st.success(f"Turno reservado para {fecha} {franja} ✔️")

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
        borrar_submit = st.form_submit_button("Borrar reserva")
        
        if borrar_submit:
            fechas_reservas_date = pd.to_datetime(reservas["fecha"]).dt.date
            coincide = (
                reservas["habitacion"].astype(str) == str(habitacion_borrar)
            ) & (
                fechas_reservas_date == fecha_borrar
            ) & (
                reservas["franja"] == franja_borrar
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
        ocupacion = [str(x) for x in cupo["habitacion"].tolist()]
        while len(ocupacion) < 3:
            ocupacion.append("Libre")
        fila[fr] = " | ".join(ocupacion)
    tabla.append(fila)

st.table(pd.DataFrame(tabla))
st.caption("Cada franja muestra las 3 máquinas. 'Libre' indica hueco disponible.")
