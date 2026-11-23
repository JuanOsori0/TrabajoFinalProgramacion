from datetime import date
from random import randint

# Niveles de alquiler, en el orden en que se muestran en el informe.
NIVEL_BAJO = "Bajo"
NIVEL_MEDIO = "Medio"
NIVEL_ALTO = "Alto"
NIVEL_AGOTADO = "Agotado"
NIVELES = [NIVEL_BAJO, NIVEL_MEDIO, NIVEL_ALTO, NIVEL_AGOTADO]

# Porcentaje de las carpas instaladas desde el cual empieza cada nivel.
UMBRAL_MEDIO = 40
UMBRAL_ALTO = 70
UMBRAL_AGOTADO = 95

CARPAS_INSTALADAS_MINIMAS = 1
CAMPOS_POR_PLAYA = 5
CAMPOS_POR_ALQUILER = 2

# Lo usan la lógica y la interfaz, para que el aviso sea siempre el mismo.
MENSAJE_CARGA_CON_PLAYAS = "La carga solo se hace con el programa sin playas."

# Un día, obtenido como diferencia de dos fechas: permite sumar días a una
# fecha (fecha + UN_DIA * n) sin importar timedelta.
UN_DIA = date(2026, 1, 2) - date(2026, 1, 1)
# Última fecha que Python puede representar: ningún registro pasa de aquí.
FECHA_MAXIMA = date(9999, 12, 31)
MENSAJE_FIN_CALENDARIO = (
    f"El registro de la playa ya llegó a la última fecha del calendario ({FECHA_MAXIMA})."
)


# ----------------------------------------------------------------------
# Funciones de apoyo: enteros, fechas, validaciones y archivos
# ----------------------------------------------------------------------

def convertir_entero(texto: str) -> int | None:
    """Devuelve el entero que representa el texto, o None si no lo es.
    Se aceptan espacios en los extremos y un signo + o - al inicio;
    todo lo demás deben ser dígitos del 0 al 9."""
    texto = texto.strip()
    posicion = 0
    cantidad_digitos = 0
    for letra in texto:
        es_digito = letra >= "0" and letra <= "9"
        es_signo = posicion == 0 and (letra == "+" or letra == "-")
        if not es_digito and not es_signo:
            return None
        if es_digito:
            cantidad_digitos = cantidad_digitos + 1
        posicion = posicion + 1
    if cantidad_digitos == 0:
        return None
    try:
        return int(texto)
    except ValueError:
        # Desde Python 3.11, int() no convierte textos de más de 4300 cifras.
        # Un número así no es un dato válido para ningún campo del programa.
        return None


def construir_fecha(año: int | None, mes: int | None, dia: int | None) -> date:
    """Convierte año, mes y día en una fecha del calendario. Un valor None
    (no era un entero) o una combinación inexistente lanzan ValueError."""
    if año is None or mes is None or dia is None:
        raise ValueError("La fecha no es válida.")
    try:
        return date(año, mes, dia)
    except ValueError:
        # La fecha no existe (por ejemplo, el 31 de noviembre).
        raise ValueError("La fecha no es válida.")
    except OverflowError:
        # Un número demasiado grande para ser un año, un mes o un día.
        raise ValueError("La fecha no es válida.")


def validar_dias_simulados(dias: int | None) -> None:
    """Lanza ValueError si el número de días a simular no es válido."""
    if dias is None:
        raise ValueError("El número de días debe ser un número entero.")
    if dias < 1:
        raise ValueError("Se debe simular al menos un día.")


def validar_minimo_maximo(minimo: int, maximo: int) -> None:
    """Lanza ValueError si el mínimo es mayor que el máximo."""
    if minimo > maximo:
        raise ValueError("El mínimo no puede ser mayor que el máximo.")


def separar_campos(linea: str) -> list:
    """Separa una línea por los ';' y quita los espacios de cada campo."""
    campos = []
    for campo in linea.split(";"):
        campos.append(campo.strip())
    return campos


def leer_lineas(ruta: str) -> list:
    """Lee un archivo de texto UTF-8 y devuelve la lista de sus líneas.
    Si el archivo no existe, lanza FileNotFoundError; si no se puede leer,
    OSError; si no está en UTF-8, UnicodeDecodeError. Como el archivo se lee
    entero antes de procesarlo, un error de lectura no deja datos a medias.
    El 'with' cierra el archivo aunque la lectura falle."""
    lineas = []
    with open(ruta, encoding="utf-8") as archivo:
        for linea in archivo:
            lineas.append(linea)
    return lineas


# ----------------------------------------------------------------------
# Playa: una playa y su registro diario de carpas alquiladas
# ----------------------------------------------------------------------

