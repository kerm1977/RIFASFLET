import flet as ft
import sqlite3

DATABASE_NAME = "rifa.db"

def init_db():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    # Tabla de números
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS numeros (
            numero TEXT PRIMARY KEY,
            seleccionado INTEGER DEFAULT 0,
            nombre_persona TEXT DEFAULT ''
        )
    ''')
    
    # Tabla: Participantes para gestionar el estado de pago
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS participantes (
            nombre_persona TEXT PRIMARY KEY,
            pagado INTEGER DEFAULT 0 -- 0 para NO PAGADO, 1 para PAGADO
        )
    ''')

    # NUEVA TABLA: Configuracion para el valor del número y descripción de la rifa
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS configuracion (
            id INTEGER PRIMARY KEY DEFAULT 1, -- Solo una fila, con ID 1
            valor_numero INTEGER DEFAULT 0, 
            descripcion_rifa TEXT DEFAULT 'Descripción de la rifa aquí...'
        )
    ''')
    
    # Insertar una fila por defecto en configuracion si no existe
    cursor.execute("INSERT OR IGNORE INTO configuracion (id, valor_numero, descripcion_rifa) VALUES (1, 100, '¡Participa en esta emocionante rifa y gana un premio increíble!')")
    
    # Insertar números del 00 al 99 si la tabla de números está vacía
    for i in range(100):
        num_str = str(i).zfill(2)
        cursor.execute("INSERT OR IGNORE INTO numeros (numero) VALUES (?)", (num_str,))
    
    conn.commit()
    conn.close()

def get_numeros():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT numero, seleccionado, nombre_persona FROM numeros ORDER BY numero ASC")
    numeros = cursor.fetchall()
    conn.close()
    return numeros

def get_selected_numeros_by_person():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            n.nombre_persona, 
            GROUP_CONCAT(n.numero),
            p.pagado
        FROM 
            numeros n
        INNER JOIN 
            participantes p ON n.nombre_persona = p.nombre_persona
        WHERE 
            n.seleccionado = 1 AND n.nombre_persona != '' 
        GROUP BY 
            n.nombre_persona, p.pagado
        ORDER BY 
            n.nombre_persona ASC
    """)
    selected_data = cursor.fetchall()
    conn.close()
    return selected_data

# Obtener conteo de números vendidos/disponibles
def get_numeros_counts():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM numeros WHERE seleccionado = 1")
    vendidos = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM numeros WHERE seleccionado = 0")
    disponibles = cursor.fetchone()[0]
    conn.close()
    return vendidos, disponibles

def seleccionar_numero(numero, nombre_persona):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    cursor.execute("UPDATE numeros SET seleccionado = 1, nombre_persona = ? WHERE numero = ? AND seleccionado = 0", (nombre_persona, numero))
    cursor.execute("INSERT OR IGNORE INTO participantes (nombre_persona, pagado) VALUES (?, 0)", (nombre_persona,))
    
    conn.commit()
    conn.close()

def reset_rifa_db():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE numeros SET seleccionado = 0, nombre_persona = ''")
    cursor.execute("DELETE FROM participantes")
    conn.commit()
    conn.close()

def clear_numeros_by_person_db(nombre_persona_a_limpiar):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE numeros SET seleccionado = 0, nombre_persona = '' WHERE nombre_persona = ?", (nombre_persona_a_limpiar,))
    cursor.execute("DELETE FROM participantes WHERE nombre_persona = ?", (nombre_persona_a_limpiar,))
    conn.commit()
    conn.close()

def get_winner_by_number(winning_number):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT nombre_persona FROM numeros WHERE numero = ? AND seleccionado = 1", (winning_number,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def update_pago_status_db(nombre_persona, pagado_status):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE participantes SET pagado = ? WHERE nombre_persona = ?", (pagado_status, nombre_persona))
    conn.commit()
    conn.close()

def get_configuracion_db():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT valor_numero, descripcion_rifa FROM configuracion WHERE id = 1")
    config = cursor.fetchone()
    conn.close()
    return config if config else (0, 'Descripción de la rifa aquí...')

def update_configuracion_db(valor_numero, descripcion_rifa):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE configuracion SET valor_numero = ?, descripcion_rifa = ? WHERE id = 1", (valor_numero, descripcion_rifa))
    conn.commit()
    conn.close()

def main(page: ft.Page):
    page.title = "Aplicación de Rifa Flet"
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.window_min_width = 700
    page.window_min_height = 600

    init_db()

    global current_valor_numero, current_descripcion_rifa
    current_valor_numero, current_descripcion_rifa = get_configuracion_db()

    nombre_input = ft.TextField(
        label="Tu Nombre (requerido para seleccionar)",
        width=300,
        hint_text="Ingresa tu nombre aquí",
        on_change=lambda e: actualizar_ui()
    )
    mensaje_error = ft.Text("", color=ft.Colors.RED_500)

    liberar_mensaje_error = ft.Text("", color=ft.Colors.ORANGE_500)
    
    def limpiar_liberar_mensaje(e):
        liberar_mensaje_error.value = ""
        page.update()

    nombre_a_liberar_input = ft.TextField(
        label="Nombre a liberar (exacto)",
        width=300,
        hint_text="Ej: Juan Pérez",
        on_change=limpiar_liberar_mensaje,
        expand=True
    )
    
    numeros_grid_view = ft.GridView(
        runs_count=5,
        max_extent=150,
        child_aspect_ratio=1.5,
        spacing=10,
        run_spacing=10,
        expand=True,
    )

    lista_seleccionados_column = ft.Column(
        controls=[],
        scroll=ft.ScrollMode.ADAPTIVE,
        horizontal_alignment=ft.CrossAxisAlignment.START,
        expand=True
    )

    valor_numero_input = ft.TextField(
        label="Valor de cada número",
        value=str(int(current_valor_numero)),
        prefix_text="¢",
        input_filter=ft.InputFilter(allow=True, regex_string=r"^[0-9]*$"), 
        width=200,
        on_change=lambda e: actualizar_valor_input_temp(e),
        on_submit=lambda e: guardar_configuracion(e, "valor_numero")
    )

    descripcion_rifa_input = ft.TextField(
        label="Descripción de la Rifa",
        value=current_descripcion_rifa,
        multiline=True,
        min_lines=3,
        max_lines=5,
        width=400,
        hint_text="Describe el premio, las reglas, etc.",
        on_change=lambda e: guardar_configuracion(e, "descripcion_rifa")
    )
    
    display_descripcion_rifa = ft.Text(current_descripcion_rifa, size=14, italic=True, color=ft.Colors.BLUE_GREY_700, text_align=ft.TextAlign.CENTER)

    # Controles para mostrar los conteos
    vendidos_text = ft.Text("Vendidos: 0", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_700)
    disponibles_text = ft.Text("Disponibles: 100", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.RED_700)
    
    def actualizar_valor_input_temp(e):
        valor_numero_input.value = e.control.value
        valor_numero_input.error_text = None 
        page.update()


    def guardar_configuracion(e, campo):
        global current_valor_numero, current_descripcion_rifa
        try:
            if campo == "valor_numero":
                if not valor_numero_input.value.strip():
                    val = 0
                else:
                    val = int(valor_numero_input.value)
                
                current_valor_numero = val
                valor_numero_input.value = str(val)
                valor_numero_input.error_text = None
                
            elif campo == "descripcion_rifa":
                current_descripcion_rifa = descripcion_rifa_input.value
            
            update_configuracion_db(current_valor_numero, current_descripcion_rifa)
            display_descripcion_rifa.value = current_descripcion_rifa
            actualizar_numeros_ui() 
            page.update()
        except ValueError:
            valor_numero_input.error_text = "Valor inválido. Debe ser un número entero."
            page.update()

    def actualizar_numeros_ui():
        numeros_grid_view.controls.clear()
        todos_los_numeros = get_numeros()
        
        current_nombre = nombre_input.value.strip()

        for num_str, seleccionado, nombre_persona in todos_los_numeros:
            card_content = [
                ft.Text(f"Número: {num_str}", size=18, weight=ft.FontWeight.BOLD),
                ft.Text(f"¢{current_valor_numero}", size=12, color=ft.Colors.INDIGO_700, weight=ft.FontWeight.W_600),
            ]
            
            card_color = ft.Colors.BLUE_GREY_100
            is_clickable = True

            if seleccionado:
                card_content.append(ft.Text(f"Por: {nombre_persona}", size=12, color=ft.Colors.GREEN_700))
                card_color = ft.Colors.GREY_300
                is_clickable = False
            else:
                card_content.append(ft.Text("Disponible", size=12, color=ft.Colors.GREY_500))
                if not current_nombre:
                    is_clickable = False
                    card_color = ft.Colors.BLUE_GREY_50
                    card_content.append(ft.Text("(Ingresa tu nombre)", size=10, color=ft.Colors.AMBER_700))

            def on_numero_click(e, numero=num_str):
                if not is_clickable:
                    if not current_nombre:
                        mensaje_error.value = "Por favor, ingresa tu nombre para seleccionar un número."
                        page.update()
                    elif seleccionado:
                        mensaje_error.value = f"El número {numero} ya fue seleccionado por {nombre_persona}."
                        page.update()
                    return

                seleccionar_numero(numero, current_nombre)
                mensaje_error.value = ""
                actualizar_ui() # Esto actualizará también los conteos
                page.update()

            numero_card = ft.Card(
                content=ft.Container(
                    content=ft.Column(card_content, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    alignment=ft.alignment.center,
                    width=120,
                    height=80,
                    padding=10,
                    bgcolor=card_color,
                    border_radius=ft.border_radius.all(10),
                    on_click=on_numero_click if is_clickable else None,
                    ink=is_clickable,
                    tooltip=f"Selecciona el {num_str}" if is_clickable else (f"Seleccionado por {nombre_persona}" if seleccionado else "Ingresa tu nombre para seleccionar")
                ),
                elevation=3 if is_clickable else 1
            )
            numeros_grid_view.controls.append(numero_card)
        page.update()

    def actualizar_lista_seleccionados_ui():
        lista_seleccionados_column.controls.clear()
        selected_data = get_selected_numeros_by_person() 

        if not selected_data:
            lista_seleccionados_column.controls.append(
                ft.Text("Aún no hay números seleccionados.", italic=True, color=ft.Colors.GREY_500)
            )
        else:
            for nombre, numeros_concatenados, pagado_status in selected_data:
                numeros_formateados = numeros_concatenados.replace(",", ", ")

                def on_radio_change(e, persona_nombre=nombre):
                    nuevo_estado = int(e.control.value) 
                    update_pago_status_db(persona_nombre, nuevo_estado)

                radio_group_pago = ft.RadioGroup(
                    value=str(pagado_status),
                    on_change=on_radio_change,
                    content=ft.Row([
                        ft.Radio(value="1", label="Pagó"),
                        ft.Radio(value="0", label="No pagó"),
                    ], spacing=10)
                )

                lista_seleccionados_column.controls.append(
                    ft.Card(
                        content=ft.Container(
                            content=ft.Column([
                                ft.Row([
                                    ft.Text(f"{nombre}:", size=14, weight=ft.FontWeight.BOLD, expand=True),
                                    ft.Text(numeros_formateados, size=14, color=ft.Colors.BLUE_GREY_900)
                                ], vertical_alignment=ft.CrossAxisAlignment.START),
                                ft.Row([
                                    ft.Text("Estado de Pago:", size=12, color=ft.Colors.GREY_700),
                                    radio_group_pago
                                ], alignment=ft.MainAxisAlignment.END, spacing=5)
                            ]),
                            padding=10,
                            bgcolor=ft.Colors.BLUE_GREY_50,
                            border_radius=ft.border_radius.all(8)
                        ),
                        elevation=1,
                        margin=ft.margin.only(bottom=10),
                        width=600
                    )
                )
        page.update()

    # Función para actualizar solo los conteos
    def actualizar_conteo_numeros_ui():
        vendidos, disponibles = get_numeros_counts()
        vendidos_text.value = f"Vendidos: {vendidos}"
        disponibles_text.value = f"Disponibles: {disponibles}"
        # CORRECCIÓN AQUÍ: Pasar los controles como argumentos separados
        page.update(vendidos_text, disponibles_text) 


    def actualizar_ui():
        global current_valor_numero, current_descripcion_rifa
        current_valor_numero, current_descripcion_rifa = get_configuracion_db()
        valor_numero_input.value = str(int(current_valor_numero)) 
        descripcion_rifa_input.value = current_descripcion_rifa
        display_descripcion_rifa.value = current_descripcion_rifa
        
        actualizar_numeros_ui()
        actualizar_lista_seleccionados_ui()
        actualizar_conteo_numeros_ui() # Llamar a la función para actualizar conteos
        page.update() # Se deja aquí una actualización general por si otros elementos necesitan refrescarse

    def close_reset_dialog(e):
        reset_alert_dialog.open = False
        page.update()

    def perform_reset_and_close_dialog(e):
        reset_rifa_db()
        actualizar_ui()
        mensaje_error.value = "La rifa ha sido reseteada."
        nombre_input.value = ""
        reset_alert_dialog.open = False
        page.update()

    reset_alert_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Confirmar Reseteo Total"),
        content=ft.Text("¿Estás seguro de que deseas resetear la rifa? Esto borrará TODAS las selecciones de TODOS los participantes."),
        actions=[
            ft.TextButton("Cancelar", on_click=close_reset_dialog),
            ft.FilledButton("Sí, Resetear Todo", on_click=perform_reset_and_close_dialog, style=ft.ButtonStyle(bgcolor=ft.Colors.RED_500)),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
        on_dismiss=lambda e: print("Diálogo de confirmación de reset total cerrado por dismiss."),
    )
    page.overlay.append(reset_alert_dialog)
    
    def on_reset_button_click(e):
        print("Botón de reset total clickeado! Intentando abrir diálogo...")
        reset_alert_dialog.open = True
        page.update()

    reset_button_final = ft.ElevatedButton(
        "Resetear Rifa Completa",
        on_click=on_reset_button_click,
        icon=ft.Icons.WARNING_ROUNDED,
        style=ft.ButtonStyle(
            bgcolor=ft.Colors.RED_700,
            color=ft.Colors.WHITE,
            icon_color=ft.Colors.WHITE,
        )
    )

    def close_liberar_dialog(e):
        liberar_por_contacto_alert_dialog.open = False
        page.update()

    def perform_liberar_by_contact_and_close_dialog(e):
        nombre = nombre_a_liberar_input.value.strip()
        if not nombre:
            liberar_mensaje_error.value = "Error interno: Nombre no proporcionado."
            page.update()
            return

        clear_numeros_by_person_db(nombre)
        actualizar_ui()
        liberar_mensaje_error.value = f"Números de '{nombre}' liberados correctamente."
        nombre_a_liberar_input.value = ""
        liberar_por_contacto_alert_dialog.open = False
        page.update()

    liberar_por_contacto_alert_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Confirmar Liberar Números"),
        content=ft.Text(""),
        actions=[
            ft.TextButton("Cancelar", on_click=close_liberar_dialog),
            ft.FilledButton("Sí, Liberar", on_click=perform_liberar_by_contact_and_close_dialog, style=ft.ButtonStyle(bgcolor=ft.Colors.ORANGE_500)),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
        on_dismiss=lambda e: print("Diálogo de confirmación de liberar por contacto cerrado."),
    )
    page.overlay.append(liberar_por_contacto_alert_dialog)

    def on_liberar_by_contact_button_click(e):
        nombre = nombre_a_liberar_input.value.strip()
        if not nombre:
            liberar_mensaje_error.value = "Ingresa el nombre del participante para liberar sus números."
            page.update()
            return
        
        liberar_por_contacto_alert_dialog.content = ft.Text(f"¿Estás seguro de que deseas liberar los números de '{nombre}'? Esto eliminará sus selecciones.")
        liberar_por_contacto_alert_dialog.open = True
        page.update()

    liberar_por_contacto_button = ft.ElevatedButton(
        "Liberar números de Contacto",
        on_click=on_liberar_by_contact_button_click,
        icon=ft.Icons.CLEANING_SERVICES,
        style=ft.ButtonStyle(
            bgcolor=ft.Colors.BLUE_GREY_600,
            color=ft.Colors.WHITE,
            icon_color=ft.Colors.WHITE,
        ),
        expand=True
    )

    resultado_ganador_text = ft.Text("", size=18, weight=ft.FontWeight.BOLD)
    
    def limpiar_resultado_ganador_mensaje(e):
        resultado_ganador_text.value = ""
        resultado_ganador_text.color = ft.Colors.BLACK
        page.update()

    numero_ganador_input = ft.TextField(
        label="Número Ganador (00-99)",
        width=200,
        hint_text="Ej: 42",
        input_filter=ft.InputFilter(allow=True, regex_string=r"^[0-9]{0,2}$"),
        on_change=limpiar_resultado_ganador_mensaje,
        expand=True
    )
    
    def anunciar_ganador(e):
        numero = numero_ganador_input.value.strip()
        if not numero:
            resultado_ganador_text.value = "Por favor, ingresa un número ganador."
            resultado_ganador_text.color = ft.Colors.RED_500
        elif not (numero.isdigit() and 0 <= int(numero) <= 99):
            resultado_ganador_text.value = "Número inválido. Debe ser entre 00 y 99."
            resultado_ganador_text.color = ft.Colors.RED_500
        else:
            formatted_numero = str(int(numero)).zfill(2)
            ganador = get_winner_by_number(formatted_numero)
            
            if ganador:
                resultado_ganador_text.value = f"¡Felicidades, {ganador}!"
                resultado_ganador_text.color = ft.Colors.GREEN_700
            else:
                resultado_ganador_text.value = f"El número {formatted_numero} no ha sido seleccionado."
                resultado_ganador_text.color = ft.Colors.AMBER_700
        page.update()

    anunciar_ganador_button = ft.ElevatedButton(
        "Anunciar Ganador",
        on_click=anunciar_ganador,
        icon=ft.Icons.STAR,
        style=ft.ButtonStyle(
            bgcolor=ft.Colors.PURPLE_600,
            color=ft.Colors.WHITE,
            icon_color=ft.Colors.YELLOW_ACCENT_100,
        ),
        expand=True
    )

    page.add(
        ft.Column(
            [
                ft.Text("¡Bienvenido a la Aplicación de Rifa!", size=28, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text("Configuración de la Rifa", size=20, weight=ft.FontWeight.BOLD),
                            ft.Row(
                                [
                                    valor_numero_input,
                                    ft.Container(width=20),
                                    ft.Column([
                                        ft.Text("Descripción de la Rifa Actual:", size=12, color=ft.Colors.GREY_700),
                                        display_descripcion_rifa,
                                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True)
                                ],
                                alignment=ft.MainAxisAlignment.CENTER,
                                spacing=15
                            ),
                            descripcion_rifa_input,
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=10,
                        alignment=ft.CrossAxisAlignment.CENTER,
                        width=ft.WEB_BROWSER,
                    ),
                    padding=ft.padding.only(top=10, bottom=10, left=15, right=15),
                    margin=ft.margin.only(top=10, bottom=20),
                    bgcolor=ft.Colors.BLUE_GREY_50,
                    border_radius=ft.border_radius.all(10),
                    border=ft.border.all(1, ft.Colors.BLUE_GREY_200)
                ),
                ft.Divider(),
                ft.Text("Ingresa tu nombre y selecciona un número para participar.", size=16),
                ft.Row(
                    [nombre_input],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=20
                ),
                mensaje_error,
                ft.Container(
                    content=numeros_grid_view,
                    alignment=ft.alignment.center,
                    expand=True,
                    padding=ft.padding.only(top=20, bottom=20, left=5, right=5),
                    bgcolor=ft.Colors.WHITE,
                    width=ft.WEB_BROWSER
                ),
                ft.Divider(),
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text("Números Seleccionados", size=20, weight=ft.FontWeight.BOLD),
                            ft.Divider(),
                            lista_seleccionados_column,
                            # AÑADIDO: Contadores de números vendidos y disponibles
                            ft.Divider(), # Separador visual
                            ft.Row(
                                [
                                    vendidos_text,
                                    disponibles_text
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_AROUND,
                                spacing=20
                            )
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=10
                    ),
                    padding=ft.padding.only(top=10, bottom=20, left=15, right=15),
                    bgcolor=ft.Colors.BLUE_GREY_50,
                    width=ft.WEB_BROWSER,
                    margin=ft.margin.only(top=20)
                ),
                ft.Divider(),
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text("Administración de Números", size=20, weight=ft.FontWeight.BOLD),
                            ft.Text("Libera los números de un participante específico:", size=14),
                            ft.ResponsiveRow(
                                [
                                    ft.Column([nombre_a_liberar_input], col={"xs": 12, "md": 6}),
                                    ft.Column([liberar_por_contacto_button], col={"xs": 12, "md": 6}),
                                ],
                                alignment=ft.MainAxisAlignment.CENTER,
                                spacing=15
                            ),
                            liberar_mensaje_error,
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=10,
                        alignment=ft.CrossAxisAlignment.CENTER,
                        width=ft.WEB_BROWSER,
                    ),
                    padding=ft.padding.only(top=10, bottom=10, left=15, right=15),
                    margin=ft.margin.only(top=20),
                    bgcolor=ft.Colors.BLUE_GREY_100,
                    border_radius=ft.border_radius.all(10)
                ),
                ft.Divider(),
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text("Anunciar Ganador", size=20, weight=ft.FontWeight.BOLD),
                            ft.Text("Ingresa el número ganador para ver quién lo tiene:", size=14),
                            ft.ResponsiveRow(
                                [
                                    ft.Column([numero_ganador_input], col={"xs": 12, "md": 6}),
                                    ft.Column([anunciar_ganador_button], col={"xs": 12, "md": 6}),
                                ],
                                alignment=ft.MainAxisAlignment.CENTER,
                                spacing=15
                            ),
                            resultado_ganador_text,
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=10,
                        alignment=ft.CrossAxisAlignment.CENTER,
                        width=ft.WEB_BROWSER,
                    ),
                    padding=ft.padding.only(top=10, bottom=10, left=15, right=15),
                    margin=ft.margin.only(top=20),
                    bgcolor=ft.Colors.LIGHT_GREEN_50,
                    border_radius=ft.border_radius.all(10),
                    border=ft.border.all(2, ft.Colors.LIGHT_GREEN_200)
                ),
                ft.Divider(),
                reset_button_final,
                ft.Container(height=20)
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.START,
            expand=True,
            scroll=ft.ScrollMode.ADAPTIVE
        )
    )

    def on_page_resize(e):
        page.update()
    page.on_resize = on_page_resize

    actualizar_ui()

if __name__ == "__main__":
    ft.app(target=main)