# Módulo de recibos de servicios

Gestión de luz, agua e internet del edificio. Reemplaza el manejo manual en
`src/database/Recibos servicios.xlsx`.

Alcance: **solo servicios**. La renta no se maneja en este módulo.

## Estado

| Paso | Estado |
|---|---|
| 1. Modelos + migración + importador | Hecho |
| 2. Motor de cálculo (`UtilityBillingService`) | Hecho |
| 3. API REST | Hecho |
| 4. Frontend Angular | Hecho |
| 5. PDF + email + alertas | Hecho |

## Modelo de datos

| Tabla | Contenido |
|---|---|
| `units` | Departamentos (201, 301, 303, 304) |
| `tenants` | Inquilinos, con `people_count` (agua), `water_flat_fee` e `internet_fee` |
| `meters` | Medidores con vigencia `valid_from` / `valid_to` |
| `utility_bills` | Recibo global del edificio por mes y servicio |
| `meter_readings` | Lectura anterior/actual y consumo por medidor y periodo |
| `unit_charges` | Cobro consolidado por unidad y periodo |
| `payments` | Pagos recibidos contra un cargo |

El periodo es siempre `'YYYY-MM'` y se ancla al **inicio** del ciclo de
facturación, no al fin: los ciclos van a mitad de mes (ej. `01/03 - 01/04`) y
anclarlos al fin haría colisionar dos bloques consecutivos en el mismo periodo.

### Medidores con vigencia

`meters.valid_from` / `valid_to` permiten que una unidad cambie de medidor sin
perder historia. El caso real: el **303** consumió por el medidor `301` hasta el
07/05/2026 y por el `303` desde esa fecha. El consumo de ese periodo es la suma
de ambos medidores vigentes (4.7 + 36 = 40.7 KW).

### Tarifas

Del recibo global sale la tarifa que se aplica a cada unidad:

- luz: `unit_price = total_amount / total_units` → S/ por KW
- agua: `unit_price = total_amount / total_units` → S/ por persona

### Faltante de áreas comunes

`recibo_global − suma_cobrada_a_unidades`. Lo asume el propietario, **no** se
reparte entre los departamentos. En el histórico fue S/ 21.00 (marzo) y
S/ 7.08 (abril). El motor de cálculo debe exponerlo, no redistribuirlo.

## Migración

```bash
python flask_commands.py db upgrade
```

Revisión `a1c4e9b27f10`, encadenada a `9d137158c020`. Crea las 7 tablas.

## Importar el histórico del Excel

```bash
python import_recibos_excel.py --dry-run   # muestra sin escribir
python import_recibos_excel.py             # escribe
```

Es idempotente: se puede volver a ejecutar sin duplicar filas.

Carga 4 unidades, 4 inquilinos, 6 medidores, 15 recibos globales, 23 lecturas y
21 cargos.

### Desfase de tarifas en el Excel histórico

Las hojas de departamento referencian filas de `RECIBOS` que **no siempre
corresponden al mes facturado**. Ejemplos verificados:

- `201`, ciclo `01/03 - 01/04` (periodo marzo) → usa `RECIBOS!E6`, que es la
  tarifa de **febrero** (0.9709)
- `304` filas 59 y 82 → ambas apuntan a `RECIBOS!E9`
- `304` fila 11 → tarifa `1.019801` escrita a mano, no sale de ningún recibo

Recalcular con la tarifa correcta cambiaría montos que ya fueron cobrados. Por
eso el importador **preserva el importe histórico**: usa la tarifa que cada
bloque tiene escrita y solo cae a la del recibo global si el bloque no la trae.
Cuando ambas difieren lo deja anotado en `unit_charges.notes` y lo cuenta en
`price_mismatch` (15 bloques en el histórico actual).

Con este criterio los **19 bloques con importe de luz cuadran exacto** contra el
Excel (diferencia 0.0000).

Para los periodos nuevos, el motor de cálculo del paso 2 sí debe usar siempre la
tarifa del recibo global del periodo que corresponde.

## Motor de cálculo

`src/services/UtilityBillingService.py`. Reemplaza las fórmulas del Excel.

