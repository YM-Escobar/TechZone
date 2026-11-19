# Catálogo semilla de productos

154 productos de las siete categorías del configurador, estructurados según
*TECHZONE — Catálogo de Especificaciones Técnicas v1.1*.

| Archivo | Categoría | Productos |
|---|---|---|
| `cpu.json` | `cpu` | 25 |
| `placa_madre.json` | `placa_madre` | 24 |
| `ram.json` | `ram` | 22 |
| `gpu.json` | `gpu` | 21 |
| `fuente.json` | `fuente` | 21 |
| `refrigeracion.json` | `refrigeracion` | 20 |
| `almacenamiento.json` | `almacenamiento` | 21 |

## Cargar el catálogo

Desde `backend/`, con `DATABASE_URL` apuntando a la base deseada (`.env`):

```bash
python -m app.db.seed_products --dry-run   # solo valida, no escribe
python -m app.db.seed_products             # crea o actualiza
```

Con Docker: `docker compose exec backend python -m app.db.seed_products`.

- Los productos se registran con `ProductService`, igual que la API, así que
  `is_builder_eligible` lo calcula el backend (guía §2).
- Un producto se identifica por nombre + categoría: si ya existe se actualiza
  y **no** se le cambia el stock. Se puede ejecutar varias veces.
- Si un JSON no trae `purchase_url`, se usa la búsqueda en Amazon del nombre
  exacto del producto.
- `tests/test_seed_catalog.py` comprueba que todos los productos sean elegibles
  y que el catálogo no choque con el motor de compatibilidad.

## Convenciones que el motor exige (comparación de texto exacta)

- **CPU ↔ placa madre:** `supported_cpu_models[].model` debe ser idéntico al
  `name` del producto CPU (ej. `"AMD Ryzen 7 9800X3D"`). Si se agrega una CPU,
  hay que añadirla a las placas de su socket.
- **Sockets:** `AM4`, `AM5`, `LGA1700`, `LGA1851`, igual en CPU, placas y
  refrigeración.
- **Conectores GPU ↔ fuente:** se usan los mismos textos en ambos lados:
  `PCIe 8-pin`, `12VHPWR`, `12V-2x6`. En la fuente, `PCIe 8-pin` cuenta los
  conectores 6+2. El ejemplo de la guía (`8-pin` en GPU y `PCIe 6+2-pin` en
  fuente) no coincidiría en el motor y daría una incompatibilidad falsa.
- **M.2:** formatos como `2280`, sin prefijo, en placas y SSD.

## Estado de los datos

Los datos se basan en las fichas de los fabricantes, pero **todavía no tienen
fuente auditada** campo por campo. `control_fuentes.csv` es la hoja de control
de la guía (§9), con el estado `Pendiente`. Antes de la entrega hay que
verificar cada producto y anotar la fecha de consulta.

Limitaciones conocidas:

- **`min_bios_version` no se registró** en ninguna placa porque no se tiene la
  versión exacta. Las placas B650/X670 con Ryzen 9000, las B550 con Ryzen 5000
  y las B760/Z790 con Intel 14.ª gen pueden necesitar una actualización de BIOS.
  Con el dato, el builder mostraría la advertencia correspondiente.
- **`tdp_rating_w` solo aparece donde el fabricante lo publica** (DeepCool,
  be quiet!). Con el resto de disipadores la regla térmica queda indeterminada
  y el builder muestra "requiere revisión". Esto es intencional (guía §4).
- Las ranuras M.2 que admiten tanto PCIe como SATA se registraron solo como
  PCIe, para no contar dos veces la misma ranura física. Por eso el catálogo no
  incluye SSD M.2 SATA.
- **Precio (USD) y stock son valores iniciales de referencia**, no inventario real.
