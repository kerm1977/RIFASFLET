import flet as ft
import sqlite3
import os
import hashlib # Importar la librería hashlib

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

def get_numeros_counts():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM numeros WHERE seleccionado = 1")
    vendidos = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM numeros WHERE seleccionado = 0")
    disponibles = cursor.fetchone()[0]
    conn.close()
    return vendidos, disponibles

def seleccionar_o_deseleccionar_numero(numero, nombre_persona_actual, estado_actual_numero, nombre_seleccionado_por):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    if estado_actual_numero == 0:  # Número disponible, intentando seleccionar
        if nombre_persona_actual:
            cursor.execute("UPDATE numeros SET seleccionado = 1, nombre_persona = ? WHERE numero = ?", (nombre_persona_actual, numero))
            cursor.execute("INSERT OR IGNORE INTO participantes (nombre_persona, pagado) VALUES (?, 0)", (nombre_persona_actual,))
            conn.commit()
            conn.close()
            return True
        else:
            conn.close()
            return False
    elif estado_actual_numero == 1:  # Número seleccionado, intentando deseleccionar
        if nombre_persona_actual == nombre_seleccionado_por:
            cursor.execute("UPDATE numeros SET seleccionado = 0, nombre_persona = '' WHERE numero = ?", (numero,))
            
            cursor.execute("SELECT COUNT(*) FROM numeros WHERE nombre_persona = ?", (nombre_persona_actual,))
            remaining_numbers = cursor.fetchone()[0]
            if remaining_numbers == 0:
                cursor.execute("DELETE FROM participantes WHERE nombre_persona = ?", (nombre_persona_actual,))
            
            conn.commit()
            conn.close()
            return True
        else:
            conn.close()
            return False
    conn.close()
    return False


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

def debug_list_all_numeros():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT numero, seleccionado, nombre_persona FROM numeros ORDER BY numero ASC")
    all_numeros = cursor.fetchall()
    conn.close()
    print("\n--- Contenido actual de la tabla 'numeros' en la DB ---")
    if not all_numeros:
        print("La tabla 'numeros' está vacía.")
    else:
        for num, sel, name in all_numeros:
            print(f"Número: {num}, Seleccionado: {sel}, Por: {name if name else 'N/A'}")
    print(f"Total de números en la DB: {len(all_numeros)}")
    print("---------------------------------------------------\n")