### Métodos principales

| Método | Qué hace |
|---|---|
| `save_bill(...)` | Registra el recibo global y calcula su tarifa |
| `get_unit_price(service_type, period)` | Tarifa del periodo; `None` si no está cargado |
| `get_unit_consumption(unit_id, period)` | KW de la unidad sumando **todos** sus medidores |
| `generate_period(period)` | Genera los cobros de todas las unidades y devuelve el cuadre |
| `get_period_summary(period)` | Consolidado del periodo (reemplaza `TOTALESXMES`) |
| `register_payment(...)` / `delete_payment(...)` | Pagos, con recálculo de estado y saldo |
| `get_charge_detail(charge_id)` | Recibo del inquilino, con lecturas y pagos |
| `get_unit_history(unit_id)` | Histórico para comparar |
| `get_consumption_alerts(period)` | Unidades con desvío ≥40% vs. su promedio |

### Reglas

- **Total del cargo** = luz + agua + internet − saldo a favor del periodo anterior
- **Luz** = consumo KW × tarifa del recibo global del periodo
- **Agua** = `people_count` del inquilino vigente × tarifa por persona.
  Si el inquilino tiene `water_flat_fee`, se cobra ese monto fijo en lugar del
  prorrateo y el cargo se guarda con `water_people = 0` y `water_price = 0`.
  El inquilino sigue contando en el total de personas del recibo global, así que
  la tarifa de los demás no cambia: la diferencia la absorbe el propietario.
- **Internet** = `internet_fee` pactado con el inquilino
- Los importes se redondean a 2 decimales con redondeo comercial (`money()`)

### Saldo a favor

Un pago por encima del total genera `credit_balance`, que `generate_period` del
periodo siguiente arrastra y descuenta automáticamente. Ya no se copia a mano.

### Áreas comunes

`get_period_summary` expone `common_area_amount` (luz y agua) y
`common_area_kw`. Es la diferencia entre el recibo global y lo repartido, y la
asume el propietario: se reporta en `totals.owner_absorbed`, **nunca** se
redistribuye entre los departamentos.

En agua ese faltante mezcla dos cosas distintas: el consumo de áreas comunes y
la rebaja de quienes tienen tarifa plana. Por eso el bloque `water` separa
`prorated_billed` (lo que salió del prorrateo) de `flat_billed` (lo cobrado en
tarifas planas).

### Protecciones

- Un cargo con pagos registrados **no se recalcula**: cambiar el monto dejaría
  los pagos descuadrados. `generate_period` lo informa en `skipped`.
- Si falta el recibo global del periodo, genera igual con tarifa 0 y lo avisa
  en `warnings`, en vez de fallar.

## Pruebas

```bash
python test_billing.py
```

46 comprobaciones sobre una SQLite temporal cargada con el Excel real. Cubren
tarifas, el caso del 303 con dos medidores, arrastre de saldo, cuadre de áreas
comunes, pagos, borrado de pagos, protección de cargos pagados y periodos sin
recibo. Estado actual: **46 OK, 0 fallas**.

## API REST

Todos los endpoints requieren token de administrador
(`Authorization: Bearer <token>`) y responden `{message, success, data}`.

### Maestros — `/api/utilities`

| Método | Ruta | Qué hace |
|---|---|---|
| GET/POST | `/units` | Listar / crear departamentos |
| GET/PUT/DELETE | `/units/<id>` | Ver / editar / deshabilitar |
| GET/POST | `/tenants` | Listar / crear inquilinos |
| GET/PUT/DELETE | `/tenants/<id>` | Ver / editar / deshabilitar |
| GET/POST | `/meters` | Listar / crear medidores |
| GET/PUT/DELETE | `/meters/<id>` | Ver / editar / deshabilitar |
| POST | `/meters/replace` | Cambiar de medidor cerrando vigencias |
| GET | `/readings` | Listar lecturas |
| GET | `/readings/sheet/<period>` | Planilla del mes con lectura anterior precargada |
| POST | `/readings` | Registrar una lectura |
| POST | `/readings/bulk` | Registrar la toma de lecturas del mes |
| PUT/DELETE | `/readings/<id>` | Editar / eliminar |

