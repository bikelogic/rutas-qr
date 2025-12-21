# 🚴 BikeLogic - Sistema de Gestión de Rutas

Sistema inteligente de optimización de rutas para entregas en bicicleta en Sant Cugat del Vallès.

## 📁 Estructura del Proyecto

```
BikeLogic/
├── src/                      # Código fuente principal
│   ├── main.py              # Punto de entrada
│   ├── config.py            # Configuración del proyecto
│   ├── sheets_manager.py    # Gestión de Google Sheets
│   ├── geocoding.py         # Geocodificación de direcciones
│   ├── zone_manager.py      # Gestión de zonas geográficas
│   ├── tsp_solver.py        # Algoritmo TSP (Travelling Salesman)
│   ├── line_distance_solver.py  # Cálculo de distancias en línea
│   ├── address_cleaner.py   # Limpieza de direcciones
│   ├── street_name_corrector.py # Corrección de nombres de calles
│   └── bike.py              # Modelo de datos de bicicleta
│
├── web/                     # Aplicación web de escaneo de códigos
│   └── index.html          # Escáner de códigos de barras
│
├── data/                    # Datos y recursos
│   └── carrers_SantCugat.csv  # Calles de Sant Cugat
│
├── docs/                    # Documentación
│   ├── README.md           # Documentación original
│   └── INSTALL.md          # Guía de instalación
│
├── tests/                   # Tests (por añadir)
│
├── requirements.txt         # Dependencias Python
├── .gitignore              # Archivos ignorados por Git
└── README.md               # Este archivo
```

## 🚀 Inicio Rápido

### 1. Clonar el repositorio
```bash
git clone https://github.com/TU-USUARIO/bikelogic.git
cd bikelogic
```

### 2. Crear entorno virtual
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar credenciales
Crea un archivo `key1.json` con tus credenciales de Google Sheets API en la raíz del proyecto.

> ⚠️ **Importante**: Nunca subas `key1.json` a Git. Ya está en `.gitignore`.

### 5. Ejecutar
```bash
cd src
python main.py
```

## 📱 Escáner de Códigos de Barras

La carpeta `web/` contiene una aplicación web móvil para escanear códigos de barras y buscarlos en Google Sheets.

### Deploy en GitHub Pages

1. Sube el repositorio a GitHub
2. Ve a Settings > Pages
3. Selecciona la rama y carpeta `/web`
4. ¡Listo! Tendrás una URL pública

### Deploy en Netlify

1. Arrastra la carpeta `web/` a [Netlify Drop](https://app.netlify.com/drop)
2. O conecta el repositorio de GitHub para deploy automático

Ver más detalles en [`web/README.md`](web/README.md) (si existe).

## 🛠️ Tecnologías

- **Python 3.8+**
- **Google Sheets API** - Gestión de datos
- **Google Maps API** - Geocodificación
- **OR-Tools** - Optimización de rutas (TSP)
- **QuaggaJS** - Escaneo de códigos de barras (web)

## 📦 Dependencias principales

```txt
google-auth
google-auth-oauthlib
google-auth-httplib2
google-api-python-client
googlemaps
ortools
```

## 🔧 Configuración

Edita `src/config.py` para configurar:
- IDs de Google Sheets
- API Keys de Google Maps
- Polígonos de zonas
- Punto de depósito (inicio de rutas)

## 📝 Licencia

[Añadir licencia]

## 👥 Contribuir

Las contribuciones son bienvenidas. Por favor:
1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📧 Contacto

[Añadir información de contacto]

---

**Desarrollado con ❤️ para optimizar entregas en bicicleta**
