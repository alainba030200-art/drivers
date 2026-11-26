# drivers
busca los drivers de la computadora y si hay desactualizados, te refiere si se puede o no actualizar.
# Escáner de Hardware y Clasificador de Drivers (Windows)

Herramienta de escritorio ligera para Windows desarrollada en Python (`tkinter` + consultas CIM/PnP nativas) que audita los controladores del sistema, clasifica su estado por código de colores y facilita la búsqueda de paquetes oficiales.

## Características
- **Clasificación visual intuitiva:**
  - **Verde intenso (`Necesita actualizarse`):** Dispositivos sin controlador instalado o con errores PnP (ej. Código 28).
  - **Verde claro (`Puede actualizar`):** Controladores de terceros instalados con versiones antiguas.
  - **Rojo (`NO ACTUALIZAR`):** Controladores nativos del núcleo de Windows que no deben modificarse manualmente.
  - **Blanco (`Al día`):** Controladores recientes y operativos.
- **Identificación real de hardware:** Extrae el `VEN_ID` / `DEV_ID` limpio (`PCI` y `USB`) para detectar el fabricante real del chip.
- **Búsqueda asistida:** Acceso directo al soporte oficial del fabricante, búsqueda filtrada del paquete `.inf` y consulta en base de datos *DeviceHunt*.
- **Exportación:** Genera reportes completos en **CSV** y **TXT**.

## Requisitos y Ejecución
- Windows 10 / 11 con PowerShell habilitado.
- Python 3.10+ (sin dependencias externas para ejecutar el `.py`).

```bash
python escaner_drivers.py ya tengo varias modificaciones, se vale modificar y mejorar.
Gracias!-