class Playa:

    def __init__(self, nombre: str, carpas_instaladas: int | None,
                 año: int | None, mes: int | None, dia: int | None) -> None:
        # Un None en carpas_instaladas, año, mes o dia significa que el dato
        # tecleado o leído no era un entero. Las condiciones se revisan en el
        # orden del caso y antes de guardar cualquier atributo.
        nombre_limpio = nombre.strip()
        if nombre_limpio == "":
            raise ValueError("El nombre no puede estar vacío.")
        if carpas_instaladas is None:
            raise ValueError("Las carpas instaladas deben ser un número entero.")
        if carpas_instaladas < CARPAS_INSTALADAS_MINIMAS:
            raise ValueError("La playa debe tener al menos una carpa instalada.")
        fecha_inicio = construir_fecha(año, mes, dia)

        self.nombre = nombre_limpio
        self.carpas_instaladas = carpas_instaladas
        self.fecha_inicio = fecha_inicio
        # alquileres[i] son las carpas alquiladas del día fecha_del_dia(i).
        self.alquileres = []

    # --- Registro de días ---------------------------------------------

    def dias_registrados(self) -> int:
        return len(self.alquileres)

    def dias_disponibles(self) -> int:
        """Cuántos días más caben en el registro sin pasar de FECHA_MAXIMA."""
        return (FECHA_MAXIMA - self.fecha_inicio).days + 1 - len(self.alquileres)

    def fecha_del_dia(self, posicion: int) -> date:
        """Fecha del día que ocupa la posición dada en el registro."""
        return self.fecha_inicio + UN_DIA * posicion

    def fecha_siguiente(self) -> date | None:
        """Fecha del día que sigue en el registro, o None si el registro ya
        llegó a FECHA_MAXIMA."""
        if self.dias_disponibles() < 1:
            return None
        return self.fecha_del_dia(len(self.alquileres))

    def ultimo_dia(self) -> date | None:
        """Fecha del último día registrado, o None si no hay días."""
        if len(self.alquileres) == 0:
            return None
        return self.fecha_del_dia(len(self.alquileres) - 1)

    def validar_carpas(self, carpas: int | None) -> None:
        """Lanza ValueError si las carpas alquiladas de un día no son válidas."""
        if carpas is None:
            raise ValueError("Las carpas alquiladas deben ser un número entero.")
        if carpas < 0 or carpas > self.carpas_instaladas:
            raise ValueError(
                f"Las carpas alquiladas van de 0 a {self.carpas_instaladas}."
            )

    def registrar_dia(self, carpas: int | None) -> None:
        """Valida las carpas y las agrega como el día siguiente del registro."""
        self.validar_carpas(carpas)
        if self.dias_disponibles() < 1:
            raise ValueError(MENSAJE_FIN_CALENDARIO)
        self.alquileres.append(carpas)

    def simular_dias(self, dias: int | None, minimo: int | None,
                     maximo: int | None) -> None:
        """Agrega 'dias' días con carpas alquiladas al azar entre minimo y
        maximo (ambos incluidos). Si algún dato no es válido, lanza
        ValueError y no agrega ningún día."""
        validar_dias_simulados(dias)
        self.validar_carpas(minimo)
        self.validar_carpas(maximo)
        validar_minimo_maximo(minimo, maximo)
        disponibles = self.dias_disponibles()
        if disponibles == 0:
            raise ValueError(MENSAJE_FIN_CALENDARIO)
        if dias > disponibles:
            if disponibles == 1:
                raise ValueError("Solo se puede registrar 1 día más en esa playa.")
            raise ValueError(
                f"Solo se pueden registrar {disponibles} días más en esa playa."
            )
        for _ in range(dias):
            self.registrar_dia(randint(minimo, maximo))

    # --- Indicadores ----------------------------------------------------
    # Si la playa no tiene días registrados, total() da 0 y los demás None.

    def total(self) -> int:
        suma = 0
        for carpas in self.alquileres:
            suma = suma + carpas
        return suma

    def promedio(self) -> float | None:
        if len(self.alquileres) == 0:
            return None
        return self.total() / len(self.alquileres)

    def porcentaje_alquiler(self) -> float | None:
        """Promedio de carpas alquiladas entre las instaladas, por cien."""
        promedio = self.promedio()
        if promedio is None:
            return None
        return promedio / self.carpas_instaladas * 100

    def porcentaje_mayor_que(self, otra: "Playa") -> bool:
        """True si el porcentaje de esta playa es estrictamente mayor que el
        de la otra (las dos con días registrados). El porcentaje es
        total * 100 / (días * carpas instaladas); para comparar dos fracciones
        sin decimales se multiplica en cruz: a/b > c/d equivale a a * d > c * b
        (con b y d positivos)."""
        izquierda = self.total() * len(otra.alquileres) * otra.carpas_instaladas
        derecha = otra.total() * len(self.alquileres) * self.carpas_instaladas
        return izquierda > derecha

    def desviacion_estandar(self) -> float | None:
        promedio = self.promedio()
        if promedio is None:
            return None
        suma_cuadrados = 0
        for carpas in self.alquileres:
            diferencia = carpas - promedio
            suma_cuadrados = suma_cuadrados + diferencia * diferencia
        return (suma_cuadrados / len(self.alquileres)) ** 0.5

    def posicion_extrema(self, buscar_maximo: bool) -> int | None:
        """Posición del primer día con más (o con menos) carpas alquiladas.
        None si no hay días registrados."""
        if len(self.alquileres) == 0:
            return None
        posicion = 0
        for i in range(1, len(self.alquileres)):
            if buscar_maximo and self.alquileres[i] > self.alquileres[posicion]:
                posicion = i
            elif not buscar_maximo and self.alquileres[i] < self.alquileres[posicion]:
                posicion = i
        return posicion

    def fecha_maximo(self) -> date | None:
        """Fecha del primer día con más carpas alquiladas."""
        posicion = self.posicion_extrema(True)
        if posicion is None:
            return None
        return self.fecha_del_dia(posicion)

    def fecha_minimo(self) -> date | None:
        """Fecha del primer día con menos carpas alquiladas."""
        posicion = self.posicion_extrema(False)
        if posicion is None:
            return None
        return self.fecha_del_dia(posicion)

    # --- Niveles de alquiler -------------------------------------------

    def nivel(self, carpas: int) -> str:
        """Nivel de un día. Se compara con enteros (carpas * 100 contra
        umbral * instaladas) para evitar errores de decimales en los bordes."""
        por_cien = carpas * 100
        if por_cien < UMBRAL_MEDIO * self.carpas_instaladas:
            return NIVEL_BAJO
        if por_cien < UMBRAL_ALTO * self.carpas_instaladas:
            return NIVEL_MEDIO
        if por_cien < UMBRAL_AGOTADO * self.carpas_instaladas:
            return NIVEL_ALTO
        return NIVEL_AGOTADO

    def dias_por_nivel(self) -> dict:
        """Diccionario con cuántos días hubo en cada nivel, también los que
        tuvieron cero días."""
        conteo = {}
        for nivel in NIVELES:
            conteo[nivel] = 0
        for carpas in self.alquileres:
            nivel = self.nivel(carpas)
            conteo[nivel] = conteo[nivel] + 1
        return conteo

    def racha_agotado(self) -> dict:
        """Racha más larga de días seguidos en nivel Agotado, como un
        diccionario con 'longitud' y 'inicio' (la fecha en que empezó).
        Si no hubo ninguna, la longitud es 0 y el inicio es None."""
        mejor_longitud = 0
        mejor_inicio = None
        actual = 0
        for i in range(len(self.alquileres)):
            if self.nivel(self.alquileres[i]) == NIVEL_AGOTADO:
                actual = actual + 1
                # Solo ">" para que, en un empate, gane la racha que empezó primero.
                if actual > mejor_longitud:
                    mejor_longitud = actual
                    mejor_inicio = self.fecha_del_dia(i - actual + 1)
            else:
                actual = 0
        return {"longitud": mejor_longitud, "inicio": mejor_inicio}

    # --- Días sin registrar --------------------------------------------

    def dias_sin_registrar(self, hoy: date) -> dict | None:
        """Días que faltan por registrar: desde el siguiente al último
        registrado hasta el anterior a hoy. Devuelve un diccionario con
        'cantidad', 'primero' y 'ultimo' (estos dos son None si no falta
        ninguno), o None si la playa no tiene días registrados."""
        ultimo_registrado = self.ultimo_dia()
        if ultimo_registrado is None:
            return None
        cantidad = (hoy - ultimo_registrado).days - 1
        if cantidad <= 0:
            return {"cantidad": 0, "primero": None, "ultimo": None}
        return {"cantidad": cantidad,
                "primero": ultimo_registrado + UN_DIA,
                "ultimo": hoy - UN_DIA}

    # --- Informe -------------------------------------------------------

    def informe(self, hoy: date) -> dict:
        """Diccionario con los datos del informe, sin redondear (el
        redondeo es cosa de la interfaz). 'hoy' es la fecha actual y se
        recibe como parámetro para poder probar con fechas fijas."""
        datos = {
            "nombre": self.nombre,
            "carpas_instaladas": self.carpas_instaladas,
            "dias": self.dias_registrados(),
        }
        if datos["dias"] == 0:
            return datos

        datos["total"] = self.total()
        datos["promedio"] = self.promedio()
        datos["porcentaje"] = self.porcentaje_alquiler()
        datos["desviacion"] = self.desviacion_estandar()
        datos["fecha_maximo"] = self.fecha_maximo()
        datos["fecha_minimo"] = self.fecha_minimo()
        datos["niveles"] = self.dias_por_nivel()
        datos["racha"] = self.racha_agotado()
        datos["ultimo_dia"] = self.ultimo_dia()
        datos["faltan"] = self.dias_sin_registrar(hoy)
        return datos


