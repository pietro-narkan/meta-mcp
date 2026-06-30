# Meta Ads MCP remoto (claude.ai) — Narkan

Conector web de **solo lectura** para usar Meta Ads desde **claude.ai en el navegador**.
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

## Despliegue (resumen — ver DEPLOY.md)
1. DNS `A: mcp.plasa.cl -> 173.249.49.22` (único paso manual).
2. Servicio en Dokploy (build path `remote/`) con `META_ACCESS_TOKEN` y `MCP_SECRET`, dominio `mcp.plasa.cl` con HTTPS.

## Uso (trabajador)
claude.ai -> Ajustes -> Conectores -> Añadir conector -> pegar
`https://mcp.plasa.cl/<MCP_SECRET>/mcp` -> preguntar. Sin login, sin instalar nada.

Solo lectura: imposible crear/editar/gastar. Basado en el reporting de konquest (MIT).
