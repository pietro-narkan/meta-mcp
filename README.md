# Meta Ads MCP (solo lectura) — Narkan

Consulta los datos de Meta Ads de las cuentas de la agencia **en lenguaje natural
desde Claude Code, Claude.ai o ChatGPT web**. Es de **solo lectura**: puedes ver campañas, conjuntos de
anuncios, anuncios e insights, pero no se puede crear, editar ni gastar nada.

## Requisitos
- [Claude Code](https://claude.com/claude-code) instalado.
- macOS, Linux o Windows.
- (El script instala `uv` automáticamente si falta.)

## Instalación (1 comando)

**macOS / Linux**
```bash
git clone https://github.com/pietro-narkan/meta-mcp
cd meta-mcp
./setup.sh
```

**Windows (PowerShell)**
```powershell
git clone https://github.com/pietro-narkan/meta-mcp
cd meta-mcp
.\setup.ps1
```

El script instala dependencias, te pide **una vez** el token de solo-lectura
(te lo entrega el admin), genera la configuración local y valida que todo funcione
listando las cuentas a las que tienes acceso.

## Cómo usar
Abre Claude Code dentro de la carpeta `meta-mcp` y pregunta, por ejemplo:
- "¿Qué campañas activas hay en cada cuenta y cuánto gastaron este mes?"
- "Compara el CTR de Bellas Todas vs Spa Infinity en los últimos 30 días."
- "Dame el gasto por cuenta de los últimos 7 días."
- "¿Qué conjuntos de anuncios están pausados en Fiorenza?"

## Claude.ai y ChatGPT web

El servidor remoto vive en [`remote/`](remote/) y usa MCP Streamable HTTP sobre
HTTPS. No instala ni ejecuta código local en el navegador. La arquitectura,
despliegue y pasos de conexión están documentados en
[`remote/README.md`](remote/README.md).

## Seguridad
- **Solo lectura.** El token tiene permiso `ads_read`: imposible gastar, crear o borrar.
- **Tu token nunca entra a git.** Vive solo en tu archivo `.env` local (ignorado por git).
- No compartas tu `.env` ni tu token.

## Para el admin
- **Entregar el token:** comparte el token de solo-lectura por gestor de contraseñas,
  nunca por el repo ni por chat.
- **Rotar el token** (si alguien se va o se filtra): genera un nuevo token del System User
  en el Business Manager (app "plasa", scope `ads_read`), y reparte el nuevo. Cada trabajador
  actualiza la línea `META_ACCESS_TOKEN=` de su `.env` y reinicia Claude Code.

## Créditos
Basado en [konquest-meta-ads-mcp](https://github.com/brandu-mos/konquest-meta-ads-mcp)
(licencia MIT — ver `LICENSE`). Recortado a solo-lectura. Ver `VENDOR.md`.