`DELETE` sobre unidades, inquilinos y medidores **deshabilita**, no borra: el
histórico de cargos y lecturas tiene que seguir cuadrando.

### Facturación — `/api/billing`

| Método | Ruta | Qué hace |
|---|---|---|
| GET/POST | `/bills` | Listar / registrar el recibo global del mes |
| DELETE | `/bills/<id>` | Eliminar recibo global |
| POST | `/generate/<period>` | Generar los cobros del periodo |
| GET | `/summary/<period>` | Consolidado con el faltante de áreas comunes |
| GET | `/charges` | Listar cobros (filtros: `period`, `unit_id`, `status`) |
| GET | `/charges/<id>` | Recibo del inquilino, con lecturas y pagos |
| GET | `/units/<id>/history` | Histórico de consumo |
| GET | `/alerts/<period>` | Departamentos fuera de su promedio |
| POST | `/payments` | Registrar pago |
| DELETE | `/payments/<id>` | Eliminar pago |

### Validaciones

- El periodo debe ser `YYYY-MM` con mes entre 01 y 12
- `service_type` solo acepta `luz` o `agua`
- `total_units` mayor que cero, o no se puede calcular la tarifa
- Una lectura menor que la anterior se rechaza: es error de digitación
- El monto de un pago debe ser numérico y mayor que cero

### Flujo mensual

```
POST /api/billing/bills          { service_type, period, total_amount, total_units }
GET  /api/utilities/readings/sheet/2026-10
POST /api/utilities/readings/bulk { readings: [...] }
POST /api/billing/generate/2026-10
GET  /api/billing/summary/2026-10
POST /api/billing/payments       { charge_id, amount, method }
```

## Pruebas de la API

```bash
python test_billing_api.py
```

72 comprobaciones contra los endpoints con el test client, incluyendo token
inválido, validaciones y casos borde. Estado actual: **72 OK, 0 fallas**.

## Frontend

Ruta `/api/admin/recibos`, en la sección **Edificio** del menú lateral.

| Archivo | Contenido |
|---|---|
| `src/app/admin/interfaces/recibo.ts` | Tipos del módulo |
| `src/app/admin/services/recibo.service.ts` | Cliente de los 33 endpoints |
| `src/app/admin/components/recibos/` | Componente standalone |

Usa las clases `adm-*` del sistema de diseño existente; lo propio del módulo
lleva el prefijo `rec-`. Hereda tema, acento y tipografía del customizer.

### Pestañas

**Resumen** — KPIs del mes, cuadre de luz con barra de reparto, alertas de
consumo y detalle por departamento. El KPI de áreas comunes muestra en ámbar lo
que absorbe el propietario y su porcentaje sobre el recibo. Botón «Generar
periodo»; si algún cobro tenía pagos, el aviso dice cuántos no se recalcularon.

**Lecturas** — planilla del mes, un renglón por medidor vigente con la lectura
anterior precargada. El consumo se calcula mientras se teclea. Una lectura menor
que la anterior pinta el renglón y bloquea el guardado: un medidor no retrocede.
Se guardan todas juntas con `readings/bulk`.

**Recibos del edificio** — carga del recibo global de luz y agua. Al escribir
total e unidades muestra la tarifa resultante antes de guardar.

**Cobros y pagos** — cobros del periodo filtrables por estado. «Ver recibo» abre
el recibo del inquilino con lecturas, conceptos, saldo arrastrado y pagos.
«Pagar» registra el pago y avisa cuánto quedará como saldo a favor si el monto
excede lo pendiente.

**Maestros** — departamentos, inquilinos y medidores. El botón «Reemplazar» de un
medidor vigente cierra su vigencia y abre la del nuevo en la misma fecha, que es
el caso del 303.

### Build

```bash
cd amarutech-app-web
npm start          # desarrollo
npx ng build       # producción
```

El módulo compila sin errores ni warnings.

## PDF y envío por correo

`src/services/ReceiptPdfService.py` genera el recibo en PDF con `reportlab`
(agregado a `requirements.txt`). Reemplaza la captura de pantalla del Excel.

