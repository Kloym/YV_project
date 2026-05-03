import os
import sqlite3
import webbrowser
from threading import Timer
import dash
import pandas as pd
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, State


# КОНФИГУРАЦИЯ И КОНСТАНТЫ

DB_NAME = "database.db"

MONTHS_RU = {
    1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель",
    5: "Май", 6: "Июнь", 7: "Июль", 8: "Август",
    9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь"
}

# Кэш для минимизации обращений к диску
_CACHE = {
    "data": pd.DataFrame(),
    "last_modified": 0
}

# ИНИЦИАЛИЗАЦИЯ ПРИЛОЖЕНИЯ

app = dash.Dash(
    __name__, 
    external_stylesheets=[
        dbc.themes.BOOTSTRAP, 
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css",
        "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap"
    ]
)
app.title = "Clinical AI Dashboard"

# CSS Блок

app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            /* --- БАЗОВЫЕ ПЕРЕМЕННЫЕ (СВЕТЛАЯ ТЕМА) --- */
            :root {
                --bg-color: #f4f7fe;
                --card-bg: #ffffff;
                --text-main: #1b2559;
                --text-muted: #a3aed1;
                --grid-color: #e9edf7;
                --shadow: 0px 18px 40px rgba(112, 144, 176, 0.12);
                --sidebar-shadow: 14px 17px 40px 4px rgba(112, 144, 176, 0.08);
                --primary: #4318FF;
                --primary-light: rgba(67, 24, 255, 0.1);
            }

            /* --- ПЕРЕМЕННЫЕ (ТЕМНАЯ ТЕМА) --- */
            [data-theme="dark"] {
                --bg-color: #0b1437;
                --card-bg: #111c44;
                --text-main: #ffffff;
                --text-muted: #8f9bba;
                --grid-color: #1b254b;
                --shadow: 0px 18px 40px rgba(0, 0, 0, 0.4);
                --sidebar-shadow: 14px 17px 40px 4px rgba(0, 0, 0, 0.5);
                --primary-light: rgba(67, 24, 255, 0.2);
            }

            body {
                background-color: var(--bg-color);
                color: var(--text-main);
                font-family: 'Inter', sans-serif;
                transition: background-color 0.4s ease, color 0.4s ease;
                margin: 0;
            }
            
            /* --- ДИЗАЙН ВЫПАДАЮЩИХ СПИСКОВ --- */
            
            /* Делаем прозрачным фон базовых контейнеров, чтобы они не перекрывали цвета */
            .Select, .Select-value {
                background-color: transparent !important;
            }

            .Select-control { 
                background-color: var(--card-bg) !important; 
                border: 2px solid var(--grid-color) !important; 
                border-radius: 16px !important; 
                box-shadow: none !important; 
                padding: 4px 8px !important; 
                transition: all 0.3s ease !important; 
            }
            
            .Select-control:hover, .is-focused > .Select-control { 
                border-color: var(--primary) !important; 
                box-shadow: 0 0 0 4px var(--primary-light) !important; 
            }

            /* Текст выбранного значения и заглушки опирается на переменные */
            .Select-value-label,
            .Select-input > input,
            .Select-placeholder { 
                color: var(--text-main) !important; 
                font-weight: 500;
            }

            /* Выпадающее меню с опциями */
            .Select-menu-outer { 
                background-color: var(--card-bg) !important; 
                border: 1px solid var(--grid-color) !important; 
                border-radius: 16px !important; 
                box-shadow: var(--shadow) !important; 
                margin-top: 8px !important; 
                padding: 8px !important; 
                z-index: 9999 !important; 
            }
            
            .Select-menu-outer input { 
                background-color: var(--bg-color) !important; 
                border: 1px solid var(--grid-color) !important; 
                color: var(--text-main) !important; 
                border-radius: 10px !important; 
                padding: 10px 15px !important; 
            }
            
            .Select-menu-outer label { 
                color: var(--text-main) !important; 
                font-weight: 500 !important; 
            }
            
            .Select-menu-outer button { 
                color: var(--primary) !important; 
                font-weight: 600 !important; 
                background: transparent !important; 
                border: none !important; 
            }
            
            .VirtualizedSelectOption { 
                color: var(--text-main) !important; 
                padding: 10px 15px !important; 
                border-radius: 10px !important; 
                margin-bottom: 2px !important; 
                transition: all 0.2s; 
                background-color: transparent !important;
            }
            
            .VirtualizedSelectFocusedOption, .VirtualizedSelectOption:hover { 
                background-color: var(--primary-light) !important; 
                color: var(--primary) !important; 
            }

            /* Капсулы (Tags) для множественного выбора */
            .has-value.Select--multi .Select-value { 
                background-color: var(--primary-light) !important; 
                color: var(--primary) !important; 
                border: 1px solid var(--grid-color) !important; 
                border-radius: 12px !important; 
                padding: 4px 10px !important; 
                margin: 4px !important; 
                font-weight: 600; 
            }
            
            .has-value.Select--multi .Select-value-icon { 
                border-right: 1px solid var(--grid-color) !important; 
                color: var(--primary) !important; 
                border-radius: 12px 0 0 12px !important; 
                transition: background 0.2s; 
            }
            
            .has-value.Select--multi .Select-value-icon:hover { 
                background-color: var(--primary) !important; 
                color: white !important; 
            }
            
            /* Скроллбар */
            ::-webkit-scrollbar { width: 8px; height: 8px; }
            ::-webkit-scrollbar-track { background: transparent; }
            ::-webkit-scrollbar-thumb { background: var(--grid-color); border-radius: 10px; }
            ::-webkit-scrollbar-thumb:hover { background: var(--text-muted); }
            
            /* Иконка стрелочки и крестик */
            .Select-clear-zone { color: var(--text-muted) !important; }
            .Select-arrow { border-color: var(--text-muted) transparent transparent !important; }
            
            /* --- ДИЗАЙН SQL ПЕСОЧНИЦЫ --- */
            .sql-editor {
                font-family: 'Courier New', Courier, monospace !important;
                background-color: #1e1e1e !important;
                color: #d4d4d4 !important;
                border-radius: 16px !important;
                border: 2px solid var(--grid-color) !important;
                padding: 15px !important;
                width: 100% !important;
                min-height: 140px !important;
                resize: vertical !important;
                transition: all 0.3s ease;
                font-size: 14px;
            }
            
            .sql-editor:focus {
                border-color: var(--primary) !important;
                outline: none !important;
                box-shadow: 0 0 0 4px var(--primary-light) !important;
            }
            
            .schema-badge {
                background-color: var(--bg-color);
                color: var(--text-main);
                padding: 8px 14px;
                border-radius: 10px;
                font-size: 13px;
                font-weight: 600;
                display: inline-block;
                margin: 4px;
                border: 1px solid var(--grid-color);
                transition: all 0.3s;
            }
            
            .schema-badge:hover {
                background-color: var(--primary-light);
                color: var(--primary);
                border-color: var(--primary);
                cursor: default;
            }
        </style>
    </head>
    <body>
        <div id="app-container">{%app_entry%}</div>
        <footer>{%config%}{%scripts%}{%renderer%}</footer>
    </body>
