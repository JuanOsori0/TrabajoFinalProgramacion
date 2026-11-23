from datetime import date

from business_logic import (
    MENSAJE_CARGA_CON_PLAYAS,
    MENSAJE_FIN_CALENDARIO,
    NIVELES,
    Cooperativa,
    Playa,
    convertir_entero,
    validar_dias_simulados,
    validar_minimo_maximo,
)

OPCION_CREAR = 1
OPCION_REGISTRAR = 2
OPCION_SIMULAR = 3
OPCION_INFORME = 4
OPCION_EXTREMOS = 5
OPCION_CARGAR = 6
OPCION_SALIR = 7


def texto_dias(cantidad: int) -> str:
    if cantidad == 1:
        return "1 día"
    return f"{cantidad} días"


def pedir_playa(cooperativa: Cooperativa) -> Playa | None:
    """Pide un nombre y devuelve la playa, o None (avisando) si no existe."""
    nombre = input("Nombre de la playa: ")
    playa = cooperativa.buscar(nombre)
    if playa is None:
        print("Error: no hay una playa con ese nombre.")
    return playa


def menu_crear(cooperativa: Cooperativa) -> None:
    print("\n--- Crear playa ---")
    nombre = input("Nombre de la playa: ")
    carpas = convertir_entero(input("Carpas instaladas: "))
    año = convertir_entero(input("Año de inicio del registro: "))
    mes = convertir_entero(input("Mes de inicio del registro: "))
    dia = convertir_entero(input("Día de inicio del registro: "))
    try:
        cooperativa.crear_playa(nombre, carpas, año, mes, dia)
        print("Playa creada, sin días registrados.")
    except ValueError as error:
        print(f"Error: {error}")


def menu_registrar(cooperativa: Cooperativa) -> None:
    print("\n--- Registrar el día siguiente ---")
    playa = pedir_playa(cooperativa)
    if playa is None:
        return

    fecha_siguiente = playa.fecha_siguiente()
    if fecha_siguiente is None:
        print(f"Error: {MENSAJE_FIN_CALENDARIO}")
        return

    print(f"Día que se va a registrar: {fecha_siguiente}")
    registrado = False
    while not registrado:
        carpas = convertir_entero(input("Carpas alquiladas: "))
        try:
            playa.registrar_dia(carpas)
            registrado = True
            print("Día registrado.")
        except ValueError as error:
            print(f"Error: {error}")


def menu_simular(cooperativa: Cooperativa) -> None:
    print("\n--- Simular días ---")
    playa = pedir_playa(cooperativa)
    if playa is None:
        return

    # Cada dato se valida apenas se lee; si uno falla, no se piden los demás.
    try:
        dias = convertir_entero(input("¿Cuántos días quieres simular? "))
        validar_dias_simulados(dias)
        minimo = convertir_entero(input("Mínimo de carpas alquiladas: "))
        playa.validar_carpas(minimo)
        maximo = convertir_entero(input("Máximo de carpas alquiladas: "))
        playa.validar_carpas(maximo)
        validar_minimo_maximo(minimo, maximo)
        playa.simular_dias(dias, minimo, maximo)
    except ValueError as error:
        print(f"Error: {error}")
        return

    if dias == 1:
        print(f"Se simuló 1 día para la playa {playa.nombre}.")
    else:
        print(f"Se simularon {dias} días para la playa {playa.nombre}.")


def menu_informe(cooperativa: Cooperativa) -> None:
    print("\n--- Informe de una playa ---")
    playa = pedir_playa(cooperativa)
    if playa is None:
        return

    informe = playa.informe(date.today())
    print(f"Playa: {informe['nombre']}")
    print(f"Carpas instaladas: {informe['carpas_instaladas']}")
    if informe["dias"] == 0:
        print("La playa no tiene días registrados.")
        return

    # El redondeo se hace aquí, al mostrar: la lógica entrega los valores sin redondear.
    print(f"Días registrados: {informe['dias']}")
    print(f"Alquileres totales: {informe['total']}")
    print(f"Promedio de carpas alquiladas por día: {round(informe['promedio'], 2)}")
    print(f"Porcentaje de alquiler: {round(informe['porcentaje'], 2)} %")
    print(f"Desviación estándar: {round(informe['desviacion'], 2)}")
    print(f"Día con más carpas alquiladas: {informe['fecha_maximo']}")
    print(f"Día con menos carpas alquiladas: {informe['fecha_minimo']}")
    for nivel in NIVELES:
        print(f"Días en nivel {nivel}: {informe['niveles'][nivel]}")

    racha = informe["racha"]
    if racha["longitud"] == 0:
        print("No hubo ningún día en nivel Agotado.")
    else:
        print(f"Racha más larga en nivel Agotado: {texto_dias(racha['longitud'])}, "
              f"empieza el {racha['inicio']}")

    print(f"Último día registrado: {informe['ultimo_dia']}")
    faltan = informe["faltan"]
    if faltan["cantidad"] == 0:
        print("El registro está al día.")
    else:
        print(f"Días sin registrar: {texto_dias(faltan['cantidad'])} "
              f"(del {faltan['primero']} al {faltan['ultimo']})")


