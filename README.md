# Laboratorio #4 Teoría de la Computación (AFN por Thompson + simulación + dibujo con Matplotlib)

## Descripción

Este repositorio implementa el **algoritmo de Thompson** para convertir una **expresión regular** en un **AFN**, lo **dibuja** en PNG (usando **matplotlib**, sin Graphviz) y **simula** si una cadena $w$ pertenece al lenguaje de la expresión.

**Operadores soportados:**
`|` (unión), **concatenación implícita**, `*` (Kleene), `+` (una o más), `?` (cero o una), paréntesis `()`, y `ε` (epsilon).

---

## Rama (branch) del proyecto

Se usa **una rama por problema**.
Para este problema, el trabajo está en la rama **`Problema_1`**.

Comandos de referencia:

```bash
git checkout -b Problema_1   # crear y cambiar a la rama
# ...trabajar, agregar archivos y commits...
git add .
git commit -m "Problema 1: Thompson NFA + simulador + dibujo con matplotlib"
git push -u origin Problema_1
```

---

## Requisitos

* **Python 3.9**
* `pip install matplotlib`

---

## Archivos principales

* `thompson_nfa.py` — Script que:

  1. parsea la ER,
  2. construye el AFN por Thompson,
  3. lo grafica a PNG (matplotlib),
  4. simula la aceptación de una cadena $w$.

Salida de imágenes en la carpeta `out_nfas/` (se crea automáticamente).

---

## Cómo funciona (resumen técnico)

1. **Preprocesado:** inserta la **concatenación explícita** `.` donde corresponde.
2. **Shunting-Yard:** convierte la ER a **postfijo** respetando precedencias.
3. **Thompson:** apila **fragmentos** y crea estados/transiciones con `ε`.
4. **Simulación:** se calcula **ε-cierre** y **move** símbolo a símbolo; al final, si el estado de aceptación está en el conjunto actual → **“sí”**, de lo contrario **“no”**.
5. **Dibujo:** genera un PNG con nodos (doble círculo para aceptación), flecha de inicio y etiquetas en cada transición.

---

## Formato de entrada

Archivo de texto con **una ER por línea**.
Ejemplo (`regexes.txt`) — las 4 del enunciado:

```
(a*|b*)+
((ε|a)|b*)*
(a|b*)*abb(a|b)*
0?(1?)?0*
```

> **Epsilon** debe ponerse como el carácter **`ε`**.

Opcionalmente, un archivo `words.txt` con **una cadena por línea**, alineada con cada ER.

---

## Ejecución

### 0) Instalar dependencia (una vez)

```bash
pip install matplotlib
```

### 1) Modo interactivo (pide una `w` por cada ER)

```bash
python thompson_nfa.py --input regexes.txt
```

* Para probar **ε (cadena vacía)**, presiona **ENTER** cuando la pida.

### 2) Misma `w` para todas las ER

```bash
python thompson_nfa.py --input regexes.txt --word ababb
```

* Para ε con este modo:

  * Linux/Mac: `--word ''`
  * Windows: `--word ""`

### 3) Archivo de palabras (una por ER)

Crea `words.txt`, por ejemplo:

```
abba
baa
babbba
0100
```

Ejecuta:

```bash
python thompson_nfa.py --input regexes.txt --words words.txt
```

### 4) Cambiar carpeta de salida de imágenes (opcional)

```bash
python thompson_nfa.py --input regexes.txt --outdir resultados
```

---

## Qué verás en la salida

* En consola, por cada ER:

  * El nombre del PNG generado (`out_nfas/nfa_i.png`).
  * El veredicto de la simulación: `w = '...'  ->  sí/no`.
* En `out_nfas/`, archivos `nfa_1.png`, `nfa_2.png`, etc.

  * **Estado inicial:** flecha desde un punto sólido.
  * **Estado de aceptación:** **doble círculo**.
  * **Transiciones:** flechas etiquetadas con el símbolo o `ε`.

---

## Ejemplo reproducible (como en la prueba)

Con `regexes.txt` anterior y en modo interactivo, ingresa:

```
(a*|b*)+            -> abba
((ε|a)|b*)*         -> baa
(a|b*)*abb(a|b)*    -> babbba
0?(1?)?0*           -> 0100
```

Resultados esperados: **sí, sí, sí, sí**.
Si ejecutas `--word ababb`, esperas:

* ER 1: **sí**
* ER 2: **sí** (acepta cualquier cadena sobre {a,b}, incluyendo ε)
* ER 3: **sí**
* ER 4: **no** (solo 0/1 con la forma indicada)

---

## Consejos y consideraciones

* Si ves `ModuleNotFoundError: matplotlib`, instala dependencias: `pip install matplotlib`.
* En Windows también puedes usar el launcher: `py -3.9 thompson_nfa.py --input regexes.txt`.
* Si no aparece la carpeta de salida, crea otra con `--outdir` o revisa permisos.

---

## Video de ejecución

Hay un **video corto** con la ejecución real del programa (carga de `regexes.txt`, uso en modo interactivo y con `--word`, y revisión de los PNG generados en `out_nfas/`).
**YouTube:** [https://youtu.be/wPjZlh8USHA](https://youtu.be/wPjZlh8USHA)

---

