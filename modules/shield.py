import streamlit as st
import streamlit.components.v1 as components
import base64
import os

def obtener_logo_base64():
    """Convierte assets/logo.png a Base64 para integrarlo en toda la interfaz sin perder calidad."""
    ruta_logo = os.path.join("assets", "logo.png")
    if os.path.exists(ruta_logo):
        with open(ruta_logo, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode("utf-8")
    return None

def aplicar_blindaje_y_estilos():
    """Oculta iconos de GitHub, configura metadatos, manifiesto y el tema DiSys."""
    
    st.markdown("""
        <head>
            <meta property="og:title" content="DiSys CuentaClara | Gestión de Créditos">
            <meta property="og:description" content="Plataforma profesional para la administración de créditos y cobranzas en bodegas.">
            <meta property="og:image" content="https://raw.githubusercontent.com/TU_USUARIO/disys-cuentaclara/main/assets/logo.png">
            <meta property="og:type" content="website">
            <link rel="manifest" href="https://raw.githubusercontent.com/Deibysapp/disys-cuentaclara/main/manifest.json">
            <link rel="icon" type="image/png" href="https://raw.githubusercontent.com/TU_USUARIO/disys-cuentaclara/main/assets/logo.png">
            <link rel="apple-touch-icon" href="https://raw.githubusercontent.com/TU_USUARIO/disys-cuentaclara/main/assets/logo.png">
        </head>
    """, unsafe_allow_html=True)

    st.markdown("""
        <style>
        /* OCULTAMIENTO TOTAL DE ELEMENTOS STREAMLIT */
            #MainMenu {visibility: hidden !important; display: none !important;}
            header {visibility: hidden !important; display: none !important;}
            footer {visibility: hidden !important; display: none !important;}
            .stDeployButton {display: none !important;}
            [data-testid="stToolbar"] {visibility: hidden !important; display: none !important;}
            [data-testid="stDecoration"] {visibility: hidden !important; display: none !important;}
            [data-testid="stStatusWidget"] {visibility: hidden !important; display: none !important;}
            [data-testid="manage-app-button"] {display: none !important;}
            [data-testid="stHeader"] {display: none !important;}
            .viewerBadge_container__1QSob {display: none !important; visibility: hidden !important;}
            .styles_viewerBadge__1yB5_ {display: none !important; visibility: hidden !important;}
            
            /* Ocultar botones flotantes inferiores derechos */
            div[class*="viewerBadge"] {display: none !important; visibility: hidden !important;}
            iframe[title="streamlitApp"] {display: block;}
            
            .block-container {
                padding-top: 0.8rem !important;
                padding-bottom: 2.5rem !important;
                max-width: 1150px !important;
            }
       
            /* ==========================================================
               1. OCULTAMIENTO TOTAL DE ICONOS GITHUB Y BARRAS STREAMLIT
               ========================================================== */
            #MainMenu {visibility: hidden !important; display: none !important;}
            header {visibility: hidden !important; display: none !important;}
            footer {visibility: hidden !important; display: none !important;}
            .stDeployButton {display: none !important;}
            [data-testid="stToolbar"] {visibility: hidden !important; display: none !important;}
            [data-testid="stDecoration"] {visibility: hidden !important; display: none !important;}
            [data-testid="stStatusWidget"] {visibility: hidden !important; display: none !important;}
            [data-testid="manage-app-button"] {display: none !important;}
            [data-testid="stHeader"] {display: hidden !important; display: none !important;}
            .viewerBadge_container__1QSob {display: none !important;}
            .styles_viewerBadge__1yB5_ {display: none !important;}
            a[href*="github.com"] {display: none !important; visibility: hidden !important;}

            .block-container {
                padding-top: 0.8rem !important;
                padding-bottom: 2.5rem !important;
                max-width: 1150px !important;
            }

            /* ==========================================================
               2. IDENTIDAD VISUAL CORPORATIVA DISYS CUENTACLARA
               ========================================================== */
            :root {
                --disys-navy: #0A2239;
                --disys-orange: #F9690E;
                --disys-green: #10B981;
                --disys-amber: #F59E0B;
                --disys-red: #EF4444;
            }

            .disys-card {
                background: #FFFFFF;
                border-radius: 12px;
                padding: 18px 20px;
                border: 1px solid #E2E8F0;
                border-left: 5px solid #0A2239;
                box-shadow: 0 3px 10px rgba(0, 0, 0, 0.04);
                margin-bottom: 14px;
            }

            .disys-card-orange {
                border-left: 5px solid #F9690E !important;
            }

            div.stButton > button[kind="primary"] {
                background-color: #F9690E !important;
                color: #FFFFFF !important;
                border: none !important;
                border-radius: 10px !important;
                font-weight: 700 !important;
                padding: 0.55rem 1.2rem !important;
                box-shadow: 0 4px 10px rgba(249, 105, 14, 0.25) !important;
            }
            div.stButton > button[kind="primary"]:hover {
                background-color: #D95300 !important;
            }
        </style>
    """, unsafe_allow_html=True)

    components.html("""
        <script>
            const parentDoc = window.parent.document;
            parentDoc.addEventListener('contextmenu', function(e) {
                e.preventDefault();
            });
            parentDoc.addEventListener('keydown', function(e) {
                if (e.keyCode === 123 || 
                   (e.ctrlKey && e.shiftKey && (e.keyCode === 73 || e.keyCode === 74 || e.keyCode === 67)) || 
                   (e.ctrlKey && (e.keyCode === 85 || e.keyCode === 83))) {
                    e.preventDefault();
                    return false;
                }
            });
        </script>
    """, height=0, width=0)

def mostrar_cabecera_corporativa(titulo_vista, subtitulo_bodega="", estado_sincronizado=True):
    logo_b64 = obtener_logo_base64()
    if logo_b64:
        img_tag = f'<img src="data:image/png;base64,{logo_b64}" class="disys-topbar-logo" alt="DiSys Logo">'
    else:
        img_tag = '<span style="font-size:24px; font-weight:900; color:#FFFFFF;">DiSys <span style="color:#F9690E;">CuentaClara</span></span>'

    if estado_sincronizado:
        badge_html = '<span style="background-color: #D1FAE5; color: #065F46; border: 1px solid #10B981; padding: 6px 14px; border-radius: 20px; font-size: 12.5px; font-weight: 700; display: inline-block;">✅ Sincronizado</span>'
    else:
        badge_html = '<span style="background-color: #FEF3C7; color: #92400E; border: 1px solid #F59E0B; padding: 6px 14px; border-radius: 20px; font-size: 12.5px; font-weight: 700; display: inline-block;">⏳ Pendiente</span>'

    st.markdown(f"""
        <div style="background: linear-gradient(135deg, #0A2239 0%, #13385C 100%); color: #FFFFFF; padding: 14px 22px; border-radius: 14px; border-bottom: 4px solid #F9690E; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 6px 16px rgba(10, 34, 57, 0.15); margin-bottom: 16px; flex-wrap: wrap; gap: 10px;">
            <div style="display: flex; align-items: center; gap: 14px;">
                {img_tag}
                <div>
                    <div style="font-size: 18px; font-weight: 800; color: #FFFFFF; line-height: 1.2;">
                        DiSys CuentaClara
                    </div>
                    <div style="font-size: 13px; color: #F9690E; font-weight: 600;">
                        {titulo_vista} {f"• {subtitulo_bodega}" if subtitulo_bodega else ""}
                    </div>
                </div>
            </div>
            <div>
                {badge_html}
            </div>
        </div>
    """, unsafe_allow_html=True)