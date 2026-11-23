"""Verificador de los casos de prueba del programa de carpas.

Cada caso tiene dos archivos con el mismo nombre:
  entradas/<caso>.txt   lo que se teclea, una línea por cada vez que el
                        programa espera un dato (una línea vacía es un Enter);
  esperadas/<caso>.txt  lo que debe quedar en la pantalla, con lo tecleado
                        a continuación de cada pregunta, como en la consola.

El verificador ejecuta el main() de user_interface.py, le da las entradas en
lugar del teclado, recoge lo que se imprime y lo compara línea por línea con
la salida esperada. No cambia nada del programa.

Algunas salidas dependen de la fecha del computador (requisito 9) o del azar
(requisito 3). Para ellas, los archivos usan estas marcas:
  {hoy}, {hoy-1}, {hoy+3}...   la fecha actual, más o menos esos días;
  {año:hoy-2}, {mes:hoy-2}, {dia:hoy-2}   (en las entradas) el año, el mes o el
                                día de esa fecha, para teclearlos;
  {faltan:2026-11-05}          la línea de días sin registrar de un registro
                                cuyo último día es esa fecha, según la regla
                                del requisito 9;
  re:<patrón>                  (al inicio de una línea esperada) una expresión
                                regular que la línea obtenida debe cumplir.

Uso, desde la carpeta del proyecto:
  python verificacion/verificar.py             verifica todos los casos
  python verificacion/verificar.py R03-02      verifica solo ese caso
  python verificacion/verificar.py R03-02 -v   y además muestra su pantalla
"""

import builtins
import io
import os
import re
import sys
from contextlib import redirect_stdout
from datetime import date, timedelta

CARPETA = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(CARPETA)
CARPETA_ENTRADAS = os.path.join(CARPETA, "entradas")
CARPETA_ESPERADAS = os.path.join(CARPETA, "esperadas")

# Las rutas de los casos (datos/...) son relativas a la carpeta del proyecto.
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
import user_interface  # noqa: E402  (debe importarse después de ajustar sys.path)

MARCA_FECHA = re.compile(r"\{hoy([+-]\d+)?\}")
MARCA_PARTE = re.compile(r"\{(año|mes|dia):hoy([+-]\d+)?\}")
MARCA_FALTAN = re.compile(r"^\{faltan:([^}]+)\}$")


def fecha_relativa(desplazamiento: str | None, hoy: date) -> date:
    if desplazamiento is None:
        return hoy
    return hoy + timedelta(days=int(desplazamiento))


def leer_fecha(texto: str, hoy: date) -> date:
    """Lee '2026-11-05' o 'hoy-2'."""
    if texto.startswith("hoy"):
        return fecha_relativa(texto[3:] or None, hoy)
    return date.fromisoformat(texto)


def texto_dias(cantidad: int) -> str:
    return "1 día" if cantidad == 1 else f"{cantidad} días"


def linea_faltan(ultimo: date, hoy: date) -> str:
    """La regla del requisito 9, escrita aquí aparte del programa: faltan los
    días desde el siguiente al último registrado hasta el anterior a hoy."""
    cantidad = (hoy - ultimo).days - 1
    if cantidad <= 0:
        return "El registro está al día."
    return (f"Días sin registrar: {texto_dias(cantidad)} "
            f"(del {ultimo + timedelta(days=1)} al {hoy - timedelta(days=1)})")


def expandir_entrada(linea: str, hoy: date) -> str:
    def parte(coincidencia):
        fecha = fecha_relativa(coincidencia.group(2), hoy)
        valores = {"año": fecha.year, "mes": fecha.month, "dia": fecha.day}
        return str(valores[coincidencia.group(1)])
    return MARCA_PARTE.sub(parte, linea)


def expandir_esperada(linea: str, hoy: date) -> str:
    faltan = MARCA_FALTAN.match(linea)
    if faltan:
        return linea_faltan(leer_fecha(faltan.group(1), hoy), hoy)
    # Lo tecleado aparece en la pantalla, así que también lleva las marcas.
    linea = expandir_entrada(linea, hoy)
    return MARCA_FECHA.sub(lambda c: str(fecha_relativa(c.group(1), hoy)), linea)


def leer_archivo(ruta: str) -> list:
    with open(ruta, encoding="utf-8") as archivo:
        return archivo.read().split("\n")[:-1]


def ejecutar(entradas: list) -> str:
    """Ejecuta el programa con esas entradas y devuelve lo que mostró."""
    pendientes = list(entradas)
    pantalla = io.StringIO()

    def teclado(pregunta=""):
        print(pregunta, end="")
        if len(pendientes) == 0:
            raise EOFError  # como cuando se acaba un archivo de entrada
        valor = pendientes.pop(0)
        print(valor)  # en la consola, lo tecleado se ve tras la pregunta
        return valor

    input_original = builtins.input
    builtins.input = teclado
    try:
        with redirect_stdout(pantalla):
            user_interface.main()
    finally:
        builtins.input = input_original
    return pantalla.getvalue()


def comparar(esperadas: list, obtenidas: list) -> str | None:
    """None si coinciden; si no, la descripción de la primera diferencia."""
    for i in range(max(len(esperadas), len(obtenidas))):
        esperada = esperadas[i] if i < len(esperadas) else "(fin de la salida)"
        obtenida = obtenidas[i] if i < len(obtenidas) else "(fin de la salida)"
        if esperada.startswith("re:"):
            iguales = re.fullmatch(esperada[3:], obtenida) is not None
        else:
            iguales = esperada == obtenida
        if not iguales:
            return (f"    línea {i + 1}\n"
                    f"    esperada: {esperada}\n"
                    f"    obtenida: {obtenida}")
    return None


def verificar_caso(caso: str, hoy: date, mostrar: bool) -> bool:
    entradas = [expandir_entrada(linea, hoy)
                for linea in leer_archivo(os.path.join(CARPETA_ENTRADAS, caso + ".txt"))]
    esperadas = [expandir_esperada(linea, hoy)
                 for linea in leer_archivo(os.path.join(CARPETA_ESPERADAS, caso + ".txt"))]
    obtenida = ejecutar(entradas)
    if mostrar:
        print(obtenida)
    diferencia = comparar(esperadas, obtenida.split("\n")[:-1])
    if diferencia is None:
        print(f"PASA   {caso}")
        return True
    print(f"FALLA  {caso}\n{diferencia}")
    return False


def main() -> None:
    # En Windows, una salida redirigida puede no aceptar caracteres como «５»;
    # se reemplazan en lugar de detener la verificación.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    argumentos = sys.argv[1:]
    mostrar = "-v" in argumentos
    pedidos = [a for a in argumentos if a != "-v"]
    todos = sorted(nombre[:-4] for nombre in os.listdir(CARPETA_ENTRADAS)
                   if nombre.endswith(".txt"))
    casos = pedidos if pedidos else todos
    hoy = date.today()
    print(f"Fecha de la verificación: {hoy}\n")
    fallidos = [caso for caso in casos if not verificar_caso(caso, hoy, mostrar)]
    print(f"\n{len(casos) - len(fallidos)} de {len(casos)} casos pasan.")
    if fallidos:
        print("Fallan: " + ", ".join(fallidos))
        sys.exit(1)


if __name__ == "__main__":
    main()
