# Mapa del proyecto Meta Ads MCP

## Dos runtimes independientes

| Superficie | Entrada | Transporte | Dependencias | Credencial |
|---|---|---|---|---|
| Claude Code local | `meta_ads_mcp/__main__.py` | `stdio` | `pyproject.toml` | `.env` local |
| Claude.ai / ChatGPT web | `remote/app/server.py` | Streamable HTTP | `remote/pyproject.toml` | entorno de Dokploy |

El runtime remoto no copia el paquete local dentro de su imagen Docker. Esta
separación impide que las operaciones de escritura presentes en el código
vendorizado local lleguen al servicio web.

## Flujo remoto

```text
Cliente MCP
  -> HTTPS /<MCP_SECRET>/mcp
  -> FastMCP stateless
  -> una de 11 tools read-only
  -> MetaClient (solo GET)
  -> graph.facebook.com/v25.0
```

`GET /health` comprueba vida del proceso. No valida que el token de Meta siga
vigente.

## Componentes

- `remote/app/server.py`: superficie ASGI, registro de tools, CORS y health.
- `remote/app/security.py`: valida y construye la ruta secreta.
- `remote/app/tools.py`: 11 consultas de cuentas, jerarquía e insights.
- `remote/app/meta.py`: cliente HTTP GET-only para Meta Graph.
- `remote/Dockerfile`: imagen de producción y healthcheck.
- `remote/tests/`: contrato de seguridad, transporte y resultados.
- `meta_ads_mcp/server.py`: allowlist del servidor local.
- `tests/test_readonly_allowlist.py`: impide registrar tools locales de escritura.

## Límites conocidos

- La URL secreta es compartida; no hay identidad ni auditoría por persona.
- Las colecciones remotas usan límites de una página y todavía no paginan.
- El healthcheck no comprueba el token de Meta.
- Las tools remotas conservan los nombres del runtime local, pero exponen
  respuestas y opciones más simples.
- `mcp.plasa.cl` requiere un registro DNS A hacia el VPS.

## Evolución recomendada

1. Mantener un único contrato remoto estándar para Claude y ChatGPT.
2. Añadir paginación y pruebas de integración con datos grandes.
3. Incorporar readiness que valide configuración sin filtrar secretos.
4. Migrar a OAuth 2.1 si se necesita acceso individual o distribución pública.
