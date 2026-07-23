# Meta Ads MCP remoto (Claude.ai + ChatGPT web) — Narkan

Conector web de **solo lectura** para usar Meta Ads desde Claude.ai o ChatGPT.
Sin login: el acceso es una URL con un secreto (`https://mcp.plasa.cl/<MCP_SECRET>/mcp`).

## Variables de entorno (en Dokploy, nunca en git)
Ver `.env.example`: `META_ACCESS_TOKEN`, `MCP_SECRET`.

## Local
```bash
cd remote
uv sync
env $(grep -v '^#' .env | xargs) uv run uvicorn app.server:app --host 0.0.0.0 --port 8000
# /health -> 200 ; /<MCP_SECRET>/mcp -> endpoint MCP ; otras rutas -> 404
```

## Despliegue (resumen — ver [DEPLOY.md](DEPLOY.md))

1. DNS `A: mcp.plasa.cl -> 173.249.49.22` (único paso manual).
2. Servicio en Dokploy (build path `remote/`) con `META_ACCESS_TOKEN` y `MCP_SECRET`, dominio `mcp.plasa.cl` con HTTPS.

## Uso en Claude.ai

Claude.ai -> Ajustes -> Conectores -> Añadir conector -> pegar la URL completa
`https://mcp.plasa.cl/<MCP_SECRET>/mcp`.

## Uso en ChatGPT web

1. Activa Developer mode en ChatGPT.
2. Crea una app/conector MCP personalizado.
3. Pega la misma URL completa y selecciona **sin autenticación**.
4. Verifica que el escaneo muestre las 11 tools y habilita la app en un chat nuevo.

ChatGPT admite MCP remoto por Streamable HTTP. Este servicio declara formalmente
las 11 tools como `readOnly` para que el cliente las trate como consultas. La
disponibilidad exacta de Developer mode depende del plan y las políticas del
workspace; consulta la [guía oficial de OpenAI](https://developers.openai.com/apps-sdk/deploy/connect-chatgpt).

> La URL secreta es una credencial compartida. Para acceso individual, auditoría
> por persona o una distribución pública se debe migrar a OAuth 2.1.

Solo lectura: imposible crear/editar/gastar. Basado en el reporting de konquest (MIT).
