# Diseño y desarrollo de una herramienta de soporte a la toma de decisiones frente a ciberamenazas en escenarios multidominio

El código contenido en este repositorio permite ejecutar una herramienta de soporte a la toma de decisiones (DST) frente a ciberamenazas en operaciones multidominio, desarrollada para un Trabajo Fin de Grado.

Su objetivo es evaluar el estado de la operación para recomendar contramedidas priorizadas que mitiguen el efecto de eventos en las misiones.

## Requisitos

Para poder ejecutar la DST en una máquina, es necesario tener instalado Python. En sistemas operativos Windows o macOS se puede desgargar el instalador en https://www.python.org/downloads/. Desde Linux se debe ejecutar en línea de comandos:

```
sudo apt update
sudo apt install python3 python3-venv python3-pip
```

Para verificar su correcta instalación, hay que ejecutar desde un terminal:

```
python3 --version
```

La versión deberá ser 3.11 o superior.

Se recomienda la creación de un entorno virtual de Python para la instalación de paquetes y la ejecución de la herramienta (más información en https://docs.python.org/es/3/tutorial/venv.html).

Para ello, será necesario ejecutar el siguiente comando desde la carpeta que contenga el código de la DST:

```
python3 -m venv venv
```

Dicho entorno virtual se activa con el comando:

```
source venv/bin/activate        # Linux / macOS
venv\Scripts\activate.bat       # Windows
```

La herramienta incluye un fichero `pyproject.toml` [...]

```
pip install -e .
```

Se pueden comprobar los requisitos específicos de estas bibliotecas en los siguientes enlaces:

| Biblioteca | Enlace |
| --- | --- |
| Owlready2 | https://owlready2.readthedocs.io/en/v0.50/ |
| NumPy | https://numpy.org |
| NetworkX | https://networkx.org/en/ |
| Jinja | https://jinja.palletsprojects.com/en/stable/ |
| WeasyPrint | https://weasyprint.org |
| Matplotlib | https://matplotlib.org |
| Pydantic | https://pydantic.dev/docs/validation/latest/get-started/ |

## Estructura

Intro

```
data
 └ ontology
   └ mission.owx
 └ scenarios
   └ <nombre-del-escenario>
     └ countermeasures
       └ catalog.json
     └ events.json
     └ mission.json
output
src
```


### /data

Bloque para explicar cómo se estructura el proyecto contenido en este repositorio.

### /output

Directorio que contiene los informes de evaluación generados por la DST organizados por carpetas.

### /src

Bloque para explicar cómo se estructura el proyecto contenido en este repositorio.

## Ejecución

Una vez se ha activado el entorno virtual descrito en el apartado de requisitos, bastará con introducir en un terminal el siguiente comando para ejecutar la herramienta:

```
python -m tfg.main <nombre-del-escenario>
```

El `<nombre-del-escenario>` deberá ser el del directorio que contenga la información del escenario a evaluar, situado dentro de `/data` según se ha indicado en el apartado de estructura.

Una vez finalice la ejecución de la DST, se almacenarán los informes en `/output/<nombre-del-escenario>`.

Cabe resaltar que las rutas de los directorios [son relativas con respecto a la carpeta raíz del proyecto].

### Alejo Martínez de Pisón Campo

### Trabajo Fin de Grado - Grado en Ingeniería de Tecnologías y Servicios de Telecomunicación

### ETSIT - UPM