def main(page: ft.Page):
    page.title = "Aplicación de Rifa Flet"
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.window_min_width = 700
    page.window_min_height = 600

    init_db()
    debug_list_all_numeros() 

    global current_valor_numero, current_descripcion_rifa
    current_valor_numero, current_descripcion_rifa = get_configuracion_db()

    ADMIN_EMAILS = [
        "kenth1977@gmail.com", 
        "jceciliano69@gmail.com", 
        "lthikingcr@gmail.com"
    ]
    # Contraseña pre-encriptada (hash SHA256 de "CR129x7848n")
    # Puedes generar este hash ejecutando:
    # import hashlib
    # print(hashlib.sha256("CR129x7848n".encode()).hexdigest())
    ADMIN_PASSWORD_HASH = "8f96e2329244081c7f999f193f2f0b957635c34510b64d1f5e8f52077e69c73a" # Hash de CR129x7848n
    
    is_admin_logged_in = False

    admin_email_input = ft.TextField(
        label="Correo del Administrador (Opcional)",
        hint_text="Ingresa tu correo o la contraseña",
        width=300,
        can_reveal_password=False # No revelar, es un correo
    )
    admin_password_input = ft.TextField(
        label="Contraseña (Opcional)",
        hint_text="Ingresa la contraseña para acceder",
        password=True, # Oculta los caracteres
        can_reveal_password=True, # Permite ver la contraseña si el usuario hace click
        width=300
    )
    admin_login_message = ft.Text("", color=ft.Colors.RED_500)

    # --- CONTROLES DE CONFIGURACIÓN ---
    valor_numero_input = ft.TextField(
        label="Valor de cada número",
        value=str(int(current_valor_numero)),
        prefix_text="¢",
        input_filter=ft.InputFilter(allow=True, regex_string=r"^[0-9]*$"), 
        width=200,
        on_submit=lambda e: guardar_configuracion(e, "valor_numero"), # Guarda cuando se presiona Enter
        on_blur=lambda e: guardar_configuracion(e, "valor_numero"),   # Guarda cuando el campo pierde el foco
        visible=False
    )
    display_valor_numero = ft.Text(
        f"Valor del número: ¢{current_valor_numero}", 
        size=18, 
        weight=ft.FontWeight.BOLD, 
        color=ft.Colors.INDIGO_800,
        visible=True
    )

    descripcion_rifa_input = ft.TextField(
        label="Descripción de la Rifa",
        value=current_descripcion_rifa,
        multiline=True,
        min_lines=3,
        max_lines=5,
        width=400,
        hint_text="Describe el premio, las reglas, etc.",
        on_change=lambda e: guardar_configuracion(e, "descripcion_rifa"), # Guarda en cada cambio para descripción
        visible=False
    )
    display_descripcion_rifa = ft.Text(
        current_descripcion_rifa, 
        size=14, 
        italic=True, 
        color=ft.Colors.BLUE_GREY_700, 
        text_align=ft.TextAlign.CENTER,
        visible=True
    )

    config_admin_controls = ft.Column(
        [
            ft.Text("Editar Configuración", size=20, weight=ft.FontWeight.BOLD),
            ft.Row(
                [
                    valor_numero_input,
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
        visible=False
    )

    def verify_admin_email_or_password(e):
        nonlocal is_admin_logged_in
        entered_email = admin_email_input.value.strip().lower()
        entered_password = admin_password_input.value.strip()

        # Generar el hash de la contraseña ingresada
        entered_password_hash = hashlib.sha256(entered_password.encode()).hexdigest()

        # Lógica de autenticación: El correo es correcto O la contraseña es correcta
        is_email_correct = entered_email in ADMIN_EMAILS
        is_password_correct = entered_password_hash == ADMIN_PASSWORD_HASH

        if is_email_correct or is_password_correct:
            is_admin_logged_in = True
            admin_login_message.value = "Acceso de administrador concedido."
            admin_login_message.color = ft.Colors.GREEN_700
            
            config_admin_controls.visible = True
            valor_numero_input.visible = True
            descripcion_rifa_input.visible = True
            display_valor_numero.visible = False
            display_descripcion_rifa.visible = False

            admin_email_input.visible = False
            admin_password_input.visible = False
            admin_login_button.visible = False
            admin_logout_button.visible = True
        else:
            is_admin_logged_in = False
            admin_login_message.value = "Correo o contraseña incorrectos."
            admin_login_message.color = ft.Colors.RED_500
            
            config_admin_controls.visible = False
            valor_numero_input.visible = False
            descripcion_rifa_input.visible = False
            display_valor_numero.visible = True
            display_descripcion_rifa.visible = True

        page.update()

    def admin_logout(e):
        nonlocal is_admin_logged_in
        is_admin_logged_in = False
        admin_email_input.value = ""
        admin_password_input.value = "" # Limpiar el campo de contraseña al cerrar sesión
        admin_login_message.value = "Sesión de administrador cerrada."
        admin_login_message.color = ft.Colors.BLACK54
        
        config_admin_controls.visible = False
        valor_numero_input.visible = False
        descripcion_rifa_input.visible = False
        display_valor_numero.visible = True
        display_descripcion_rifa.visible = True

        admin_email_input.visible = True
        admin_password_input.visible = True
        admin_login_button.visible = True
        admin_logout_button.visible = False
        page.update()

    admin_login_button = ft.ElevatedButton(
        "Acceder a Configuración",
        on_click=verify_admin_email_or_password,
        icon=ft.Icons.LOCK
    )
    admin_logout_button = ft.FilledButton(
        "Cerrar Sesión Admin",
        on_click=admin_logout,
        icon=ft.Icons.LOCK_OPEN,
        visible=False,
        style=ft.ButtonStyle(bgcolor=ft.Colors.AMBER_700)
    )

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
    
    vendidos_text = ft.Text("Vendidos: 0", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_700)
    disponibles_text = ft.Text("Disponibles: 100", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.RED_700)
    
    def guardar_configuracion(e, campo):
        if not is_admin_logged_in:
            admin_login_message.value = "Acceso denegado. Debes iniciar sesión como administrador para modificar la configuración."
            admin_login_message.color = ft.Colors.RED_500
            page.update(admin_login_message)
            return

        global current_valor_numero, current_descripcion_rifa
        try:
            if campo == "valor_numero":
                # Asegúrate de tomar el valor actual del input, no del 'e.control.value' directamente,
                # ya que 'on_blur' o 'on_submit' podrían tener 'e.control' como el TextField mismo.
                val_str = valor_numero_input.value.strip() # Accede directamente al .value del TextField
                if not val_str:
                    val = 0
                else:
                    val = int(val_str)
                
                current_valor_numero = val
                valor_numero_input.value = str(val) # Aseguramos que el valor se mantenga formateado en el input
                valor_numero_input.error_text = None
                
            elif campo == "descripcion_rifa":
                current_descripcion_rifa = descripcion_rifa_input.value
            
            update_configuracion_db(current_valor_numero, current_descripcion_rifa)
            
            # ¡Esta es la clave! Llamar a actualizar_ui() para refrescar todo lo que depende de la configuración.
            actualizar_ui() 
            # No necesitamos page.update() aquí porque actualizar_ui ya lo hace.
        except ValueError:
            valor_numero_input.error_text = "Valor inválido. Debe ser un número entero."
            page.update()

    def actualizar_numeros_ui():
        numeros_grid_view.controls.clear() 
        todos_los_numeros = get_numeros()
        
        current_nombre = nombre_input.value.strip()

        for num_str, seleccionado, nombre_persona_del_db in todos_los_numeros:
            card_content = [
                ft.Text(f"Número: {num_str}", size=18, weight=ft.FontWeight.BOLD),
                ft.Text(f"¢{current_valor_numero}", size=12, color=ft.Colors.INDIGO_700, weight=ft.FontWeight.W_600), # Usa current_valor_numero
            ]
            
            card_color = ft.Colors.BLUE_GREY_100
            is_clickable = True 
            tooltip_text = ""

            if seleccionado:
                card_content.append(ft.Text(f"Por: {nombre_persona_del_db}", size=12, color=ft.Colors.GREEN_700))
                tooltip_text = f"Seleccionado por {nombre_persona_del_db}"

                if current_nombre == nombre_persona_del_db:
                    card_color = ft.Colors.AMBER_100
                    tooltip_text = f"Clic para deseleccionar {num_str}"
                else:
                    is_clickable = False
                    card_color = ft.Colors.RED_100
                    
            else:
                card_content.append(ft.Text("Disponible", size=12, color=ft.Colors.GREY_500))
                if not current_nombre:
                    is_clickable = False
                    card_color = ft.Colors.BLUE_GREY_50
                    card_content.append(ft.Text("(Ingresa tu nombre)", size=10, color=ft.Colors.AMBER_700))
                    tooltip_text = "Ingresa tu nombre para seleccionar"
                else:
                    tooltip_text = f"Clic para seleccionar {num_str}"


            def on_numero_click(e, numero=num_str, estado_sel=seleccionado, persona_db=nombre_persona_del_db):
                nombre_actual_en_input = nombre_input.value.strip()
                
                if not nombre_actual_en_input and estado_sel == 0:
                    mensaje_error.value = "Por favor, ingresa tu nombre para seleccionar un número."
                    page.update()
                    return
                
                exito = seleccionar_o_deseleccionar_numero(numero, nombre_actual_en_input, estado_sel, persona_db)

                if exito:
                    mensaje_error.value = ""
                    actualizar_ui() 
                else:
                    if estado_sel == 0:
                        mensaje_error.value = "No se pudo seleccionar. Asegúrate de ingresar tu nombre."
                    elif estado_sel == 1:
                        mensaje_error.value = f"El número {numero} fue seleccionado por {persona_db}. Solo {persona_db} puede deseleccionarlo."
                    page.update(mensaje_error)

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
                    tooltip=tooltip_text
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
                    if not is_admin_logged_in:
                        admin_login_message.value = "Acceso denegado. Debes iniciar sesión como administrador para cambiar el estado de pago."
                        admin_login_message.color = ft.Colors.RED_500
                        e.control.value = str(1 - int(e.control.value)) 
                        page.update(admin_login_message, e.control)
                        return

                    nuevo_estado = int(e.control.value) 
                    update_pago_status_db(persona_nombre, nuevo_estado)
                    admin_login_message.value = ""
                    page.update(e.control, admin_login_message) 

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

    def actualizar_conteo_numeros_ui():
        vendidos, disponibles = get_numeros_counts()
        vendidos_text.value = f"Vendidos: {vendidos}"
        disponibles_text.value = f"Disponibles: {disponibles}"
        page.update(vendidos_text, disponibles_text) 


    def actualizar_ui():
        global current_valor_numero, current_descripcion_rifa
        current_valor_numero, current_descripcion_rifa = get_configuracion_db()
        
        display_valor_numero.value = f"Valor del número: ¢{current_valor_numero}"
        display_descripcion_rifa.value = current_descripcion_rifa
        
        if is_admin_logged_in:
            valor_numero_input.value = str(int(current_valor_numero)) 
            descripcion_rifa_input.value = current_descripcion_rifa
            valor_numero_input.visible = True
            descripcion_rifa_input.visible = True
            config_admin_controls.visible = True # Asegurar que el contenedor de edición esté visible
        else:
            valor_numero_input.visible = False
            descripcion_rifa_input.visible = False
            config_admin_controls.visible = False # Asegurar que el contenedor de edición esté oculto

            display_valor_numero.visible = True
            display_descripcion_rifa.visible = True

        actualizar_numeros_ui()
        actualizar_lista_seleccionados_ui()
        actualizar_conteo_numeros_ui()
        page.update()


    def close_reset_dialog(e):
        reset_alert_dialog.open = False
        page.update()

    def perform_reset_and_close_dialog(e):
        if not is_admin_logged_in:
            admin_login_message.value = "Acceso denegado. Debes iniciar sesión como administrador para resetear la rifa."
            admin_login_message.color = ft.Colors.RED_500
            reset_alert_dialog.open = False
            page.update(admin_login_message)
            return

        reset_rifa_db()
        debug_list_all_numeros() 
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
        if not is_admin_logged_in:
            admin_login_message.value = "Acceso denegado. Debes iniciar sesión como administrador para resetear la rifa."
            admin_login_message.color = ft.Colors.RED_500
            page.update(admin_login_message)
            return
        
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
        if not is_admin_logged_in:
            admin_login_message.value = "Acceso denegado. Debes iniciar sesión como administrador para liberar números por contacto."
            admin_login_message.color = ft.Colors.RED_500
            liberar_por_contacto_alert_dialog.open = False
            page.update(admin_login_message)
            return

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
        if not is_admin_logged_in:
            admin_login_message.value = "Acceso denegado. Debes iniciar sesión como administrador para liberar números por contacto."
            admin_login_message.color = ft.Colors.RED_500
            page.update(admin_login_message)
            return

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
                ft.Text("Acceso a Configuración de Administrador", size=18, weight=ft.FontWeight.BOLD),
                ft.Row(
                    [
                        admin_email_input,
                        admin_password_input, # Campo de contraseña
                        admin_login_button,
                        admin_logout_button
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=10
                ),
                admin_login_message,
                ft.Divider(),
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text("Detalles de la Rifa", size=20, weight=ft.FontWeight.BOLD),
                            display_valor_numero, 
                            ft.Text("Descripción de la Rifa:", size=12, color=ft.Colors.GREY_700),
                            display_descripcion_rifa, 
                            config_admin_controls,
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
                            ft.Divider(), 
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

    actualizar_ui() # Llamar al inicio para establecer el estado inicial

if __name__ == "__main__":
    # Opcional: Eliminar la base de datos al inicio para pruebas limpias
    # if os.path.exists(DATABASE_NAME):
    #     os.remove(DATABASE_NAME)
    #     print(f"Archivo de base de datos '{DATABASE_NAME}' eliminado para un inicio limpio.")
        
    ft.app(target=main)