import flet as ft
import sqlite3

DATABASE_NAME = "rifa.db"

def init_db():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS numeros (
            numero TEXT PRIMARY KEY,
            seleccionado INTEGER DEFAULT 0,
            nombre_persona TEXT DEFAULT ''
        )
    ''')
    # Insertar números del 00 al 99 si la tabla está vacía
    for i in range(100):
        num_str = str(i).zfill(2) # Formatea a dos dígitos (00, 01, ..., 99)
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
    cursor.execute("SELECT nombre_persona, GROUP_CONCAT(numero) FROM numeros WHERE seleccionado = 1 AND nombre_persona != '' GROUP BY nombre_persona ORDER BY nombre_persona ASC")
    selected_data = cursor.fetchall()
    conn.close()
    return selected_data

def seleccionar_numero(numero, nombre_persona):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor() # <--- ¡CORRECCIÓN APLICADA AQUÍ!
    cursor.execute("UPDATE numeros SET seleccionado = 1, nombre_persona = ? WHERE numero = ? AND seleccionado = 0", (nombre_persona, numero))
    conn.commit()
    conn.close()

def reset_rifa_db():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE numeros SET seleccionado = 0, nombre_persona = ''")
    conn.commit()
    conn.close()

def main(page: ft.Page):
    page.title = "Aplicación de Rifa Flet"
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.window_min_width = 700
    page.window_min_height = 600

    init_db()

    nombre_input = ft.TextField(
        label="Tu Nombre (requerido para seleccionar)",
        width=300,
        hint_text="Ingresa tu nombre aquí",
        on_change=lambda e: actualizar_ui()
    )
    mensaje_error = ft.Text("", color=ft.Colors.RED_500)

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

    def actualizar_numeros_ui():
        numeros_grid_view.controls.clear()
        todos_los_numeros = get_numeros()
        
        current_nombre = nombre_input.value.strip()

        for num_str, seleccionado, nombre_persona in todos_los_numeros:
            card_content = [
                ft.Text(f"Número: {num_str}", size=18, weight=ft.FontWeight.BOLD),
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
                actualizar_ui()
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
            for nombre, numeros_concatenados in selected_data:
                numeros_formateados = numeros_concatenados.replace(",", ", ")
                lista_seleccionados_column.controls.append(
                    ft.Card(
                        content=ft.Container(
                            content=ft.Row([
                                ft.Text(f"{nombre}:", size=14, weight=ft.FontWeight.BOLD, expand=True),
                                ft.Text(numeros_formateados, size=14, color=ft.Colors.BLUE_GREY_900)
                            ], vertical_alignment=ft.CrossAxisAlignment.START),
                            padding=10,
                            bgcolor=ft.Colors.BLUE_GREY_50,
                            border_radius=ft.border_radius.all(8)
                        ),
                        elevation=1,
                        margin=ft.margin.only(bottom=5),
                        width=600
                    )
                )
        page.update()

    def actualizar_ui():
        actualizar_numeros_ui()
        actualizar_lista_seleccionados_ui()
        page.update()

    # --- Diálogo de Confirmación para Resetear Rifa (Usando page.overlay) ---

    def close_dialog(e):
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
        title=ft.Text("Confirmar Reseteo"),
        content=ft.Text("¿Estás seguro de que deseas resetear la rifa? Esto borrará todas las selecciones."),
        actions=[
            ft.TextButton("Cancelar", on_click=close_dialog),
            ft.FilledButton("Sí, Resetear", on_click=perform_reset_and_close_dialog, style=ft.ButtonStyle(bgcolor=ft.Colors.RED_500)),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
        on_dismiss=lambda e: print("Diálogo de confirmación cerrado por dismiss."),
    )

    page.overlay.append(reset_alert_dialog)
    
    def on_reset_button_click(e):
        print("Botón de reset clickeado! Intentando abrir diálogo...")
        reset_alert_dialog.open = True
        page.update()

    reset_button_final = ft.ElevatedButton(
        "Resetear Rifa",
        on_click=on_reset_button_click,
        icon=ft.Icons.WARNING_ROUNDED,
        style=ft.ButtonStyle(
            bgcolor=ft.Colors.RED_700,
            color=ft.Colors.WHITE,
            icon_color=ft.Colors.WHITE,
        )
    )

    page.add(
        ft.Column(
            [
                ft.Text("¡Bienvenido a la Aplicación de Rifa!", size=28, weight=ft.FontWeight.BOLD),
                ft.Text("Ingresa tu nombre y selecciona un número para participar.", size=16),
                ft.Divider(),
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
                            lista_seleccionados_column
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