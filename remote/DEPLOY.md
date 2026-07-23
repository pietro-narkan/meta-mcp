# Despliegue del MCP remoto en Dokploy

## Arquitectura de producción

```text
Claude.ai / ChatGPT web
        |
        | HTTPS + MCP Streamable HTTP
        v
Traefik (Dokploy) -> contenedor :8000 -> Meta Graph API v25.0
```

El endpoint MCP es `/<MCP_SECRET>/mcp`. La ruta `/health` es pública y sirve
exclusivamente para comprobar que el proceso responde.

## Configuración de Dokploy

- Repositorio: `pietro-narkan/meta-mcp`
- Rama: `main`
- Build type: Dockerfile
- Docker context: `remote`
- Dockerfile: `remote/Dockerfile`
- Puerto del dominio: `8000`
- HTTPS: habilitado con Let's Encrypt
- Variables secretas:
  - `META_ACCESS_TOKEN`: token de System User con `ads_read`
  - `MCP_SECRET`: secreto aleatorio URL-safe de al menos 32 caracteres

Nunca guardes valores reales en Git ni los imprimas en logs.

## DNS

Crear el registro:

```text
Tipo: A
Host: mcp
Valor: 173.249.49.22
```

Hasta que el registro propague, el dominio alternativo configurado en Dokploy es
`metaconn.173.249.49.22.sslip.io`.

## Verificación

1. `GET https://mcp.plasa.cl/health` debe devolver `{"status":"ok"}`.
2. `POST /mcp` sin el secreto debe devolver `404`.
3. Un handshake MCP contra `/<MCP_SECRET>/mcp` debe completar `initialize`.
4. `tools/list` debe mostrar exactamente 11 tools, todas con
   `readOnlyHint=true` y `destructiveHint=false`.
5. Probar al menos `check_token_status` y `get_ad_accounts`.

Ejecutar las pruebas locales antes del deploy:

```bash
cd remote
uv sync --frozen
uv run pytest -q
```

## Conexión de clientes

### Claude.ai

Añadir un conector personalizado con la URL completa
`https://mcp.plasa.cl/<MCP_SECRET>/mcp`.

### ChatGPT web

Activar Developer mode, crear una app MCP personalizada, usar la misma URL
completa y elegir el modo sin autenticación. Tras el escaneo deben aparecer las
11 tools. La guía vigente está en:
https://developers.openai.com/apps-sdk/deploy/connect-chatgpt

## Seguridad y rotación

- La URL completa equivale a una contraseña compartida.
- Uvicorn se ejecuta sin access log para no registrar `MCP_SECRET`.
- Verificar por separado si Traefik/Dokploy tiene access logs globales activos.
- Para revocar acceso, cambiar `MCP_SECRET`, redesplegar y volver a conectar los
  clientes.
- Para identidades individuales o publicación pública, reemplazar la ruta
  secreta por OAuth 2.1 conforme a la especificación de autorización MCP.
