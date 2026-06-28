app.layout = html.Div(
    [
        dcc.Interval(
        id='update-interval',
        interval=60 * 1000,
        n_intervals=0
        ),

        dbc.Toast(
            [
                html.P(
                    "Вышло обновление, закройте программу и запустите обновленную программу в папке Обновление", 
                    className="mb-0", 
                    style={"fontSize": "14px", "fontWeight": "600", "color": "var(--text-main)", "lineHeight": "1.5"}
                )
            ],
            id="update-toast",
            header=html.Div([
                html.I(className="fas fa-info-circle", style={"color": "#FF7D00", "marginRight": "8px", "fontSize": "16px"}),
                html.Span("Внимание", style={"fontWeight": "800", "color": "var(--text-main)"})
            ]),
            is_open=False,
            dismissable=True,
            duration=None,
            style={
                "position": "fixed",
                "top": "50%",
                "left": "50%",
                "transform": "translate(-50%, -50%)",
                "width": "380px",
                "zIndex": 99999, 
                "backgroundColor": "var(--card-bg)",
                "boxShadow": "0 25px 50px rgba(0,0,0,0.5)",
                "borderRadius": "12px",
                "border": "2px solid #FF7D00"
            }
        ),
        dcc.Store(id="theme-store", data="light"),
        dcc.Store(id="presets-store", storage_type="local", data={}),
        dcc.Store(id="filtered-click-data"),
        dcc.Store(id="filtered-selected-data"),
    
        dcc.Store(id="app-version-store", storage_type="local"),
        dbc.Modal(
            [
                dbc.ModalHeader(
                    dbc.ModalTitle(
                        [html.I(className="fas fa-gift", style={"color": "#FF7D00", "marginRight": "10px"}), "Что нового в этой версии?"],
                        style={"fontWeight": "900", "color": "var(--primary)"}
                    ),
                    close_button=True
                ),
                dbc.ModalBody(
                    [
                        html.H5(CURRENT_APP_VERSION, style={"fontWeight": "800", "color": "var(--text-main)", "marginBottom": "15px"}),
                        html.Ul([
                            html.Li([html.B("Быстрый переход к пациенту: "), "В таблице на вкладке «Улучшенная аналитика» (под тепловой картой) теперь можно кликнуть на номер истории болезни (ИБ), чтобы моментально открыть детальную карточку пациента."]),
                            html.Li([html.B("Сравнение (PoP): "), "Улучшена панель сравнения периодов — теперь можно точечно выбирать конкретные месяцы для аналитики. (Находится в самом низу колонки фильтры, под Расширенными фильтрами)"]),
                            html.Li([html.B("Изменения в дизайне: "), "Колонка фильтров теперь сворачивается, что позволяет увеличить график. Изменена палитра цветов Дашборда. Некоторые фильтры перенесены в 'Расширенные фильтры'."]),
                            html.Li([html.B("Оптимизация: "), "Приложение теперь работает стабильнее, быстрее загружает графики и занимает меньше места!"]),
                        ], style={"lineHeight": "1.8", "fontSize": "15px", "color": "var(--text-main)"}),
                        
                        html.Div(
                            "Это окно появляется только один раз после обновления. Приятной работы! 💙",
                            style={"marginTop": "20px", "padding": "15px", "backgroundColor": "rgba(14, 165, 233, 0.1)", "borderRadius": "10px", "color": "var(--primary)", "fontWeight": "600", "fontSize": "13px"}
                        )
                    ],
                    style={"padding": "25px", "backgroundColor": "var(--bg-color)"}
                ),
                dbc.ModalFooter(
                    dbc.Button("Понятно, спасибо!", id="btn-close-changelog", className="ms-auto", style={"backgroundColor": "#01B574", "border": "none", "borderRadius": "12px", "fontWeight": "600", "padding": "10px 20px"})
                ),
            ],
            id="changelog-modal",
            is_open=False,
            size="lg",
            centered=True,
        ),

        html.Div(
            id="sidebar",
            className="no-print",
            style={
                "position": "fixed",
                "top": 0,
                "left": 0,
                "bottom": 0,
                "width": "340px",
                "padding": "40px 30px",
                "backgroundColor": "var(--card-bg)",
                "boxShadow": "var(--sidebar-shadow)",
                "zIndex": 100,
                "overflowY": "auto",
                "transition": "all 0.3s ease",
            },
            children=[
                html.Div(
                    id="sidebar-header-row",
                    style={
                        "marginBottom": "35px",
                        "display": "flex",
                        "alignItems": "center",
                        "justifyContent": "space-between",
                        "padding": "10px",
                        "transition": "all 0.3s ease"
                    },
                    children=[
                        html.Div(
                            id="sidebar-logo-container",
                            style={"transition": "all 0.3s ease", "opacity": "1", "width": "100%", "overflow": "hidden"},
                            children=html.Img(
                                src=CUSTOM_ICON,
                                style={"height": "45px", "display": "block", "minWidth": "200px"},
                            ),
                        ),
                        html.Button(
                            html.I(className="fas fa-chevron-left", id="sidebar-arrow-icon"),
                            id="btn-toggle-sidebar",
                            n_clicks=0,
                            style={
                                "background": "var(--primary-light)", "border": "none", "color": "var(--primary)",
                                "borderRadius": "50%", "width": "32px", "height": "32px", "minWidth": "32px",
                                "display": "flex", "alignItems": "center", "justifyContent": "center",
                                "cursor": "pointer", "zIndex": "10"
                            }
                        )
                    ],
                ),

                html.Div(
                    id="sidebar-content",
                    style={"display": "block"},
                    children=[
                        html.Label(
                            "Поиск пациента",
                            style={
                                "color": "var(--text-main)",
                                "fontWeight": "700",
                                "fontSize": "13px",
                                "marginBottom": "8px",
                                "textTransform": "uppercase",
                            },
                        ),
                        dbc.Input(id="f-patient", placeholder="Введите номер ИБ и нажмите Enter...", debounce=True, className="mb-4", style={"borderRadius": "12px", "border": "2px solid var(--grid-color)", "padding": "10px", "backgroundColor": "var(--bg-color)", "color": "var(--text-main)"}),
                        dbc.Checklist(options=[{"label": "Сравнить с прошлым годом (YoY)", "value": True}], id="f-yoy", value=[], switch=True, style={"color": "var(--primary)", "fontWeight": "600", "marginBottom": "25px"}),
                        html.Div(
                            [
                                html.Label("1. Показатель", style={"color": "var(--text-main)", "fontWeight": "700", "fontSize": "13px", "marginBottom": "8px", "textTransform": "uppercase"}),
                                dcc.Dropdown(id="f-metric", options=[{"label": "💰 Общая сумма (₽)", "value": "sum"}, {"label": "📋 Количество услуг", "value": "count_mes"}, {"label": "🧑 Пациенты", "value": "count_patients"}], value="count_mes", clearable=False),
                                html.Label("2. Разрез линий", style={"color": "var(--text-main)", "fontWeight": "700", "fontSize": "13px", "marginBottom": "8px", "marginTop": "20px", "textTransform": "uppercase"}),
                                dcc.Dropdown(id="f-group-by", options=[{"label": "🏥 По отделениям", "value": "Наименование отделения"}, {"label": "📋 По кодам МЭС", "value": "Код Услуги"}, {"label": "🩺 По профилям", "value": "Наименование профиля"}], value="Наименование отделения", clearable=False),
                            ],
                            style={"marginBottom": "25px", "paddingBottom": "25px", "borderBottom": "2px dashed var(--grid-color)"},
                        ),
                        html.Label("ФИЛЬТРЫ ДАННЫХ", style={"color": "var(--text-muted)", "fontWeight": "800", "fontSize": "12px", "marginBottom": "15px", "letterSpacing": "1px"}),
                        dbc.Accordion(
                            [
                                dbc.AccordionItem(
                                    title="Базовые фильтры",
                                    children=[
                                        html.Div([html.Label("Год", style={"color": "var(--text-main)", "fontWeight": "600", "fontSize": "14px", "marginBottom": "8px"}), dcc.Dropdown(id="f-year", multi=True, placeholder="Все года...")]),
                                        html.Div([html.Label("Квартал", style={"color": "var(--text-main)", "fontWeight": "600", "fontSize": "14px", "marginBottom": "8px"}), dcc.Dropdown(id="f-quarter", multi=True, placeholder="Все кварталы...")]),
                                        html.Div([html.Label("Профиль", style={"color": "var(--text-main)", "fontWeight": "600", "fontSize": "14px", "marginBottom": "8px"}), dcc.Dropdown(id="f-profile", multi=True, placeholder="Все профили...")]),
                                        html.Div([html.Label("Код услуги", style={"color": "var(--text-main)", "fontWeight": "600", "fontSize": "14px", "marginBottom": "8px"}), dcc.Dropdown(id="f-mes", multi=True, placeholder="Все коды...")]),
                                    ],
                                )
                            ], start_collapsed=False, always_open=True, style={"marginBottom": "15px"}
                        ),
                        dbc.Accordion(
                            [
                                dbc.AccordionItem(
                                    title="Расширенные фильтры",
                                    children=[
                                        html.Div([html.Label("Месяц", style={"color": "var(--text-main)", "fontWeight": "600", "fontSize": "14px", "marginBottom": "8px"}), dcc.Dropdown(id="f-month", multi=True, placeholder="Все месяцы...")]),
                                        html.Div([html.Label("Отделение", style={"color": "var(--text-main)", "fontWeight": "600", "fontSize": "14px", "marginBottom": "8px"}), dcc.Dropdown(id="f-dept", multi=True, placeholder="Все отделения...")]),
                                    ],
                                )
                            ], start_collapsed=True, always_open=False, style={"marginBottom": "15px"}
                        ),
                        dbc.Accordion(
                            [
                                dbc.AccordionItem(
                                    title="Сравнение периодов (PoP)",
                                    children=[
                                        html.Label("Период А (База):", style={"color": "var(--primary)", "fontWeight": "700", "fontSize": "12px", "marginTop": "5px"}),
                                        dbc.Row([
                                            dbc.Col(dcc.Dropdown(id="pop-a-year", placeholder="Год..."), width=6, style={"paddingRight": "5px"}),
                                            dbc.Col(dcc.Dropdown(id="pop-a-month", placeholder="Месяц..."), width=6, style={"paddingLeft": "5px"}),
                                        ], className="mb-3"),
                                        
                                        html.Label("Период B (Для сравнения):", style={"color": "#FF7D00", "fontWeight": "700", "fontSize": "12px"}),
                                        dbc.Row([
                                            dbc.Col(dcc.Dropdown(id="pop-b-year", placeholder="Год..."), width=6, style={"paddingRight": "5px"}),
                                            dbc.Col(dcc.Dropdown(id="pop-b-month", placeholder="Месяц..."), width=6, style={"paddingLeft": "5px"}),
                                        ], className="mb-3"),
                                        
                                        dbc.Button([html.I(className="fas fa-balance-scale", style={"marginRight": "8px"}), "Сравнить"], id="btn-run-pop", n_clicks=0, style={"width": "100%", "backgroundColor": "var(--primary)", "border": "none", "borderRadius": "12px", "padding": "10px", "fontWeight": "600"}),
                                    ]
                                )
                            ], start_collapsed=True, always_open=False, style={"marginBottom": "15px"}
                        ),
                        dbc.Button([html.I(className="fas fa-check", style={"marginRight": "10px"}), "Применить фильтры"], id="btn-apply-filters", n_clicks=0, style={"width": "100%", "backgroundColor": "#01B574", "border": "none", "borderRadius": "16px", "padding": "14px", "fontWeight": "600", "marginTop": "5px", "boxShadow": "0px 10px 20px rgba(1, 181, 116, 0.2)"}),
                        dbc.Button([html.I(className="fas fa-trash-alt", style={"marginRight": "10px"}), "Сбросить все"], id="btn-reset-all-filters", n_clicks=0, style={"width": "100%", "backgroundColor": "transparent", "border": "2px solid #E11D48", "color": "#E11D48", "borderRadius": "16px", "padding": "14px", "fontWeight": "600", "marginTop": "10px"}),
                        html.Div(
                            [
                                html.Span(
                                    className="pulse-dot", 
                                    style={
                                        "height": "10px", "width": "10px", "backgroundColor": "#01B574", 
                                        "borderRadius": "50%", "display": "inline-block", "marginRight": "10px"
                                    }
                                ),
                                html.Span(
                                    f"Обновлено: {get_db_last_updated()}", 
                                    style={"fontSize": "13px", "color": "var(--text-muted)", "fontWeight": "600"}
                                )
                            ],
                            style={
                                "marginTop": "35px", 
                                "display": "flex", 
                                "alignItems": "center", 
                                "justifyContent": "center", 
                                "padding": "12px", 
                                "backgroundColor": "var(--bg-soft)", 
                                "borderRadius": "12px",
                                "border": "1px solid var(--grid-color)"
                            }
                        ),
                    ]
                )
            ],
        ),

        html.Div(
            id="main-content",
            style={
                "marginLeft": "340px", 
                "padding": "40px 50px", 
                "minHeight": "100vh",
                "transition": "all 0.3s ease"
            },
            children=[
                dbc.Row(
                    [
                        dbc.Col(
                            html.Div(
                                style={"display": "flex", "alignItems": "center"},
                                children=[
                                    html.Img(
                                        id="main-header-logo",
                                        src=CUSTOM_ICON,
                                        style={
                                            "height": "0px",
                                            "opacity": "0",
                                            "transition": "all 0.3s ease",
                                            "marginRight": "0px",
                                        }
                                    ),
                                    html.H2(
                                        ["Дашборд мониторинг"],
                                        style={
                                            "fontWeight": "800",
                                            "color": "var(--text-main)",
                                            "letterSpacing": "-0.5px",
                                            "margin": 0,
                                        },
                                    ),
                                ]
                            ),
                            width=6,
                        ),
                        dbc.Col(
                            html.Div(
                                [
                                    dbc.Button(
                                        [html.I(className="fas fa-download", style={"marginRight": "8px"}), "ОБНОВИТЬ ПРОГРАММУ"],
                                        id="btn-force-update",
                                        className="no-print",
                                        style={"display": "none"}
                                    ),

                                    html.Button(
                                        html.I(className="fas fa-question-circle"),
                                        id="btn-help",
                                        n_clicks=0,
                                        title="Как пользоваться дашбордом?",
                                        className="no-print",
                                        style={
                                            "background": "transparent",
                                            "border": "none",
                                            "fontSize": "22px",
                                            "color": "var(--primary)",
                                            "cursor": "pointer",
                                            "marginRight": "20px",
                                        },
                                    ),
                                    html.Button(
                                        html.I(className="fas fa-file-pdf"),
                                        id="btn-pdf",
                                        n_clicks=0,
                                        className="no-print",
                                        style={
                                            "background": "transparent",
                                            "border": "none",
                                            "fontSize": "22px",
                                            "color": "#E11D48",
                                            "cursor": "pointer",
                                            "marginRight": "20px",
                                        },
                                    ),
                                    html.Button(
                                        html.I(
                                            id="theme-icon", className="fas fa-moon"
                                        ),
                                        id="theme-toggle",
                                        className="no-print",
                                        style={
                                            "background": "transparent",
                                            "border": "none",
                                            "fontSize": "22px",
                                            "color": "var(--text-muted)",
                                            "cursor": "pointer",
                                            "marginRight": "25px",
                                        },
                                    ),
                                ],
                                style={
                                    "textAlign": "right",
                                    "display": "flex",
                                    "alignItems": "center",
                                    "justifyContent": "flex-end",
                                },
                            ),
                            width=6,
                        ),
                    ],
                    style={"marginBottom": "30px", "marginTop": "10px"},
                ),
                dbc.Tabs(
                    id="main-tabs",
                    active_tab="tab-main",
                    children=[
                        dbc.Tab(
                            label="📈 Стандартный отчет",
                            tab_id="tab-main",
                            children=[
                                html.Div(
                                    style={"marginTop": "25px"},
                                    children=[
                                        dbc.Row(
                                            className="no-print",
                                            children=[
                                                dbc.Col(
                                                    create_kpi_card(
                                                        "ОБЩАЯ СУММА",
                                                        "kpi-sum",
                                                        "fas fa-wallet",
                                                        "#4318FF",
                                                        "rgba(67, 24, 255, 0.1)",
                                                    ),
                                                    xl=3,
                                                    lg=6,
                                                    md=6,
                                                    sm=12,
                                                    className="mb-4",
                                                ),
                                                dbc.Col(
                                                    create_kpi_card(
                                                        "УНИКАЛЬНЫХ ПАЦИЕНТОВ",
                                                        "kpi-patients",
                                                        "fas fa-user-injured",
                                                        "#FF7D00",
                                                        "rgba(255, 125, 0, 0.1)",
                                                    ),
                                                    xl=3,
                                                    lg=6,
                                                    md=6,
                                                    sm=12,
                                                    className="mb-4",
                                                ),
                                                dbc.Col(
                                                    create_kpi_card(
                                                        "ОКАЗАНО УСЛУГ (МЭС)",
                                                        "kpi-mes",
                                                        "fas fa-file-medical-alt",
                                                        "#01B574",
                                                        "rgba(1, 181, 116, 0.1)",
                                                    ),
                                                    xl=3,
                                                    lg=6,
                                                    md=6,
                                                    sm=12,
                                                    className="mb-4",
                                                ),
                                                dbc.Col(
                                                    create_kpi_card(
                                                        "АКТИВНЫХ ОТДЕЛЕНИЙ",
                                                        "kpi-depts",
                                                        "fas fa-hospital",
                                                        "#39B8FF",
                                                        "rgba(57, 184, 255, 0.1)",
                                                    ),
                                                    xl=3,
                                                    lg=6,
                                                    md=6,
                                                    sm=12,
                                                    className="mb-4",
                                                ),
                                            ],
                                        ),
                                        html.Div(
                                            id="pdf-export-container",
                                            children=[
                                                dbc.Row(
                                                    [
                                                        dbc.Col(
                                                            html.Div(
                                                                [
                                                                    html.Div(
                                                                        [
                                                                            html.H4(
                                                                                "Аналитика по времени",
                                                                                id="main-chart-title",
                                                                                style={
                                                                                    "fontWeight": "800",
                                                                                    "color": "var(--text-main)",
                                                                                    "margin": "0",
                                                                                },
                                                                            ),
                                                                            html.Button(
                                                                                [html.I(className="fas fa-list-ul", style={"marginRight": "6px"}), "Сводка МЭС"],
                                                                                id="btn-show-mes-breakdown",
                                                                                className="no-print",
                                                                                style={
                                                                                    "background": "var(--chip-bg)",
                                                                                    "border": "1px solid var(--chip-border)",
                                                                                    "color": "var(--chip-text)",
                                                                                    "borderRadius": "999px",
                                                                                    "padding": "4px 14px",
                                                                                    "fontWeight": "700",
                                                                                    "cursor": "pointer",
                                                                                    "fontSize": "12px",
                                                                                    "marginLeft": "15px",
                                                                                    "transition": "all 0.2s"
                                                                                },
                                                                            style={"display": "flex", "alignItems": "center"}
                                                                            ),
                                                                            html.Button(
                                                                                [
                                                                                    html.I(
                                                                                        className="fas fa-sync-alt",
                                                                                        style={
                                                                                            "marginRight": "8px"
                                                                                        },
                                                                                    ),
                                                                                    "Сбросить выделение",
                                                                                ],
                                                                                id="btn-reset-selection",
                                                                                title="Вернуть цвета графику",
                                                                                className="no-print",
                                                                                style={
                                                                                    "background": "var(--primary-light)",
                                                                                    "border": "none",
                                                                                    "color": "var(--primary)",
                                                                                    "borderRadius": "8px",
                                                                                    "padding": "6px 12px",
                                                                                    "fontWeight": "600",
                                                                                    "cursor": "pointer",
                                                                                    "fontSize": "13px",
                                                                                },
                                                                            ),
                                                                        ],
                                                                        style={
                                                                            "display": "flex",
                                                                            "justifyContent": "space-between",
                                                                            "alignItems": "center",
                                                                            "marginBottom": "15px",
                                                                        },
                                                                    ),
                                                                    dcc.Loading(
                                                                        type="dot",
                                                                        color="var(--primary)",
                                                                        overlay_style={
                                                                            "visibility": "visible",
                                                                            "filter": "blur(2px)",
                                                                            "opacity": 0.6,
                                                                            "transition": "all 0.3s ease",
                                                                        },
                                                                        children=[
                                                                            html.Div(
                                                                                id="smart-insights-container",
                                                                                style={
                                                                                    "marginBottom": "20px",
                                                                                    "padding": "16px 20px",
                                                                                    "backgroundColor": "var(--primary-light)",
                                                                                    "borderRadius": "14px",
                                                                                    "border": "1px solid var(--grid-color)",
                                                                                },
                                                                            ),
                                                                            dcc.Graph(
                                                                                id="main-line-chart",
                                                                                config={
                                                                                    "displayModeBar": False
                                                                                },
                                                                                style={
                                                                                    "height": "550px"
                                                                                },
                                                                            ),
                                                                            html.Div(
                                                                                id="active-filters-bar",
                                                                                style={
                                                                                    "marginTop": "10px",
                                                                                    "display": "flex",
                                                                                    "flexWrap": "wrap",
                                                                                    "gap": "8px",
                                                                                    "fontSize": "12px",
                                                                                },
                                                                            ),
                                                                        ],
                                                                    ),
                                                                ],
                                                                style={
                                                                    "backgroundColor": "var(--card-bg)",
                                                                    "borderRadius": "24px",
                                                                    "padding": "35px",
                                                                    "boxShadow": "var(--shadow)",
                                                                    "marginBottom": "25px",
                                                                },
                                                            ),
                                                            width=12,
                                                        )
                                                    ]
                                                ),
                                                dbc.Row(
                                                    className="mt-4 no-print",
                                                    children=[
                                                        dbc.Col(
                                                            html.Div(
                                                                [
                                                                    html.H4(
                                                                        [
                                                                            html.I(
                                                                                className="fas fa-terminal",
                                                                                style={
                                                                                    "marginRight": "12px",
                                                                                    "color": "var(--primary)",
                                                                                },
                                                                            ),
                                                                            "SQL-Песочница",
                                                                        ],
                                                                        style={
                                                                            "fontWeight": "800",
                                                                            "color": "var(--text-main)",
                                                                            "marginBottom": "15px",
                                                                        },
                                                                    ),
                                                                    html.P(
                                                                        "Напишите ваш SQL-запрос.",
                                                                        style={
                                                                            "color": "var(--text-muted)",
                                                                            "fontSize": "14px",
                                                                            "marginBottom": "20px",
                                                                        },
                                                                    ),
                                                                    html.Div(
                                                                        style={
                                                                            "position": "relative",
                                                                            "width": "100%",
                                                                        },
                                                                        children=[
                                                                            dcc.Textarea(
                                                                                id="sql-input",
                                                                                className="sql-editor",
                                                                                style={
                                                                                    "resize": "none",
                                                                                    "paddingRight": "50px",
                                                                                },
                                                                                placeholder="Введите ваш SQL запрос...",
                                                                                value="SELECT \n  [Наименование отделения], \n  COUNT(*) as [Количество услуг] \nFROM medical_data \nGROUP BY [Наименование отделения] \nORDER BY [Количество услуг] DESC \nLIMIT 7;",
                                                                            ),
                                                                            html.Button(
                                                                                html.I(
                                                                                    className="fas fa-expand"
                                                                                ),
                                                                                id="btn-expand-sql",
                                                                                n_clicks=0,
                                                                                title="Полноэкранный редактор",
                                                                                className="no-print",
                                                                                style={
                                                                                    "position": "absolute",
                                                                                    "top": "12px",
                                                                                    "right": "12px",
                                                                                    "background": "var(--primary-light)",
                                                                                    "border": "none",
                                                                                    "borderRadius": "8px",
                                                                                    "padding": "8px 12px",
                                                                                    "color": "var(--primary)",
                                                                                    "fontSize": "16px",
                                                                                    "cursor": "pointer",
                                                                                    "transition": "all 0.3s",
                                                                                    "zIndex": "10",
                                                                                },
                                                                            ),
                                                                        ],
                                                                    ),
                                                                    dbc.Button(
                                                                        [
                                                                            html.I(
                                                                                className="fas fa-play",
                                                                                style={
                                                                                    "marginRight": "10px"
                                                                                },
                                                                            ),
                                                                            "Выполнить SQL",
                                                                        ],
                                                                        id="btn-execute-sql",
                                                                        n_clicks=0,
                                                                        style={
                                                                            "backgroundColor": "var(--primary)",
                                                                            "border": "none",
                                                                            "borderRadius": "12px",
                                                                            "padding": "12px 24px",
                                                                            "fontWeight": "600",
                                                                            "marginTop": "15px",
                                                                        },
                                                                    ),
                                                                    html.Div(
                                                                        id="sql-error",
                                                                        style={
                                                                            "color": "#E11D48",
                                                                            "marginTop": "15px",
                                                                            "fontWeight": "600",
                                                                            "fontSize": "14px",
                                                                        },
                                                                    ),
                                                                    html.Div(
                                                                        id="auto-insights-container",
                                                                        style={
                                                                            "marginTop": "20px"
                                                                        },
                                                                    ),
                                                                ],
                                                                style={
                                                                    "backgroundColor": "var(--card-bg)",
                                                                    "borderRadius": "24px",
                                                                    "padding": "35px",
                                                                    "boxShadow": "var(--shadow)",
                                                                    "height": "100%",
                                                                },
                                                            ),
                                                            xl=8,
                                                            lg=12,
                                                            className="mb-4",
                                                        ),
                                                        dbc.Col(
                                                            html.Div(
                                                                [
                                                                    html.H5(
                                                                        [
                                                                            html.I(
                                                                                className="fas fa-database",
                                                                                style={
                                                                                    "marginRight": "10px",
                                                                                    "color": "#01B574",
                                                                                },
                                                                            ),
                                                                            "Схема Данных",
                                                                        ],
                                                                        style={
                                                                            "fontWeight": "800",
                                                                            "color": "var(--text-main)",
                                                                            "marginBottom": "25px",
                                                                        },
                                                                    ),
                                                                    html.Div(
                                                                        [
                                                                            html.Span(
                                                                                "Таблица:",
                                                                                style={
                                                                                    "color": "var(--text-muted)",
                                                                                    "fontSize": "13px",
                                                                                    "fontWeight": "600",
                                                                                    "textTransform": "uppercase",
                                                                                    "marginRight": "10px",
                                                                                },
                                                                            ),
                                                                            html.Span(
                                                                                "medical_data",
                                                                                style={
                                                                                    "color": "var(--primary)",
                                                                                    "fontWeight": "700",
                                                                                    "fontSize": "16px",
                                                                                    "backgroundColor": "var(--primary-light)",
                                                                                    "padding": "4px 10px",
                                                                                    "borderRadius": "8px",
                                                                                },
                                                                            ),
                                                                        ],
                                                                        style={
                                                                            "marginBottom": "25px"
                                                                        },
                                                                    ),
                                                                    html.P(
                                                                        "Доступные колонки:",
                                                                        style={
                                                                            "color": "var(--text-muted)",
                                                                            "fontSize": "13px",
                                                                            "fontWeight": "600",
                                                                            "textTransform": "uppercase",
                                                                            "marginBottom": "15px",
                                                                        },
                                                                    ),
                                                                    html.Div(render_schema_badges()),
                                                                    html.Div(
                                                                        [
                                                                            html.I(
                                                                                className="fas fa-lightbulb",
                                                                                id="easter-egg-trigger",
                                                                                n_clicks=0,
                                                                                style={
                                                                                    "marginRight": "8px",
                                                                                    "color": "#FF7D00",
                                                                                    "cursor": "default",
                                                                                    "transition": "transform 0.2s",
                                                                                },
                                                                            ),
                                                                            html.Span(
                                                                                "Если в названии колонки есть пробелы, оборачивайте её в квадратные скобки: ",
                                                                                style={
                                                                                    "color": "var(--text-muted)"
                                                                                },
                                                                            ),
                                                                            html.Code(
                                                                                "[Наименование отделения]",
                                                                                style={
                                                                                    "color": "var(--text-main)",
                                                                                    "fontWeight": "600",
                                                                                },
                                                                            ),
                                                                        ],
                                                                        style={
                                                                            "marginTop": "30px",
                                                                            "fontSize": "13px",
                                                                            "backgroundColor": "var(--bg-color)",
                                                                            "padding": "15px",
                                                                            "borderRadius": "12px",
                                                                            "border": "1px solid var(--grid-color)",
                                                                        },
                                                                    ),
                                                                ],
                                                                style={
                                                                    "backgroundColor": "var(--card-bg)",
                                                                    "borderRadius": "24px",
                                                                    "padding": "35px",
                                                                    "boxShadow": "var(--shadow)",
                                                                    "height": "100%",
                                                                },
                                                            ),
                                                            width=4,
                                                        ),
                                                    ],
                                                ),
                                            ],
                                        ),
                                    ],
                                )
                            ],
                        ),
                        dbc.Tab(
                            label="🧪 Улучшенная аналитика",
                            tab_id="tab-beta",
                            children=[
                                html.Div(
                                    style={"marginTop": "25px"},
                                    children=[
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    html.Div(
                                                        [
                                                            html.Div(
                                                                [
                                                                    html.H4(
                                                                        [
                                                                            html.I(
                                                                                className="fas fa-th-large",
                                                                                style={
                                                                                    "color": "#4318FF",
                                                                                    "marginRight": "12px",
                                                                                },
                                                                            ),
                                                                            "Дерево показателей (Treemap)",
                                                                        ],
                                                                        style={
                                                                            "fontWeight": "800",
                                                                            "color": "var(--text-main)",
                                                                            "margin": "0",
                                                                        },
                                                                    ),
                                                                    html.Div(
                                                                        [
                                                                            dbc.Checklist(
                                                                                options=[
                                                                                    {
                                                                                        "label": "Сетка (Одинаковые размеры)",
                                                                                        "value": "equal",
                                                                                    }
                                                                                ],
                                                                                id="treemap-mode",
                                                                                value=[],
                                                                                switch=True,
                                                                                inline=True,
                                                                                style={
                                                                                    "color": "var(--text-muted)",
                                                                                    "fontWeight": "600",
                                                                                    "marginRight": "20px",
                                                                                },
                                                                            ),
                                                                            html.Button(
                                                                                html.I(
                                                                                    className="fas fa-expand-arrows-alt"
                                                                                ),
                                                                                id="btn-expand-treemap",
                                                                                title="Растянуть в высоту",
                                                                                className="no-print",
                                                                                style={
                                                                                    "background": "rgba(67, 24, 255, 0.1)",
                                                                                    "border": "none",
                                                                                    "borderRadius": "8px",
                                                                                    "padding": "8px 12px",
                                                                                    "color": "var(--primary)",
                                                                                    "cursor": "pointer",
                                                                                    "fontSize": "16px",
                                                                                },
                                                                            ),
                                                                        ],
                                                                        style={
                                                                            "display": "flex",
                                                                            "alignItems": "center",
                                                                        },
                                                                    ),
                                                                ],
                                                                style={
                                                                    "display": "flex",
                                                                    "justifyContent": "space-between",
                                                                    "alignItems": "center",
                                                                    "marginBottom": "15px",
                                                                },
                                                            ),
                                                            dcc.Loading(
                                                                type="dot",
                                                                color="#4318FF",
                                                                overlay_style={
                                                                    "visibility": "visible",
                                                                    "filter": "blur(2px)",
                                                                    "opacity": 0.6,
                                                                    "transition": "all 0.3s ease",
                                                                },
                                                                children=dcc.Graph(
                                                                    id="sunburst-chart",
                                                                    config={
                                                                        "displayModeBar": False
                                                                    },
                                                                    style={
                                                                        "height": "500px",
                                                                        "transition": "height 0.4s ease",
                                                                    },
                                                                ),
                                                            ),
                                                        ],
                                                        style={
                                                            "backgroundColor": "var(--card-bg)",
                                                            "borderRadius": "24px",
                                                            "padding": "35px",
                                                            "boxShadow": "var(--shadow)",
                                                            "marginBottom": "25px",
                                                        },
                                                    ),
                                                    width=12,
                                                )
                                            ]
                                        ),
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    html.Div(
                                                        [
                                                            html.H4(
                                                                [
                                                                    html.I(
                                                                        className="fas fa-fire",
                                                                        style={
                                                                            "color": "#E11D48",
                                                                            "marginRight": "12px",
                                                                        },
                                                                    ),
                                                                    "Тепловая карта",
                                                                ],
                                                                style={
                                                                    "fontWeight": "800",
                                                                    "color": "var(--text-main)",
                                                                    "marginBottom": "15px",
                                                                },
                                                            ),
                                                            dcc.Loading(
                                                                type="dot",
                                                                color="#E11D48",
                                                                overlay_style={
                                                                    "visibility": "visible",
                                                                    "filter": "blur(2px)",
                                                                    "opacity": 0.6,
                                                                    "transition": "all 0.3s ease",
                                                                },
                                                                children=dcc.Graph(
                                                                    id="heatmap-chart",
                                                                    config={
                                                                        "displayModeBar": False
                                                                    },
                                                                ),
                                                            ),
                                                        ],
                                                        style={
                                                            "backgroundColor": "var(--card-bg)",
                                                            "borderRadius": "24px",
                                                            "padding": "35px",
                                                            "boxShadow": "var(--shadow)",
                                                            "marginBottom": "25px",
                                                        },
                                                    ),
                                                    width=12,
                                                )
                                            ]
                                        ),
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    html.Div(
                                                        [
                                                            html.Div(
                                                                [
                                                                    html.H4(
                                                                        [
                                                                            html.I(
                                                                                className="fas fa-table",
                                                                                style={
                                                                                    "color": "#01B574",
                                                                                    "marginRight": "12px",
                                                                                },
                                                                            ),
                                                                            "Сводная таблица (Конструктор)",
                                                                        ],
                                                                        style={
                                                                            "fontWeight": "800",
                                                                            "margin": "0",
                                                                        },
                                                                    ),
                                                                    html.Div(
                                                                        [
                                                                            html.Button(
                                                                                [
                                                                                    html.I(
                                                                                        className="fas fa-times",
                                                                                        style={
                                                                                            "marginRight": "8px"
                                                                                        },
                                                                                    ),
                                                                                    "Сбросить фильтр",
                                                                                ],
                                                                                id="btn-reset-crossfilter",
                                                                                style={
                                                                                    "background": "rgba(225, 29, 72, 0.1)",
                                                                                    "border": "1px solid #E11D48",
                                                                                    "color": "#E11D48",
                                                                                    "borderRadius": "8px",
                                                                                    "padding": "6px 12px",
                                                                                    "fontWeight": "600",
                                                                                    "marginRight": "15px",
                                                                                },
                                                                            ),
                                                                            html.Button(
                                                                                html.I(
                                                                                    className="fas fa-file-csv"
                                                                                ),
                                                                                id="btn-export-grid",
                                                                                n_clicks=0,
                                                                                title="Скачать таблицу (CSV)",
                                                                                className="no-print",
                                                                                style={
                                                                                    "background": "transparent",
                                                                                    "border": "none",
                                                                                    "fontSize": "22px",
                                                                                    "color": "#01B574",
                                                                                    "cursor": "pointer",
                                                                                },
                                                                            ),
                                                                        ],
                                                                        style={
                                                                            "display": "flex",
                                                                            "alignItems": "center",
                                                                        },
                                                                    ),
                                                                ],
                                                                style={
                                                                    "display": "flex",
                                                                    "justifyContent": "space-between",
                                                                    "alignItems": "center",
                                                                    "marginBottom": "15px",
                                                                },
                                                            ),
                                                            html.Div(
                                                                id="crossfilter-msg",
                                                                style={
                                                                    "color": "#E11D48",
                                                                    "fontWeight": "700",
                                                                    "marginBottom": "15px",
                                                                },
                                                            ),
                                                            dcc.Loading(
                                                                type="dot",
                                                                color="#01B574",
                                                                overlay_style={
                                                                    "visibility": "visible",
                                                                    "filter": "blur(2px)",
                                                                    "opacity": 0.6,
                                                                    "transition": "all 0.3s ease",
                                                                },
                                                                children=html.Div(
                                                                    id="ag-grid-container",
                                                                    style={
                                                                        "width": "100%"
                                                                    },
                                                                ),
                                                            ),
                                                        ],
                                                        style={
                                                            "backgroundColor": "var(--card-bg)",
                                                            "borderRadius": "24px",
                                                            "padding": "35px",
                                                            "boxShadow": "var(--shadow)",
                                                        },
                                                    ),
                                                    width=12,
                                                )
                                            ]
                                        ),
                                    ],
                                )
                            ],
                        ),
                        dbc.Tab(
                            label="💼 Бизнес-аналитика",
                            tab_id="tab-abc",
                            children=[
                                html.Div(
                                    style={"marginTop": "25px"},
                                    children=[
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    html.Div(
                                                        [
                                                            html.Div(
                                                                [
                                                                    html.H4(
                                                                        [
                                                                            html.I(
                                                                                className="fas fa-chart-pie",
                                                                                style={
                                                                                    "color": "#4318FF",
                                                                                    "marginRight": "12px",
                                                                                },
                                                                            ),
                                                                            "ABC-Анализ выручки",
                                                                        ],
                                                                        style={
                                                                            "fontWeight": "800",
                                                                            "margin": "0",
                                                                        },
                                                                    ),
                                                                    html.Button(
                                                                        html.I(
                                                                            className="fas fa-file-excel"
                                                                        ),
                                                                        id="btn-export-abc",
                                                                        n_clicks=0,
                                                                        title="Скачать цветной Excel",
                                                                        className="no-print",
                                                                        style={
                                                                            "background": "transparent",
                                                                            "border": "none",
                                                                            "fontSize": "22px",
                                                                            "color": "#01B574",
                                                                            "cursor": "pointer",
                                                                        },
                                                                    ),
                                                                ],
                                                                style={
                                                                    "display": "flex",
                                                                    "justifyContent": "space-between",
                                                                    "alignItems": "center",
                                                                    "marginBottom": "15px",
                                                                },
                                                            ),
                                                            html.P(
                                                                "Классификация по правилу Парето (Группа А: приносит 80% выручки, Группа В: 15%, Группа С: 5%).",
                                                                style={
                                                                    "color": "var(--text-muted)",
                                                                    "marginBottom": "20px",
                                                                },
                                                            ),
                                                            html.Label(
                                                                "Сгруппировать по:",
                                                                style={
                                                                    "color": "var(--text-main)",
                                                                    "fontWeight": "600",
                                                                    "fontSize": "13px",
                                                                },
                                                            ),
                                                            dcc.Dropdown(
                                                                id="abc-group-by",
                                                                options=[
                                                                    {
                                                                        "label": "📋 По кодам МЭС",
                                                                        "value": "Код Услуги",
                                                                    },
                                                                    {
                                                                        "label": "🏥 По отделениям",
                                                                        "value": "Наименование отделения",
                                                                    },
                                                                    {
                                                                        "label": "🩺 По профилям",
                                                                        "value": "Наименование профиля",
                                                                    },
                                                                ],
                                                                value="Код Услуги",
                                                                clearable=False,
                                                                style={
                                                                    "marginBottom": "25px",
                                                                    "width": "50%",
                                                                },
                                                            ),
                                                            dcc.Loading(
                                                                type="dot",
                                                                color="#4318FF",
                                                                overlay_style={
                                                                    "visibility": "visible",
                                                                    "filter": "blur(2px)",
                                                                    "opacity": 0.6,
                                                                    "transition": "all 0.3s ease",
                                                                },
                                                                children=html.Div(
                                                                    id="abc-grid-container",
                                                                    style={
                                                                        "width": "100%"
                                                                    },
                                                                ),
                                                            ),
                                                            dcc.Download(
                                                                id="download-abc-xlsx"
                                                            ),
                                                        ],
                                                        style={
                                                            "backgroundColor": "var(--card-bg)",
                                                            "borderRadius": "24px",
                                                            "padding": "35px",
                                                            "boxShadow": "var(--shadow)",
                                                        },
                                                    ),
                                                    width=12,
                                                )
                                            ]
                                        )
                                    ],
                                )
                            ],
                        ),
                    ],
                ),
            ],
        ),
        html.Div(
            id="selection-modal",
            style={"display": "none"},
            children=[
                html.Div(
                    style={
                        "position": "fixed",
                        "bottom": "30px",
                        "right": "30px",
                        "backgroundColor": "var(--card-bg)",
                        "padding": "25px",
                        "borderRadius": "16px",
                        "boxShadow": "0px 20px 50px rgba(0,0,0,0.3)",
                        "zIndex": "9999",
                        "width": "350px",
                        "border": "2px solid var(--primary)",
                        "color": "var(--text-main)",
                    },
                    children=[
                        html.Div(
                            [
                                html.I(
                                    className="fas fa-chart-pie",
                                    style={
                                        "color": "var(--primary)",
                                        "marginRight": "10px",
                                        "fontSize": "20px",
                                    },
                                ),
                                html.B(
                                    "Аналитика по выбору", style={"fontSize": "18px"}
                                ),
                            ],
                            style={
                                "marginBottom": "15px",
                                "borderBottom": "1px solid var(--grid-color)",
                                "paddingBottom": "10px",
                            },
                        ),
                        html.Div(
                            id="selection-modal-content",
                            style={"fontSize": "15px", "lineHeight": "1.8"},
                        ),
                        html.Button(
                            "Закрыть",
                            id="btn-close-modal",
                            n_clicks=0,
                            style={
                                "marginTop": "20px",
                                "width": "100%",
                                "padding": "10px",
                                "backgroundColor": "var(--primary)",
                                "color": "white",
                                "border": "none",
                                "borderRadius": "10px",
                                "cursor": "pointer",
                                "fontWeight": "bold",
                            },
                        ),
                    ],
                )
            ],
        ),
        dbc.Modal(
            [
                dbc.ModalHeader(
                    dbc.ModalTitle(
                        "Расширенная информация",
                        id="modal-title",
                        style={"fontWeight": "800", "color": "var(--primary)"},
                    )
                ),
                dbc.ModalBody(id="modal-body", style={"padding": "25px"}),
                dbc.ModalFooter(
                    dbc.Button(
                        "Закрыть",
                        id="close-modal",
                        className="ms-auto",
                        style={"borderRadius": "12px"},
                    )
                ),
            ],
            id="drilldown-modal",
            is_open=False,
            size="lg",
            centered=True,
        ),
        dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle(id="pop-modal-title", style={"fontWeight": "800", "color": "var(--primary)"})),
                dbc.ModalBody(id="pop-modal-body", style={"padding": "25px", "backgroundColor": "var(--bg-color)"}),
                dbc.ModalFooter(dbc.Button("Закрыть", id="close-pop-modal", className="ms-auto", style={"borderRadius": "12px"})),
            ],
            id="pop-modal", is_open=False, size="lg", centered=True,
        ),
        dbc.Modal(
            [
                dbc.ModalHeader(
                    dbc.ModalTitle(
                        id="yoy-modal-title",
                        style={"fontWeight": "800", "color": "var(--primary)"},
                    )
                ),
                dbc.ModalBody(
                    id="yoy-modal-body",
                    style={"padding": "25px", "backgroundColor": "var(--bg-color)"},
                ),
                dbc.ModalFooter(
                    dbc.Button(
                        "Закрыть",
                        id="close-yoy-modal",
                        className="ms-auto",
                        style={"borderRadius": "12px"},
                    )
                ),
            ],
            id="yoy-modal",
            is_open=False,
            size="lg",
            centered=True,
        ),
        dbc.Modal(
            [
                dbc.ModalHeader(
                    dbc.ModalTitle(
                        [html.I(className="fas fa-file-medical-alt", style={"marginRight": "10px"}), "Детализация МЭС по периодам"], 
                        style={"fontWeight": "800", "color": "var(--primary)"}
                    )
                ),
                dbc.ModalBody(id="mes-breakdown-body", style={"padding": "25px", "backgroundColor": "var(--bg-color)"}),
                dbc.ModalFooter(
                    dbc.Button("Закрыть", id="close-mes-breakdown", className="ms-auto", style={"borderRadius": "12px"})
                ),
            ],
            id="mes-breakdown-modal",
            is_open=False,
            size="lg",
            centered=True,
            scrollable=True,
        ),

        dbc.Modal(
            [
                dbc.ModalHeader(
                    dbc.ModalTitle(
                        [
                            html.I(
                                className="fas fa-code", style={"marginRight": "10px"}
                            ),
                            "Продвинутый SQL-Редактор",
                        ],
                        style={"fontWeight": "800", "color": "var(--primary)"},
                    )
                ),
                dbc.ModalBody(
                    dbc.Row(
                        [
                            dbc.Col(
                                html.Div(
                                    [
                                        dcc.Textarea(
                                            id="sql-modal-input",
                                            className="sql-editor",
                                            style={
                                                "height": "480px",
                                                "resize": "none",
                                                "fontSize": "16px",
                                                "padding": "20px",
                                            },
                                        ),
                                        html.Div(
                                            id="sql-modal-linter",
                                            style={
                                                "marginTop": "8px",
                                                "fontSize": "13px",
                                                "fontWeight": "600",
                                                "minHeight": "20px",
                                            },
                                        ),
                                    ]
                                ),
                                width=8,
                            ),
                            dbc.Col(
                                html.Div(
                                    [
                                        html.H5(
                                            [
                                                html.I(
                                                    className="fas fa-table",
                                                    style={
                                                        "marginRight": "10px",
                                                        "color": "#01B574",
                                                    },
                                                ),
                                                "Схема: medical_data",
                                            ],
                                            style={
                                                "fontWeight": "800",
                                                "color": "var(--text-main)",
                                                "marginBottom": "20px",
                                            },
                                        ),
                                        html.P(
                                            "Доступные колонки:",
                                            style={
                                                "color": "var(--text-muted)",
                                                "fontSize": "13px",
                                                "fontWeight": "600",
                                                "textTransform": "uppercase",
                                                "marginBottom": "15px",
                                            },
                                        ),
                                        html.Div(render_schema_badges()),
                                        html.Div(
                                            [
                                                html.I(
                                                    className="fas fa-lightbulb",
                                                    style={
                                                        "marginRight": "8px",
                                                        "color": "#FF7D00",
                                                    },
                                                ),
                                                html.Span(
                                                    "Если в названии колонки есть пробелы, оборачивайте её в квадратные скобки: ",
                                                    style={
                                                        "color": "var(--text-muted)"
                                                    },
                                                ),
                                                html.Code(
                                                    "[Наименование отделения]",
                                                    style={
                                                        "color": "var(--text-main)",
                                                        "fontWeight": "600",
                                                    },
                                                ),
                                            ],
                                            style={
                                                "marginTop": "30px",
                                                "fontSize": "13px",
                                                "backgroundColor": "var(--bg-color)",
                                                "padding": "15px",
                                                "borderRadius": "12px",
                                                "border": "1px solid var(--grid-color)",
                                            },
                                        ),
                                    ],
                                    style={
                                        "backgroundColor": "var(--bg-color)",
                                        "borderRadius": "16px",
                                        "padding": "25px",
                                        "height": "100%",
                                        "border": "1px solid var(--grid-color)",
                                    },
                                ),
                                width=4,
                            ),
                        ]
                    )
                ),
                dbc.ModalFooter(
                    [
                        dbc.Button(
                            "Отмена",
                            id="btn-close-sql-modal",
                            n_clicks=0,
                            style={
                                "backgroundColor": "transparent",
                                "border": "none",
                                "color": "var(--text-muted)",
                                "fontWeight": "600",
                                "marginRight": "15px",
                            },
                        ),
                        dbc.Button(
                            [
                                html.I(
                                    className="fas fa-save",
                                    style={"marginRight": "8px"},
                                ),
                                "Сохранить и Применить",
                            ],
                            id="btn-save-sql-modal",
                            n_clicks=0,
                            style={
                                "backgroundColor": "var(--primary)",
                                "border": "none",
                                "borderRadius": "12px",
                                "fontWeight": "600",
                                "padding": "10px 20px",
                            },
                        ),
                    ]
                ),
            ],
            id="sql-editor-modal",
            is_open=False,
            size="xl",
            centered=True,
            backdrop="static",
        ),
        dbc.Modal(
            [
                dbc.ModalHeader(
                    dbc.ModalTitle(
                        id="patient-modal-title",
                        style={
                            "fontWeight": "800",
                            "color": "var(--primary)",
                            "fontSize": "22px",
                        },
                    )
                ),
                dbc.ModalBody(
                    id="patient-modal-body",
                    style={"padding": "30px", "backgroundColor": "var(--bg-color)"},
                ),
                dbc.ModalFooter(
                    dbc.Button(
                        "Закрыть",
                        id="close-patient-modal",
                        className="ms-auto",
                        style={"borderRadius": "12px"},
                    )
                ),
            ],
            id="patient-modal",
            is_open=False,
            size="xl",
            centered=True,
        ),
        dbc.Modal(
            [
                dbc.ModalHeader(
                    dbc.ModalTitle(
                        [
                            html.I(className="fas fa-book-open", style={"marginRight": "10px"}),
                            "Руководство пользователя",
                        ],
                        style={"fontWeight": "800", "color": "var(--primary)"},
                    )
                ),
                dbc.ModalBody(
                    style={"padding": "30px", "backgroundColor": "var(--bg-color)"},
                    children=[
                        html.H5("📈 Стандартный отчет", style={"fontWeight": "800", "color": "var(--text-main)", "marginBottom": "15px"}),
                        html.Ul([
                            html.Li("Выберите нужные метрики и разрезы в левой панели."),
                            html.Li([html.B("Интерактивный график: "), "Кликните на любую точку на графике, чтобы открыть ", html.B("глубокую детализацию"), " с Топ-10 значений и медианой."]),
                            html.Li([html.B("Множественное выделение: "), "Зажмите клавишу ", html.B("Shift"), " и кликайте по нужным точкам, чтобы получить суммарную аналитику по выбранным элементам."]),
                            html.Li([html.B("Сравнение (YoY): "), "Включите тумблер в левой панели для сравнения текущих фильтров с аналогичным периодом прошлого года."]),
                            html.Li([html.B("SQL-Песочница: "), "Продвинутый инструмент для написания собственных SQL-запросов. Кликните по иконке расширения для удобной работы в полном экране."]),
                        ], style={"color": "var(--text-main)", "marginBottom": "25px", "lineHeight": "1.6"}),

                        html.H5("🧪 Улучшенная аналитика", style={"fontWeight": "800", "color": "var(--text-main)", "marginBottom": "15px"}),
                        html.Ul([
                            html.Li([html.B("Дерево показателей: "), "Иерархическое отображение выручки. Кликните на сектор, чтобы углубиться в него. Переключатель 'Сетка' позволяет увидеть распределение по количеству услуг, а не по сумме."]),
                            html.Li([html.B("Тепловая карта (Heatmap): "), "Показывает активность отделений по месяцам. Чем темнее цвет, тем выше активность."]),
                            html.Li([html.B("Сводная таблица: "), "Мощный конструктор отчетов. Перетаскивайте колонки в панель группировки, фильтруйте значения и экспортируйте результат в CSV (иконка Excel)."]),
                        ], style={"color": "var(--text-main)", "marginBottom": "25px", "lineHeight": "1.6"}),

                        html.H5("💼 Бизнес-аналитика", style={"fontWeight": "800", "color": "var(--text-main)", "marginBottom": "15px"}),
                        html.Ul([
                            html.Li([html.B("ABC-Анализ: "), "Автоматическое распределение объектов (отделений, профилей, МЭС) по принципу Парето: Группа А (80% выручки), В (15%) и С (5%)."]),
                            html.Li("Используйте кнопку скачивания для получения цветного Excel-файла с результатами анализа."),
                        ], style={"color": "var(--text-main)", "marginBottom": "25px", "lineHeight": "1.6"}),
                        
                        html.H5("🧑 Карточка пациента", style={"fontWeight": "800", "color": "var(--text-main)", "marginBottom": "15px"}),
                        html.Ul([
                            html.Li("Введите номер истории болезни (ИБ) в левой панели и нажмите Enter."),
                            html.Li("Система соберет всю историю визитов, сгруппирует услуги по месяцам и покажет итоговую аналитику."),
                        ], style={"color": "var(--text-main)", "marginBottom": "10px", "lineHeight": "1.6"}),
                    ]
                ),
                dbc.ModalFooter(
                    dbc.Button(
                        "Понятно",
                        id="btn-close-help",
                        n_clicks=0,
                        className="ms-auto",
                        style={"borderRadius": "12px", "backgroundColor": "var(--primary)", "border": "none"},
                    )
                ),
            ],
            id="help-modal",
            is_open=False,
            size="lg",
            centered=True,
        ),
        html.Div(
            id="rocket-container",
            className="rocket-easter-egg",
            children=[
                html.Div(
                    "Вот так выглядят успехи нашей больницы! 🚀",
                    style={
                        "fontSize": "22px",
                        "fontWeight": "900",
                        "color": "#ffffff",
                        "backgroundColor": "var(--primary)",
                        "padding": "12px 30px",
                        "borderRadius": "8px",
                        "border": "3px dashed #ffffff",
                        "boxShadow": "0 10px 25px rgba(0,0,0,0.4)",
                        "marginRight": "15px",
                        "whiteSpace": "nowrap"
                    }
                ),
                html.Div(className="rocket-flame"),
                html.I(
                    className="fas fa-rocket", 
                    style={
                        "fontSize": "110px", 
                        "color": "#E11D48", 
                        "transform": "rotate(45deg)", 
                        "filter": "drop-shadow(5px 5px 10px rgba(0,0,0,0.3))"
                    }
                )
            ]
        ),
        html.Div(
            id="godzilla-container",
            className="godzilla-easter-egg",
            children=[
                html.Div("ROOOAAAR! 📉", className="roar-bubble"),
                html.I(className="fas fa-dragon godzilla-icon")
            ]
        ),
    ]
)