# ----------------------------------------------------------------------
# Cooperativa: todas las playas y la carga desde archivos
# ----------------------------------------------------------------------

class Cooperativa:

    def __init__(self) -> None:
        self.playas = []

    def tiene_playas(self) -> bool:
        return len(self.playas) > 0

    def buscar(self, nombre: str) -> Playa | None:
        """Busca por nombre exacto (sin espacios en los extremos). None si
        no existe."""
        nombre = nombre.strip()
        for playa in self.playas:
            if playa.nombre == nombre:
                return playa
        return None

    def crear_playa(self, nombre: str, carpas: int | None, año: int | None,
                    mes: int | None, dia: int | None) -> Playa:
        """Crea la playa y la agrega. Lanza ValueError con el mensaje de la
        primera condición que falle. Se usa tanto desde el teclado como
        desde el archivo."""
        if self.buscar(nombre) is not None:
            raise ValueError("Ya existe una playa con ese nombre.")
        playa = Playa(nombre, carpas, año, mes, dia)
        self.playas.append(playa)
        return playa

    def extremos(self) -> dict | None:
        """Diccionario con la playa de mayor porcentaje ('mayor') y la de
        menor ('menor') entre las que tienen días registrados. La
        comparación es exacta y, en un empate, gana la primera de la lista.
        Si ninguna tiene días, devuelve None."""
        mayor = None
        menor = None
        for playa in self.playas:
            if playa.dias_registrados() > 0:
                if mayor is None:
                    mayor = playa
                    menor = playa
                else:
                    if playa.porcentaje_mayor_que(mayor):
                        mayor = playa
                    if menor.porcentaje_mayor_que(playa):
                        menor = playa
        if mayor is None:
            return None
        return {"mayor": mayor, "menor": menor}

    def cargar_playas(self, ruta: str) -> dict:
        """Crea una playa por cada línea válida del archivo (la primera línea
        es el encabezado). Devuelve un diccionario con 'cargadas' (cuántas) y
        'descartadas' (lista de diccionarios con 'linea' y 'causa')."""
        if self.tiene_playas():
            raise ValueError(MENSAJE_CARGA_CON_PLAYAS)
        lineas = leer_lineas(ruta)

        cargadas = 0
        descartadas = []
        numero = 0
        for linea in lineas:
            numero = numero + 1
            if numero > 1 and linea.strip() != "":
                campos = separar_campos(linea)
                if len(campos) != CAMPOS_POR_PLAYA:
                    descartadas.append({"linea": numero,
                                        "causa": "La línea no tiene cinco campos."})
                else:
                    try:
                        self.crear_playa(campos[0], convertir_entero(campos[1]),
                                         convertir_entero(campos[2]),
                                         convertir_entero(campos[3]),
                                         convertir_entero(campos[4]))
                        cargadas = cargadas + 1
                    except ValueError as error:
                        descartadas.append({"linea": numero, "causa": str(error)})
        return {"cargadas": cargadas, "descartadas": descartadas}

    def cargar_alquileres(self, ruta: str) -> dict:
        """Registra un día por cada línea válida del archivo (la primera línea
        es el encabezado). Devuelve un diccionario con 'cargados' (cuántos) y
        'descartadas' (lista de diccionarios con 'linea' y 'causa')."""
        lineas = leer_lineas(ruta)

        cargados = 0
        descartadas = []
        numero = 0
        for linea in lineas:
            numero = numero + 1
            if numero > 1 and linea.strip() != "":
                campos = separar_campos(linea)
                if len(campos) != CAMPOS_POR_ALQUILER:
                    descartadas.append({"linea": numero,
                                        "causa": "La línea no tiene dos campos."})
                else:
                    playa = self.buscar(campos[0])
                    if playa is None:
                        if campos[0] == "":
                            causa = "No hay una playa con el nombre vacío."
                        else:
                            causa = f"No hay una playa llamada {campos[0]}."
                        descartadas.append({"linea": numero, "causa": causa})
                    else:
                        try:
                            playa.registrar_dia(convertir_entero(campos[1]))
                            cargados = cargados + 1
                        except ValueError as error:
                            descartadas.append({"linea": numero, "causa": str(error)})
        return {"cargados": cargados, "descartadas": descartadas}
