import ast
import bdb
import flet as ft
from openai import OpenAI
from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatters import HtmlFormatter

# Конфигурация Deepseek api
DEEPSEEK_API_KEY = "sk-fdf8c97947724096a9ca1a8190994e6b"
DEEPSEEK_API_URL = "https://api.deepseek.com/v1"

class Debugger(bdb.Bdb):
    def __init__(self):
        super().__init__()
        self.current_line = 0
        self.variables = {}
        self.client = OpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url=DEEPSEEK_API_URL
        )
        self.update_ui_callback = None

    def set_update_ui(self, callback):
        self.update_ui_callback = callback

    def user_line(self, frame):
        self.current_line = frame.f_lineno
        self.variables = {**frame.f_locals, **frame.f_globals}
        if self.update_ui_callback:
            self.update_ui_callback(self.current_line, self.variables)

    def ask_deepseek(self, code: str, error: str = None) -> str:
        """Запрашивает подсказку у DeepSeek API"""
        prompt = (
            "Ты - помощник для отладки Python-кода. Проанализируй код и предложи исправления.\n"
            f"Код:\n```python\n{code}\n```\n"
        )
        if error:
            prompt += f"Ошибка: {error}\n"

        try:
            response = self.client.chat.completions.create(
                model="deepseek-coder",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Ошибка при запросе к DeepSeek API: {str(e)}"

def main(page: ft.Page):
    page.title = "Python Visual Debugger + DeepSeek AI"
    page.theme_mode = ft.ThemeMode.DARK
    page.window.width = 800
    page.window.height = 700

    # Элементы интерфейса
    code_editor = ft.TextField(
        multiline=True,
        value="x = 5\ny = '10'\nprint(x + y)",
        width=700,
        height=300,
        border_color=ft.Colors.BLUE_400,  # Исправлено: ft.Colors вместо ft.colors
        text_style=ft.TextStyle(font_family="Consolas"),
    )

    run_button = ft.ElevatedButton("Запустить", icon=ft.Icons.PLAY_ARROW)  # Исправлено: ft.Icons
    step_button = ft.ElevatedButton("Шаг", icon=ft.Icons.SKIP_NEXT, disabled=True)  # Исправлено: ft.Icons
    stop_button = ft.ElevatedButton("Стоп", icon=ft.Icons.STOP, disabled=True)  # Исправлено: ft.Icons
    ai_button = ft.ElevatedButton("Спросить DeepSeek", icon=ft.Icons.AUTO_AWESOME, disabled=True)  # Исправлено: ft.Icons

    output = ft.Text("", selectable=True)
    variables_panel = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Переменная", weight="bold")),
            ft.DataColumn(ft.Text("Значение", weight="bold")),
        ],
        width=700,
    )

    ai_response = ft.Column(
        [
            ft.Text("AI-помощник:", weight='bold'),
            ft.Text("Здесь будут подсказки...", selectable=True),
        ],
        scroll=ft.ScrollMode.AUTO,
    )

    debugger = Debugger()
    debugger.set_update_ui(lambda line, vars: update_ui(line, vars))

    def update_ui(line, vars):
        output.value = f"Выполняется строка {line}"
        variables_panel.rows = [
            ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(k, font_family="Consolas")),
                    ft.DataCell(ft.Text(str(v), font_family="Consolas")),
                ]
            )
            for k, v in vars.items()
        ]
        page.update()

    def run_debug(e):
        code = code_editor.value
        try:
            debugger.run(code)
            output.value = "Код выполнен успешно!"
            ai_button.disabled = False
        except Exception as e:
            output.value = f"Ошибка: {str(e)}"
            ai_button.disabled = False
        page.update()

    def ask_ai(e):
        code = code_editor.value
        error = output.value if "Ошибка:" in output.value else None

        ai_response.controls[1].value = "Запрашиваю подсказку у DeepSeek..."
        page.update()

        response = debugger.ask_deepseek(code, error)
        ai_response.controls[1].value = response
        page.update()

    run_button.on_click = run_debug
    ai_button.on_click = ask_ai

    page.add(
        ft.Column(
            [
                ft.Text("Python Debugger", size=24, weight="bold"),
                code_editor,
                ft.Row([run_button, step_button, stop_button, ai_button]),
                ft.Divider(),
                ft.Text("Вывод:", weight="bold"),
                output,
                ft.Text("Переменные:", weight="bold"),
                variables_panel,
                ft.Divider(),
                ai_response,
            ],
            spacing=10,
            expand=True,
        )
    )

if __name__ == "__main__":
    ft.app(target=main)