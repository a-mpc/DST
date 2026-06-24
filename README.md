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

La herramienta incluye un documento `pyproject.toml`, un fichero de configuración del empaquetado. Contiene metadatos del proyecto, sus dependencias y la configuración de ciertas herramientas, por lo que para instalar las bibliotecas requeridas por la DST bastará con ejecutar el comando:

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

Los datos de entrada que se deben proporcionar a la herramienta son: la ontología, el escenario de la misión, los eventos registrados y el catálogo de contramedidas disponible.

La estructura en que se deberán aportar estos archivos es la siguiente:

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

Carpeta en la que se incorporan los datos de entrada. Para cada escenario se deberá crear un directorio, en el que se definirá: el escenario de la misión, `mission.json`; los eventos registrados, `events.json`; y el catálogo de mitigaciones, `/countermeasures/catalog.json`.

### /output

Directorio que contiene los informes de evaluación generados por la DST, organizados por carpetas.

### /src

Código de la herramienta, organizado en ocho módulos orquestados mediante el *script main.py*: carga de la ontología (*ontology*), carga del escenario (*scenario*), generación del grafo (*graph*), evaluación del escenario (*evaluator*), carga del catálogo de contramedidas (*catalog*), recomendación de contramedidas (*recommendator*), generación del informe de evaluación de la misión (*report*) y definición de los modelos de datos empleados en la DST (*models*).

## Ejecución

Una vez se ha activado el entorno virtual descrito en el apartado de requisitos, bastará con introducir en un terminal el siguiente comando para ejecutar la herramienta:

```
python -m tfg.main <nombre-del-escenario>
```

El `<nombre-del-escenario>` deberá ser el del directorio que contenga la información del escenario a evaluar, situado dentro de `/data` según se ha indicado en el apartado de estructura.

Por ejemplo, para ejecutar el primer caso de uso propuesto, habría que escribir en línea de comandos:

```
python -m tfg.main scenario_01
```

Una vez finalice la ejecución de la DST, se almacenarán los informes en `/output/<nombre-del-escenario>`.

Cabe resaltar que las rutas de los directorios son relativas con respecto a la carpeta raíz de la DST.

### Alejo Martínez de Pisón Campo

### Trabajo Fin de Grado - Grado en Ingeniería de Tecnologías y Servicios de Telecomunicación

### ETSIT - UPM