def menu_extremos(cooperativa: Cooperativa) -> None:
    print("\n--- Playas con mayor y menor porcentaje de alquiler ---")
    extremos = cooperativa.extremos()
    if extremos is None:
        print("Ninguna playa tiene días registrados.")
        return
    mayor = extremos["mayor"]
    menor = extremos["menor"]
    print(f"Mayor porcentaje: {mayor.nombre}, "
          f"{round(mayor.porcentaje_alquiler(), 2)} %")
    print(f"Menor porcentaje: {menor.nombre}, "
          f"{round(menor.porcentaje_alquiler(), 2)} %")


def mostrar_descartadas(descartadas: list) -> None:
    for descartada in descartadas:
        print(f"Línea {descartada['linea']} descartada: {descartada['causa']}")


def menu_cargar(cooperativa: Cooperativa) -> None:
    print("\n--- Cargar desde archivos ---")
    if cooperativa.tiene_playas():
        print(f"Error: {MENSAJE_CARGA_CON_PLAYAS}")
        return

    # strip('"') quita las comillas que pone Windows al copiar una ruta.
    ruta = input("Ruta del archivo de playas: ").strip().strip('"')
    try:
        resultado = cooperativa.cargar_playas(ruta)
    except FileNotFoundError:
        # Va antes que OSError porque FileNotFoundError es un caso de OSError.
        print("Error: el archivo de playas no existe.")
        return
    except OSError:
        # Una carpeta o un archivo sin permiso de lectura.
        print("Error: no se pudo leer el archivo de playas.")
        return
    except UnicodeDecodeError:
        # Un archivo que no está en UTF-8.
        print("Error: no se pudo leer el archivo de playas.")
        return
    mostrar_descartadas(resultado["descartadas"])
    print(f"Playas cargadas: {resultado['cargadas']}")

    ruta = input("Ruta del archivo de alquileres: ").strip().strip('"')
    try:
        resultado = cooperativa.cargar_alquileres(ruta)
    except FileNotFoundError:
        print("Error: el archivo de alquileres no existe.")
        return
    except OSError:
        print("Error: no se pudo leer el archivo de alquileres.")
        return
    except UnicodeDecodeError:
        print("Error: no se pudo leer el archivo de alquileres.")
        return
    mostrar_descartadas(resultado["descartadas"])
    print(f"Días cargados: {resultado['cargados']}")


def mostrar_menu() -> None:
    print("\n=====================================")
    print(" Registro de carpas en las playas")
    print("=====================================")
    print("1. Crear playa")
    print("2. Registrar el día siguiente de una playa")
    print("3. Simular días de una playa")
    print("4. Informe de una playa")
    print("5. Playas con mayor y menor porcentaje de alquiler")
    print("6. Cargar playas y alquileres desde archivos")
    print("7. Salir")


def main() -> None:
    cooperativa = Cooperativa()
    salir = False

    # Ctrl+C, Ctrl+Z o el fin de un archivo de entrada redirigido cortan la
    # lectura en cualquier input(); el programa termina sin mostrar el error.
    try:
        while not salir:
            mostrar_menu()
            opcion = convertir_entero(input("Elige una opción: "))

            if opcion == OPCION_CREAR:
                menu_crear(cooperativa)
            elif opcion == OPCION_REGISTRAR:
                menu_registrar(cooperativa)
            elif opcion == OPCION_SIMULAR:
                menu_simular(cooperativa)
            elif opcion == OPCION_INFORME:
                menu_informe(cooperativa)
            elif opcion == OPCION_EXTREMOS:
                menu_extremos(cooperativa)
            elif opcion == OPCION_CARGAR:
                menu_cargar(cooperativa)
            elif opcion == OPCION_SALIR:
                print("Hasta luego.")
                salir = True
            else:
                print("Error: opción no válida.")
    except EOFError:
        # Se acabó la entrada: Ctrl+Z, Ctrl+D o el fin de un archivo redirigido.
        print("\nSe interrumpió la entrada. Hasta luego.")
    except KeyboardInterrupt:
        # Se presionó Ctrl+C.
        print("\nSe interrumpió la entrada. Hasta luego.")


if __name__ == "__main__":
    main()