El PDF incluye encabezado con departamento y periodo, datos del inquilino,
tabla de lecturas (con el total sumado cuando hay varios medidores), conceptos
con su detalle de cálculo, total a pagar, pagos registrados y la nota que
explica de dónde salen las tarifas.

La tarifa de luz se imprime con **4 decimales**: redondeada a 2 aparecía como
`S/ 1.00` y el inquilino no podía rehacer la multiplicación.

### Endpoints

| Método | Ruta | Qué hace |
|---|---|---|
| GET | `/api/billing/charges/<id>/pdf` | Descarga el recibo en PDF |
| POST | `/api/billing/charges/<id>/send` | Envía el recibo por correo con el PDF |
| POST | `/api/billing/send/<period>` | Envía los recibos del periodo a todos |

`send` usa el correo de la ficha del inquilino; se puede pasar `{"email": "..."}`
en el body para enviar a otra dirección. Si no hay ninguno responde 400. Si el
SMTP falla responde 502 sin romper la operación.

El envío masivo devuelve `sent`, `skipped` (sin correo registrado) y `failed`,
para saber exactamente qué pasó con cada departamento.

### Mailer

`Mailer._send` ahora acepta adjuntos. Con adjuntos el contenedor MIME pasa a
`mixed` con el HTML dentro de un `alternative`: `alternative` es para versiones
del mismo cuerpo, no para archivos.

### Frontend

En la pestaña **Cobros y pagos** cada fila tiene botón de descarga de PDF y de
envío por correo, y la barra superior tiene «Enviar todos por correo», que abre
un resumen de enviados, omitidos y con error. El modal del recibo también tiene
ambos botones.

## Pruebas del PDF y el correo

```bash
python test_receipt_pdf.py
```

51 comprobaciones con SMTP simulado: **no se envía ningún correo real**, se
inspecciona el mensaje que se habría enviado. Cubren formato, generación del
PDF, el caso del 303 con dos medidores, estructura MIME del adjunto, los tres
endpoints, el envío masivo y el comportamiento ante un SMTP caído.
Estado actual: **51 OK, 0 fallas**.

## Estado completo de las pruebas

```bash
python test_billing.py       # 46 OK — motor de cálculo
python test_billing_api.py   # 72 OK — API REST
python test_receipt_pdf.py   # 51 OK — PDF y correo
```

## Ciclo de facturación

El ciclo **va de toma a toma**, no del 1 al 30 del mes: arranca el día en que el
inquilino ingresó al departamento. En el histórico real:

| Depto. | Inquilino | Ciclo |
|---|---|---|
| 304 | SUSAN SUAREZ | del 20 al 20 (ingresó el 20-03-2026) |
| 301 / 303 | ALEXANDER GUEVARA | del 4 al 4 |
| 201 | LEYDI CAYACA | del 1 al 1 |

`generate_period` derivaba las fechas de `period_bounds()`, o sea el mes
calendario, y ponía `01-09-2026 a 30-09-2026` en **todos** los recibos. Ahora usa
`get_unit_cycle(unit_id, period)`, que las saca de las lecturas de la unidad:
la fecha más temprana de `previous_date` y la más tardía de `current_date`, de
modo que un cambio de medidor a mitad de ciclo quede cubierto entero.

El mes calendario queda solo como respaldo para una unidad que todavía no tiene
lecturas fechadas en el periodo.

La planilla de lecturas (`/readings/sheet/<period>`) devuelve `previous_date` —
el cierre del ciclo anterior — y sugiere `current_date` en el mismo día del mes
siguiente, ajustado cuando ese día no existe (un ciclo del 31 pasa al 28 en
febrero).

## Formato de fechas

Todas las fechas se muestran en **dd-mm-aaaa**, tanto en el PDF (`fecha()` en
`ReceiptPdfService`) como en el panel (`fecha()` en `ReciboService`). Los
`<input type="date">` siguen en ISO porque el navegador lo exige.

La tabla de lecturas del PDF y del panel trae columnas **Desde** y **Hasta** con
las fechas de cada toma, que es donde se ve el ciclo real.
