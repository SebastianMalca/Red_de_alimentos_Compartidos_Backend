# Backend - Red de Alimentos Compartidos (API REST)

Este es el servidor central de nuestra aplicación, construido con **Python (FastAPI)** y una base de datos relacional **SQLite** (gestionada con SQLAlchemy).

## Requisitos Previos
1. Tener instalado **Python 3.12 o 3.13** en tu computadora.
2. Un editor de código (Recomendado: VS Code).

## Instrucciones de Configuración Local

**Paso 1: Clonar el repositorio y entrar a la carpeta**
\`\`\`bash
git clone <URL_DE_TU_REPOSITORIO_BACKEND>
cd RedAlimentos-Backend
\`\`\`

**Paso 2: Crear y activar el Entorno Virtual**
Para no mezclar librerías, creamos un entorno aislado. Ejecuta en tu terminal:
* En Windows:
  \`\`\`bash
  python -m venv venv
  .\venv\Scripts\activate
  \`\`\`
* En Mac/Linux:
  \`\`\`bash
  python3 -m venv venv
  source venv/bin/activate
  \`\`\`
*(Sabrás que funcionó si ves un `(venv)` al inicio de tu terminal).*

**Paso 3: Instalar las dependencias**
\`\`\`bash
pip install -r requirements.txt
\`\`\`

**Paso 4: Iniciar el servidor (Accesible en Red Local)**
Para que la app móvil pueda conectarse por Wi-Fi, inicia el servidor abriendo los puertos:
\`\`\`bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
\`\`\`

**Paso 5: Probar la API**
Abre tu navegador y entra a: **http://127.0.0.1:8000/docs**
Allí verás la interfaz interactiva (Swagger) con todos nuestros endpoints listos para probar. Usa el endpoint `/crear-datos-prueba` para llenar tu base de datos local.