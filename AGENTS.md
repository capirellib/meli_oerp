# AGENTS.md — meli_oerp

Módulo Odoo (branch `19.0`) que conecta Odoo con la API v2 de MercadoLibre: publica productos y sincroniza órdenes, envíos, preguntas, reclamos y notificaciones. GPL-3. El nombre de carpeta **debe** seguir siendo `meli_oerp`.

## Reglas de cambio (IMPORTANTE)

- **Nunca editar este módulo directamente.** Todo cambio se hace **heredando** en un módulo custom (extensión/inherit), salvo que el usuario dé una **orden explícita** de tocar el código base. Ante la duda, preguntar antes de escribir.
- Siempre programar con **lógica de Odoo 19 Community** (no Enterprise, no API deprecada de 16/17/18).
- Recurrir a los **skills** disponibles según la tarea (p. ej. `odoo-19`, `odoo-development`, `odoo-upgrade`, `odoo-xml-views-builder`) antes de implementar.

## Antes de trabajar: leer `.roots/`

`.roots/` es la memoria persistente del proyecto (sistema "forest", versionado en git — el `.gitignore` lo permite explícitamente). Es la fuente de verdad de convenciones y del estado. **No** lo trates como carpetas de build.

1. Seguir `.roots/hooks/session-start.md` → leer `.roots/context.md`, `.roots/tasks/todo.md`, `.roots/debug/errors-log.md`.
2. Antes de tocar productos/órdenes/stock, leer `.roots/docs/documentation.md` (diagnósticos y call-paths detallados).
3. Al encontrar/arreglar errores o tomar decisiones, registrar en `.roots/debug/errors-log.md` y `fixes-log.md` / `.roots/design/decisions.md` siguiendo los hooks.
4. El seed que define la estructura está en `.roots/roots_seed.md`; los commits de memoria usan scope `roots(...)` (ver convención de commits).

## Arquitectura

- Modelos propios con prefijo `mercadolibre.*` (`mercadolibre.orders`, `mercadolibre.shipment`, `mercadolibre.posting`, ...). Modelos Odoo extendidos (`product.product`, `product.template`, `sale.order`, `res.company`, `res.partner`, `stock.move`, ...) con campos prefijados `meli_`.
- Monolitos grandes: `models/product.py` (~5600 líneas), `models/orders.py` (~5400), `models/shipment.py` (~2050). Los números de línea citados en `.roots/docs/` varían por rama (16/17/18/19).
- SDK interno vendored en `melisdk/meli.py` (lee `melisdk/config.ini`); en producción el acceso real va por la instancia `meli` de `odoo_connector_api` (`git+https://github.com/ctmil/python-sdk-2025.git`).
- Módulos compañeros que NO están en este repo: `meli_oerp_stock`, `meli_oerp_multiple`, `meli_oerp_accounting`.
- **Gotcha crítico:** con `meli_oerp_multiple` instalado (casi todos los clientes), varios métodos base quedan override — p. ej. `product_meli_get_product` es `meli_oerp_multiple/models/product.py:1234`, y lee flags de la **cuenta** (`account.configuration.*`), no de la compañía. Antes de "arreglar" un método base, verificar si el cliente corre un override.

## Convenciones de negocio (patrones)

- Descuentos de cupón: siempre vía `line.discount` (porcentaje proporcional). **Nunca** restar del `unit_price`. Los cupones salen de `charges_details` (type=coupon), no de `order.coupon` (`.roots/skills/patterns.md` PAT-001/002).
- `mail.thread` en `orders` y `shipment` para chatter. Carrier mapping (`meli_oerp.carrier.mapping`) evita transportistas duplicados.
- Stock: productos con `meli_shipping_logistic_type` conteniendo `'fulfillment'` se saltean en ambos crons de stock (ML no permite tocar stock fulfillment por API). `meli_update_boms()` resetea `meli_stock_update=NULL` para priorizar; `meli_stock_diagnostic()` es red de seguridad anti-drift.
- No pegarle a la API de ML en campos computados que corren en el form load (p. ej. `get_connector_state` → `get_new_instance()`); empeora con rate-limit (ver `.roots/docs/troubleshooting-proxy-429-502.md`).

## Ops / entorno

- Requiere HTTPS (443). Redirect URI `https://<host>/meli_login`. Credenciales en la ficha de compañía (pestaña MercadoLibre).
- No hay tests, CI ni pre-commit en el repo. La verificación es vía instancia Odoo / `odoo shell`.
- ML rate-limita (429). El proxy de rescate es `res.company.mercadolibre_http_proxy`. Un 403 PolicyAgent en petición **sin** token desde IP de datacenter es normal, no es bloqueo. Con proxy, el token viaja en la query string y queda en logs nginx en claro.
- Costo de API por producto al importar: ~8-15 GETs (una llamada `/pictures/{id}` por imagen); los bulks requieren pacing y crones pausados (ver `documentation.md`).

## Commits

Conventional commits con scope y versión en el asunto, mezclando ES/EN:
- `fix(meli_oerp/19.0): ... (19.0.26.90)`, `fix(stock): ... (26.88)`, `feat(meli): ...`, `docs(roots): ...`, `roots(meli_oerp): ...`.
- Bump de versión en `__manifest__.py` (`version: 19.0.26.90`) por cada fix; versiones 16/17/18/19 avanzan en paralelo y los fixes suelen portarse entre ramas.