</html>
'''

def get_optimized_data() -> pd.DataFrame:
    """
    Загружает данные из SQLite, очищает их, преобразует типы 
    и кэширует в оперативной памяти для моментальной работы дашборда.
    """
    if not os.path.exists(DB_NAME):
        return pd.DataFrame()
    
    current_mtime = os.path.getmtime(DB_NAME)

    if not _CACHE["data"].empty and _CACHE["last_modified"] == current_mtime:
        return _CACHE["data"]

    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql("SELECT * FROM medical_data", conn)
    conn.close()
    
    if df.empty:
        return df

    df.columns = (
        df.columns
        .str.replace(r'\n|\r', ' ', regex=True)
        .str.replace(r'\s+', ' ', regex=True)
        .str.strip()
    )

    if 'Период' in df.columns:
        df['dt'] = pd.to_datetime(df['Период'], errors='coerce')
        df = df.dropna(subset=['dt'])
        df['Year'] = df['dt'].dt.year.astype(int)
        df['Month_Num'] = df['dt'].dt.month.astype(int)
        df['Month_Name'] = df['Month_Num'].map(MONTHS_RU)

    if 'Сумма' in df.columns and df['Сумма'].dtype == object:
        df['Сумма'] = pd.to_numeric(
            df['Сумма'].astype(str).str.replace(',', '.').str.replace(' ', ''), 
            errors='coerce'
        ).fillna(0)

    _CACHE["data"] = df
    _CACHE["last_modified"] = current_mtime
    
    return df


# --- ЕДИНАЯ ФУНКЦИЯ ГРАФИКА ---
def apply_beautiful_layout(fig: go.Figure, theme: str, x_range=None, tickvals=None, ticktext=None) -> go.Figure:
    """
    Единая функция для применения красивого дизайна ко всем графикам.
    Впитывает в себя настройки отступов, легенды, сетки и темной/светлой темы.
    """
    if theme == "dark": 
        text_color, grid_color, card_bg = "#ffffff", "#1b254b", "#111c44"
    else: 
        text_color, grid_color, card_bg = "#1b2559", "#e9edf7", "#ffffff"

    xaxis_config = dict(
        showgrid=False, 
        color=text_color, 
        showline=True, 
        linecolor=grid_color, 
        linewidth=2,
        automargin=True
    )

    if x_range is not None:
        xaxis_config['range'] = x_range
    if tickvals is not None and ticktext is not None:
        xaxis_config['tickmode'] = 'array'
        xaxis_config['tickvals'] = tickvals
        xaxis_config['ticktext'] = ticktext
        
    fig.update_layout(
        font_family="Inter", 
        separators=", ",
        plot_bgcolor="rgba(0,0,0,0)", 
        paper_bgcolor="rgba(0,0,0,0)", 
        margin=dict(l=10, r=10, t=30, b=10),
        legend=dict(
            orientation="h", 
            yanchor="bottom", 
            y=1.05, 
            xanchor="right", 
            x=1, 
            font=dict(color=text_color, size=13)
        ),
        xaxis=xaxis_config,
        yaxis=dict(
            showgrid=True, 
            gridcolor=grid_color, 
            zeroline=False, 
            color=text_color,
            automargin=True
        ),
        hoverlabel=dict(
            bgcolor=card_bg, 
            font_size=14, 
            font_family="Inter", 
            font_color=text_color, 
            bordercolor=grid_color
        ),
        hovermode="x unified",
        barmode="group"
    )
    return fig


# UI КОМПОНЕНТЫ

def create_kpi_card(title: str, id_value: str, icon_class: str, color_hex: str, bg_rgba: str) -> dbc.Card:
    """
    Генерирует стандартизированную карточку KPI (Key Performance Indicator).
    """
    return dbc.Card(
        [
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.P(
                            title, 
                            style={
                                "color": "var(--text-muted)", 
                                "fontWeight": "600", 
                                "fontSize": "13px", 
                                "marginBottom": "6px", 
                                "letterSpacing": "0.5px", 
                                "textTransform": "uppercase"
                            }
                        ),
                        html.H3(
                            id=id_value, 
                            style={
                                "color": "var(--text-main)", 
                                "fontWeight": "800", 
                                "margin": "0", 
                                "fontSize": "26px", 
                                "transition": "color 0.3s"
                            }
                        )
                    ], width=8, className="pe-0"),
                    
                    dbc.Col([
                        html.Div(
                            html.I(className=icon_class, style={"color": color_hex, "fontSize": "22px"}),
                            style={
                                "backgroundColor": bg_rgba, 
                                "width": "54px", 
                                "height": "54px", 
                                "borderRadius": "50%", 
                                "display": "flex", 
                                "alignItems": "center", 
                                "justifyContent": "center", 
                                "marginLeft": "auto"
                            }
                        )
                    ], width=4, className="ps-0")
                ], className="align-items-center")
            ])
        ], 
        style={
            "backgroundColor": "var(--card-bg)", 
            "border": "none", 
            "borderRadius": "24px", 
            "boxShadow": "var(--shadow)", 
            "transition": "all 0.3s"
        }
    )


app.layout = html.Div([
    dcc.Store(id="theme-store", data="light"),

    html.Div([
        html.Div([
            html.I(className="fas fa-heartbeat", style={"color": "var(--primary)", "fontSize": "32px", "marginRight": "12px"}),
            html.H3("Clinical AI", style={"color": "var(--text-main)", "fontWeight": "800", "margin": 0, "letterSpacing": "-1px", "transition": "color 0.3s"})
        ], style={"marginBottom": "45px", "display": "flex", "alignItems": "center", "padding": "10px"}),
        
        # Блок 1: Настройки Аналитики
        html.Div([
            html.Label("1. Показатель (Что считаем?)", style={"color": "var(--text-main)", "fontWeight": "700", "fontSize": "13px", "marginBottom": "8px", "textTransform": "uppercase"}),
            dcc.Dropdown(
                id="f-metric",
                options=[
                    {"label": "💰 Общая сумма (₽)", "value": "sum"},
                    {"label": "📋 Количество услуг (МЭС)", "value": "count_mes"},
                    {"label": "🧑 Уникальные пациенты", "value": "count_patients"}
                ],
                value="count_mes", 
                clearable=False,
            ),
            
            html.Label("2. Разрез линий (Группировка)", style={"color": "var(--text-main)", "fontWeight": "700", "fontSize": "13px", "marginBottom": "8px", "marginTop": "20px", "textTransform": "uppercase"}),
            dcc.Dropdown(
                id="f-group-by",
                options=[
                    {"label": "🏥 По отделениям", "value": "Наименование отделения"},
                    {"label": "📋 По кодам МЭС", "value": "Код Услуги"},
                    {"label": "🩺 По профилям", "value": "Наименование профиля"}
                ],
                value="Наименование отделения", 
                clearable=False,
            ),
        ], style={"marginBottom": "25px", "paddingBottom": "25px", "borderBottom": "2px dashed var(--grid-color)"}),

        # Блок 2: Фильтры Данных
        html.Label("ФИЛЬТРЫ ДАННЫХ", style={"color": "var(--text-muted)", "fontWeight": "800", "fontSize": "12px", "marginBottom": "15px", "letterSpacing": "1px"}),
        
        html.Div([
            html.Label("Период (Год)", style={"color": "var(--text-main)", "fontWeight": "600", "fontSize": "14px", "marginBottom": "8px"}),
            dcc.Dropdown(id="f-year", multi=True, placeholder="Все года..."),
        ], className="mb-4"),
        
        html.Div([
            html.Label("Месяц", style={"color": "var(--text-main)", "fontWeight": "600", "fontSize": "14px", "marginBottom": "8px"}),
            dcc.Dropdown(id="f-month", multi=True, placeholder="Все месяцы..."),
        ], className="mb-4"),
        
        html.Div([
            html.Label("Отделение", style={"color": "var(--text-main)", "fontWeight": "600", "fontSize": "14px", "marginBottom": "8px"}),
            dcc.Dropdown(id="f-dept", multi=True, placeholder="Все отделения..."),
        ], className="mb-4"),
        
        html.Div([
            html.Label("Код услуги (МЭС)", style={"color": "var(--text-main)", "fontWeight": "600", "fontSize": "14px", "marginBottom": "8px"}),
            dcc.Dropdown(id="f-mes", multi=True, placeholder="Все коды услуг..."),
        ], className="mb-4"),

        dbc.Button(
            [html.I(className="fas fa-file-excel", style={"marginRight": "10px"}), "Экспорт в Excel"], 
            id="btn-dl", 
            style={
                "width": "100%", 
                "backgroundColor": "var(--primary)", 
                "border": "none", 
                "borderRadius": "16px", 
                "padding": "14px", 
                "fontWeight": "600", 
                "boxShadow": "0px 10px 20px rgba(67, 24, 255, 0.2)", 
                "marginTop": "10px"
            }
        ),
        dcc.Download(id="download-xlsx")

    ], style={
        "position": "fixed", 
        "top": 0, 
        "left": 0, 
        "bottom": 0, 
        "width": "340px", 
        "padding": "40px 30px", 
        "backgroundColor": "var(--card-bg)", 
        "boxShadow": "var(--sidebar-shadow)", 
        "zIndex": 100, 
        "transition": "all 0.4s ease", 
        "overflowY": "auto"
    }),

    html.Div([

        dbc.Row([
            dbc.Col(html.H2("Dashboard Overview", style={"fontWeight": "800", "color": "var(--text-main)", "letterSpacing": "-1px", "transition": "color 0.3s"}), width=8),
            dbc.Col(
                html.Div([
                    html.Button(
                        html.I(id="theme-icon", className="fas fa-moon"), 
                        id="theme-toggle", 
                        style={
                            "background": "transparent", 
                            "border": "none", 
                            "fontSize": "22px", 
                            "color": "var(--text-muted)", 
                            "cursor": "pointer", 
                            "marginRight": "25px", 
                            "transition": "color 0.4s ease"
                        }
                    ),
                    html.Div([
                        html.Span("Dr. Admin", style={"fontWeight": "700", "marginRight": "15px", "color": "var(--text-main)", "fontSize": "15px"}),
                        html.Img(src="https://ui-avatars.com/api/?name=Admin&background=4318FF&color=fff", style={"borderRadius": "50%", "width": "45px", "boxShadow": "0px 4px 10px rgba(0,0,0,0.1)"})
                    ], style={
                        "display": "flex", 
                        "alignItems": "center", 
                        "backgroundColor": "var(--card-bg)", 
                        "border": "1px solid var(--grid-color)", 
                        "padding": "6px 20px", 
                        "borderRadius": "30px", 
                        "transition": "all 0.3s"
                    })
                ], style={"textAlign": "right", "display": "flex", "alignItems": "center", "justifyContent": "flex-end"}), 
                width=4
            )
        ], style={"marginBottom": "40px", "marginTop": "10px"}),

        # Карточки KPI
        dbc.Row([
            dbc.Col(create_kpi_card("ОБЩАЯ СУММА", "kpi-sum", "fas fa-wallet", "#4318FF", "rgba(67, 24, 255, 0.1)"), xl=3, lg=6, md=6, sm=12, className="mb-4"),
            dbc.Col(create_kpi_card("УНИКАЛЬНЫХ ПАЦИЕНТОВ", "kpi-patients", "fas fa-user-injured", "#FF7D00", "rgba(255, 125, 0, 0.1)"), xl=3, lg=6, md=6, sm=12, className="mb-4"),
            dbc.Col(create_kpi_card("ОКАЗАНО УСЛУГ (МЭС)", "kpi-mes", "fas fa-file-medical-alt", "#01B574", "rgba(1, 181, 116, 0.1)"), xl=3, lg=6, md=6, sm=12, className="mb-4"),
            dbc.Col(create_kpi_card("АКТИВНЫХ ОТДЕЛЕНИЙ", "kpi-depts", "fas fa-hospital", "#39B8FF", "rgba(57, 184, 255, 0.1)"), xl=3, lg=6, md=6, sm=12, className="mb-4"),
        ]),

        # Главный График
        dbc.Row([
            dbc.Col(
                html.Div([
                    html.H4("Аналитика по времени", id="main-chart-title", style={"fontWeight": "800", "color": "var(--text-main)", "marginBottom": "30px", "letterSpacing": "-0.5px"}),
                    dcc.Graph(id="main-line-chart", config={'displayModeBar': False}, style={"height": "480px"})
                ], style={
                    "backgroundColor": "var(--card-bg)", 
                    "borderRadius": "24px", 
                    "padding": "35px", 
                    "boxShadow": "var(--shadow)", 
                    "transition": "all 0.3s"
                }), 
                width=12
            )
        ]),

        # --- НОВЫЙ БЛОК: SQL ---
        dbc.Row([
            dbc.Col(
                html.Div([
                    html.H4([html.I(className="fas fa-terminal", style={"marginRight": "12px", "color": "var(--primary)"}), "SQL-Песочница"], style={"fontWeight": "800", "color": "var(--text-main)", "marginBottom": "15px", "letterSpacing": "-0.5px"}),
                    html.P("Напишите SQL-запрос. При выполнении программа перерисует верхний главный график! (Первая колонка станет осью X, числовые колонки — осью Y).", style={"color": "var(--text-muted)", "fontSize": "14px", "marginBottom": "20px"}),
                    
                    dcc.Textarea(
                        id="sql-input",
                        className="sql-editor",
                        placeholder="Введите ваш SQL запрос здесь...",
                        value="SELECT \n  [Наименование отделения], \n  COUNT(*) as [Количество услуг] \nFROM medical_data \nGROUP BY [Наименование отделения] \nORDER BY [Количество услуг] DESC \nLIMIT 7;"
                    ),
                    
                    dbc.Button(
                        [html.I(className="fas fa-play", style={"marginRight": "10px"}), "Нарисовать график из SQL"], 
                        id="btn-execute-sql", 
                        style={"backgroundColor": "var(--primary)", "border": "none", "borderRadius": "12px", "padding": "12px 24px", "fontWeight": "600", "marginTop": "15px", "boxShadow": "0px 8px 15px rgba(67, 24, 255, 0.2)"}
                    ),
                    
                    html.Div(id="sql-error", style={"color": "#E11D48", "marginTop": "15px", "fontWeight": "600", "fontSize": "14px"}),
                ], style={"backgroundColor": "var(--card-bg)", "borderRadius": "24px", "padding": "35px", "boxShadow": "var(--shadow)", "transition": "all 0.3s", "height": "100%"}), 
                xl=8, lg=12, className="mb-4"
            ),

            # Шпаргалка по базе данных
            dbc.Col(
                html.Div([
                    html.H5([html.I(className="fas fa-database", style={"marginRight": "10px", "color": "#01B574"}), "Схема Данных"], style={"fontWeight": "800", "color": "var(--text-main)", "marginBottom": "25px"}),
                    
                    html.Div([
                        html.Span("Таблица:", style={"color": "var(--text-muted)", "fontSize": "13px", "fontWeight": "600", "textTransform": "uppercase", "marginRight": "10px"}),
                        html.Span("medical_data", style={"color": "var(--primary)", "fontWeight": "700", "fontSize": "16px", "backgroundColor": "var(--primary-light)", "padding": "4px 10px", "borderRadius": "8px"})
                    ], style={"marginBottom": "25px"}),
                    
                    html.P("Доступные колонки:", style={"color": "var(--text-muted)", "fontSize": "13px", "fontWeight": "600", "textTransform": "uppercase", "marginBottom": "15px"}),
                    
                    html.Div([
                        html.Span("Период", className="schema-badge"),
                        html.Span("Наименование отделения", className="schema-badge"),
                        html.Span("Код Услуги", className="schema-badge"),
                        html.Span("Наименование профиля", className="schema-badge"),
                        html.Span("ИД пациента в версии счета", className="schema-badge"),
                        html.Span("Сумма", className="schema-badge")
                    ]),
                    
                    html.Div([
                        html.I(className="fas fa-info-circle", style={"marginRight": "8px", "color": "var(--text-muted)"}),
                        html.Span("Если в названии колонки есть пробелы, оборачивайте её в квадратные скобки: ", style={"color": "var(--text-muted)"}),
                        html.Code("[Наименование отделения]", style={"color": "var(--text-main)", "fontWeight": "600"})
                    ], style={"marginTop": "30px", "fontSize": "13px", "backgroundColor": "var(--bg-color)", "padding": "15px", "borderRadius": "12px", "border": "1px solid var(--grid-color)"})
                    
                ], style={"backgroundColor": "var(--card-bg)", "borderRadius": "24px", "padding": "35px", "boxShadow": "var(--shadow)", "transition": "all 0.3s", "height": "100%"}), 
                xl=4, lg=12, className="mb-4"
            )
        ], className="mt-4")

    ], style={"marginLeft": "340px", "padding": "40px 50px", "minHeight": "100vh"})
])


app.clientside_callback(
    """
    function(n_clicks, current_theme) {
        if (!n_clicks) { return window.dash_clientside.no_update; }
        const newTheme = current_theme === 'light' ? 'dark' : 'light';
        document.documentElement.setAttribute('data-theme', newTheme);
        return newTheme;
    }
    """,
    Output("theme-store", "data"),
    Input("theme-toggle", "n_clicks"),
    State("theme-store", "data")
)

@app.callback(
    Output("theme-icon", "className"), 
    Input("theme-store", "data")
)
def update_icon(theme: str) -> str:
    """Обновляет иконку луны/солнца при смене темы."""
    if theme == "dark":
        return "fas fa-sun"
    return "fas fa-moon"


@app.callback(
    [Output("f-year", "options"), Output("f-month", "options"), 
     Output("f-dept", "options"), Output("f-mes", "options")],
    [Input("f-year", "value"), Input("f-month", "value"),
     Input("f-dept", "value"), Input("f-mes", "value")]
)
def update_smart_filters(years, months, depts, mes_list):
    """
    Умные каскадные фильтры (Faceted Search).
    Обновляет доступные опции в фильтрах на основе того, что выбрано в других фильтрах.
    """
    df = get_optimized_data()
    
    if df.empty: 
        return [[], [], [], []]
    
    def get_mask_for(skip_col: str) -> pd.Series:
        """
        Создает маску фильтрации, игнорируя колонку
        """
        mask = pd.Series(True, index=df.index)
        if skip_col != 'Year' and years and 'Year' in df.columns: 
            mask &= df['Year'].isin(years)
        if skip_col != 'Month' and months and 'Month_Name' in df.columns: 
            mask &= df['Month_Name'].isin(months)
        if skip_col != 'Dept' and depts and 'Наименование отделения' in df.columns: 
            mask &= df['Наименование отделения'].isin(depts)
        if skip_col != 'MES' and mes_list and 'Код Услуги' in df.columns: 
            mask &= df['Код Услуги'].isin(mes_list)
        return mask

    opts_year = sorted(df.loc[get_mask_for('Year'), 'Year'].unique()) if 'Year' in df.columns else []
    
    if 'Month_Num' in df.columns:
        m_df = df.loc[get_mask_for('Month')].drop_duplicates(subset=['Month_Num', 'Month_Name']).sort_values('Month_Num')
        opts_month = [{"label": row['Month_Name'], "value": row['Month_Name']} for _, row in m_df.iterrows()]
    else: 
        opts_month = []

    opts_dept = sorted(df.loc[get_mask_for('Dept'), 'Наименование отделения'].dropna().unique()) if 'Наименование отделения' in df.columns else []
    opts_mes = sorted(df.loc[get_mask_for('MES'), 'Код Услуги'].dropna().unique()) if 'Код Услуги' in df.columns else []
    
    return [opts_year, opts_month, opts_dept, opts_mes]


@app.callback(
    [Output("main-line-chart", "figure"), Output("main-chart-title", "children"),
     Output("kpi-sum", "children"), Output("kpi-patients", "children"), 
     Output("kpi-mes", "children"), Output("kpi-depts", "children")],
    [Input("f-year", "value"), Input("f-month", "value"),
     Input("f-dept", "value"), Input("f-mes", "value"), 
     Input("f-metric", "value"), Input("f-group-by", "value"), Input("theme-store", "data")]
)
def update_standard_dashboard(years, months, depts, mes_list, metric, group_by_col, theme):
    """
    Основной метод отрисовки Дашборда. 
    Рассчитывает показатели и строит график на основе выбранных метрик и группировок.
    """
    df = get_optimized_data()
    if df.empty: 
        return go.Figure(), "Аналитика по времени", "0,00 ₽", "0", "0", "0"

    mask = pd.Series(True, index=df.index)
    if years and 'Year' in df.columns: 
        mask &= df['Year'].isin(years)
    if months and 'Month_Name' in df.columns: 
        mask &= df['Month_Name'].isin(months)
    if depts and 'Наименование отделения' in df.columns: 
        mask &= df['Наименование отделения'].isin(depts)
    if mes_list and 'Код Услуги' in df.columns: 
        mask &= df['Код Услуги'].isin(mes_list)

    filtered_df = df[mask]

    if 'Сумма' in filtered_df.columns:
        total_sum = f"{filtered_df['Сумма'].sum():,.2f}".replace(",", " ").replace(".", ",") + " ₽"
    else: 
        total_sum = "0,00 ₽"
        
    total_patients = f"{filtered_df['ИД пациента в версии счета'].nunique()}" if 'ИД пациента в версии счета' in filtered_df.columns else "0"
    total_mes = f"{len(filtered_df)}"
    active_depts = f"{filtered_df['Наименование отделения'].nunique()}" if 'Наименование отделения' in filtered_df.columns else "0"

    fig = go.Figure()
    x_range, tickvals, ticktext = None, [], []
    
    if not filtered_df.empty and 'dt' in filtered_df.columns:
        x_range = [filtered_df['dt'].min() - pd.Timedelta(days=3), filtered_df['dt'].max() + pd.Timedelta(days=3)]
        unique_dates = sorted(filtered_df['dt'].unique())
        tickvals = unique_dates
        ticktext = [f"{MONTHS_RU[pd.Timestamp(d).month]} {pd.Timestamp(d).year}" for d in unique_dates]

    if not filtered_df.empty and 'dt' in filtered_df.columns and group_by_col in filtered_df.columns:
        
        labels_map = {
            "Наименование отделения": "Отделение",
            "Код Услуги": "Код МЭС",
            "Наименование профиля": "Профиль"
        }
        hover_title = labels_map.get(group_by_col, "Значение")

        if metric == "sum" and 'Сумма' in filtered_df.columns:
            trend = filtered_df.groupby(['dt', group_by_col], observed=True)['Сумма'].sum().reset_index()
            y_col = 'Сумма'
            hover_template = f"<b>{hover_title}:</b> %{{fullData.name}}<br><b>Сумма:</b> %{{y:,.2f}} ₽<extra></extra>"
            
        elif metric == "count_patients" and 'ИД пациента в версии счета' in filtered_df.columns:
            trend = filtered_df.groupby(['dt', group_by_col], observed=True)['ИД пациента в версии счета'].nunique().reset_index(name='Пациенты')
            y_col = 'Пациенты'
            hover_template = f"<b>{hover_title}:</b> %{{fullData.name}}<br><b>Пациентов:</b> %{{y:,.0f}} чел.<extra></extra>"
            
        else:
            trend = filtered_df.groupby(['dt', group_by_col], observed=True).size().reset_index(name='Кол-во МЭС')
            y_col = 'Кол-во МЭС'
            hover_template = f"<b>{hover_title}:</b> %{{fullData.name}}<br><b>Оказано МЭС:</b> %{{y:,.0f}} ед.<extra></extra>"

        trend = trend.sort_values('dt')

        colors = [
            {"hex": "#4318FF", "rgba": "rgba(67, 24, 255, 0.15)"}, 
            {"hex": "#FF7D00", "rgba": "rgba(255, 125, 0, 0.15)"},
            {"hex": "#01B574", "rgba": "rgba(1, 181, 116, 0.15)"}, 
            {"hex": "#39B8FF", "rgba": "rgba(57, 184, 255, 0.15)"},
            {"hex": "#E11D48", "rgba": "rgba(225, 29, 72, 0.15)"}, 
            {"hex": "#8B5CF6", "rgba": "rgba(139, 92, 246, 0.15)"}
        ]

        for i, group_val in enumerate(trend[group_by_col].unique()):
            group_data = trend[trend[group_by_col] == group_val]
            c = colors[i % len(colors)]
            
            fig.add_trace(go.Scatter(
                x=group_data['dt'], 
                y=group_data[y_col], 
                name=str(group_val), 
                mode='lines+markers',
                cliponaxis=False, 
                line=dict(width=4, shape='spline', smoothing=1.3, color=c["hex"]), 
                marker=dict(size=12, color=c["hex"], line=dict(width=3, color="#ffffff" if theme=="light" else "#111c44")),
                fill='tozeroy', 
                fillcolor=c["rgba"],
                hovertemplate=hover_template
            ))

    fig = apply_beautiful_layout(fig, theme, x_range, tickvals, ticktext)

    return fig, "Аналитика по времени (Стандартный режим)", total_sum, total_patients, total_mes, active_depts


@app.callback(
    [Output("main-line-chart", "figure", allow_duplicate=True), 
     Output("main-chart-title", "children", allow_duplicate=True),
     Output("sql-error", "children")],
    Input("btn-execute-sql", "n_clicks"),
    [State("sql-input", "value"), State("theme-store", "data")],
    prevent_initial_call=True
)
def execute_custom_sql(n_clicks, query, theme):
    """
    Выполняет кастомный SQL-запрос и переписывает главный график.
    Работает через in-memory базу, чтобы использовать очищенные колонки.
    """
    if not query or not query.strip():
        return dash.no_update, dash.no_update, ""

    try:
        df = get_optimized_data()
        
        conn = sqlite3.connect(':memory:')
        df.to_sql('medical_data', conn, index=False, if_exists='replace')
        df_sql = pd.read_sql(query, conn)
        conn.close()

        if df_sql.empty:
            return dash.no_update, dash.no_update, "✅ Запрос выполнен успешно, но вернул пустой результат (0 строк)."

        fig = go.Figure()
        x_col = df_sql.columns[0] 

        colors = [
            {"hex": "#4318FF", "rgba": "rgba(67, 24, 255, 0.15)"}, 
            {"hex": "#FF7D00", "rgba": "rgba(255, 125, 0, 0.15)"},
            {"hex": "#01B574", "rgba": "rgba(1, 181, 116, 0.15)"}, 
            {"hex": "#39B8FF", "rgba": "rgba(57, 184, 255, 0.15)"},
            {"hex": "#E11D48", "rgba": "rgba(225, 29, 72, 0.15)"}, 
            {"hex": "#8B5CF6", "rgba": "rgba(139, 92, 246, 0.15)"}
        ]
        
        color_idx = 0
        has_numeric = False
        max_y_value = 0 

        for col in df_sql.columns[1:]:
            if pd.api.types.is_numeric_dtype(df_sql[col]):
                has_numeric = True
                
                current_max = df_sql[col].max()
                if current_max > max_y_value:
                    max_y_value = current_max

                c = colors[color_idx % len(colors)]

                col_name_lower = str(col).lower()
                is_currency = "сумм" in col_name_lower or "sum" in col_name_lower

                has_decimals = pd.api.types.is_float_dtype(df_sql[col]) and not (df_sql[col].dropna() % 1 == 0).all()
                
                if is_currency or has_decimals:
                    y_format = "%{y:,.2f}"
                    if is_currency:
                        y_format += " ₽"
                else:
                    y_format = "%{y:,.0f}"
                
                fig.add_trace(go.Scatter(
                    x=df_sql[x_col],
                    y=df_sql[col],
                    name=str(col),
                    mode='lines+markers',
                    cliponaxis=False, 
                    line=dict(width=4, shape='linear', color=c["hex"]),
                    marker=dict(size=12, color=c["hex"], line=dict(width=3, color="#ffffff" if theme=="light" else "#111c44")),
                    fill='tozeroy',
                    fillcolor=c["rgba"],
                    hovertemplate=f"<b>%{{x}}</b><br><b>{str(col)}:</b> {y_format}<extra></extra>"
                ))
                color_idx += 1

        if not has_numeric:
             return dash.no_update, dash.no_update, "⚠️ Для построения графика нужна хотя бы одна числовая колонка в результате."

        def format_label(label, max_len=35):
            s = str(label)
            if len(s) > max_len:
                words = s.split()
                if len(words) > 2:
                    mid = len(words) // 2
                    s = " ".join(words[:mid]) + "<br>" + " ".join(words[mid:])
                if len(s) > max_len * 2:
                    s = s[:max_len*2] + "..."
            return s
            
        tickvals = df_sql[x_col].tolist()
        ticktext = [format_label(val) for val in df_sql[x_col]]
        
        x_range = [-0.5, len(df_sql) - 0.5]
        y_padding = max_y_value * 0.05 if max_y_value > 0 else 10

        fig = apply_beautiful_layout(fig, theme, x_range=x_range, tickvals=tickvals, ticktext=ticktext)
        
        fig.update_yaxes(range=[-y_padding, max_y_value + y_padding])
        fig.update_layout(xaxis_tickangle=-30)

        return fig, "Аналитика по времени (SQL Режим 👨‍💻)", ""

    except Exception as e:
        return dash.no_update, dash.no_update, f"❌ Ошибка в запросе: {str(e)}"

@app.callback(
    Output("download-xlsx", "data"),
    Input("btn-dl", "n_clicks"),
    [State("f-year", "value"), State("f-month", "value"), 
     State("f-dept", "value"), State("f-mes", "value")],
    prevent_initial_call=True
)
def export_excel(n_clicks, years, months, depts, mes_list):
    """
    Экспортирует отфильтрованные данные обратно в Excel-файл.
    """
    df = get_optimized_data()
    mask = pd.Series(True, index=df.index)
    
    if years and 'Year' in df.columns: 
        mask &= df['Year'].isin(years)
    if months and 'Month_Name' in df.columns: 
        mask &= df['Month_Name'].isin(months)
    if depts and 'Наименование отделения' in df.columns: 
        mask &= df['Наименование отделения'].isin(depts)
    if mes_list and 'Код Услуги' in df.columns: 
        mask &= df['Код Услуги'].isin(mes_list)

    filtered_df = df[mask].copy()

    cols_to_drop = ['dt', 'Year', 'Month_Num', 'Month_Name']
    filtered_df = filtered_df.drop(columns=[c for c in cols_to_drop if c in filtered_df.columns])
    
    return dcc.send_data_frame(filtered_df.to_excel, "Clinical_Report_Export.xlsx", index=False)


def open_browser():
    """Открывает дефолтный браузер по адресу запущенного сервера."""
    webbrowser.open_new("http://127.0.0.1:8050")


if __name__ == "__main__":
    Timer(1.5, open_browser).start()
    app.run(debug=False, port=8050)