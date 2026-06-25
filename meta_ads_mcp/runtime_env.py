"""Carga el .env local del trabajador al entorno del proceso."""
import os

from dotenv import load_dotenv


def load_environment() -> None:
    """Carga <cwd>/.env al entorno del proceso.

    No-op si el archivo no existe. No sobrescribe variables ya presentes.
    Se fija al directorio actual para coincidir con cómo Claude Code arranca
    el server (uv corre con CWD = carpeta del repo, donde vive el .env).
    """
    load_dotenv(os.path.join(os.getcwd(), ".env"))
