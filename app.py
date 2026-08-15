from datetime import datetime
from email.message import EmailMessage
import mimetypes
import os
import smtplib
import textwrap
import urllib.parse

import pandas as pd
import streamlit as st

# ==============================================================================
# LOCAL MESITAS - SISTEMA POS (VERSIÓN CORREGIDA)
# ==============================================================================

st.set_page_config(
    page_title="Local Mesitas - Sistema POS",
    page_icon="🛏️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Constantes de credenciales
CLAVE_ACCESO = "1234"
CLAVE_ADMIN = "1999"  # <--- Contraseña actualizada aquí

NUMERO_1 = "573100000000"
NUMERO_2 = "573200000000"

FILE_INV = "inventario.csv"
FILE_VENTAS = "ventas.csv"
CARPETA_FOTOS = "fotos_productos"
