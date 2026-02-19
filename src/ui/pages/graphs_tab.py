from datetime import datetime, timedelta
import locale
from dateutil.relativedelta import relativedelta
import traceback
import flet as ft
import re
import src.database.admin.select_server as select_server


def graphs_tab(page):
    date_picker_from = ft.DatePicker(
        first_date=datetime(2023, 1, 1),
        last_date=datetime.now() + timedelta(days=365),
    )
    date_picker_to = ft.DatePicker(
        first_date=datetime(2023, 1, 1),
        last_date=datetime.now() + timedelta(days=365),
    )
    page.overlay.extend([date_picker_from, date_picker_to])

    date_from = ft.TextField(
        hint_text="Дата от",
        border_radius=10,
        border_color=ft.colors.GREY_300,
        focused_border_color=ft.colors.PRIMARY,
        bgcolor=ft.colors.WHITE,
        height=50,
        # text_align=ft.TextAlign.CENTER,
        text_vertical_align=ft.VerticalAlignment.CENTER,
        suffix=ft.IconButton(
            icon=ft.icons.CALENDAR_MONTH,
            on_click=lambda _: page.open(date_picker_from),
            icon_color=ft.colors.GREY_600
        ),
        hint_style=ft.TextStyle(color=ft.colors.GREY_600),
        text_style=ft.TextStyle(color=ft.colors.BLACK)
    )

    date_to = ft.TextField(
        hint_text="Дата до",
        border_radius=10,
        border_color=ft.colors.GREY_300,
        focused_border_color=ft.colors.PRIMARY,
        bgcolor=ft.colors.WHITE,
        height=50,
        text_vertical_align=ft.VerticalAlignment.CENTER,
        suffix=ft.IconButton(
            icon=ft.icons.CALENDAR_MONTH,
            on_click=lambda _: page.open(date_picker_to),
            icon_color=ft.colors.GREY_600
        ),
        hint_style=ft.TextStyle(color=ft.colors.GREY_600),
        text_style=ft.TextStyle(color=ft.colors.BLACK)
    )

    def update_date_from(e):
        if date_picker_from.value:
            date_from.value = date_picker_from.value.strftime("%d.%m.%Y")
            page.update()

    def update_date_to(e):
        if date_picker_to.value:
            date_to.value = date_picker_to.value.strftime("%d.%m.%Y")
            page.update()

    date_picker_from.on_change = update_date_from
    date_picker_to.on_change = update_date_to

    employees = ft.Dropdown(
        options=[ft.dropdown.Option(text="Все сотрудники")],
        value="Все сотрудники",
        expand=True,
        width=280,
        border_radius=10,
        border_color=ft.colors.GREY_300,
        focused_border_color=ft.colors.PRIMARY,
        bgcolor=ft.colors.WHITE,
        text_style=ft.TextStyle(color=ft.colors.BLACK),
        hint_text="Сотрудники"
    )

    def parse_date(date_str):
        try:
            return datetime.strptime(date_str, "%d.%m.%Y").date()
        except ValueError:
            return None

    def load_data(force_all=False):
        try:
            start_date = parse_date(date_from.value) if not force_all and date_from.value else None
            end_date = parse_date(date_to.value) if not force_all and date_to.value else None
            employee_id = int(employees.value) if not force_all and employees.value != "Все сотрудники" else None

            data = select_server.get_dashboard_stats_data(
                start_date=start_date,
                end_date=end_date,
                employee_id=employee_id
            )
            return data
        except Exception as e:
            print("Ошибка в load_data:", traceback.format_exc())
            return None

    graphs_column = ft.Column(
        scroll=ft.ScrollMode.AUTO,
        expand=True,
        # spacing=20,
    )

    def create_pie_chart(data):
        status_colors = {
            "не выполнен": ft.colors.BLUE,
            "выполнен": ft.colors.GREEN,
            "в исполнении": ft.colors.ORANGE,
            "просрочен": ft.colors.RED
        }

        filtered_data = [item for item in data if item['count'] > 0]
        if not filtered_data:
            # Обертка в Row с центрированием
            return ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Text("Нет данных для отображения", size=24),
                        alignment=ft.alignment.center,
                        height=550,
                        width=800,
                        bgcolor=ft.colors.WHITE,
                        border_radius=15,
                        padding=20,
                    )
                ],
                alignment=ft.MainAxisAlignment.CENTER,  # Центр по горизонтали
                vertical_alignment=ft.CrossAxisAlignment.CENTER,  # Центр по вертикали
                expand=True  # Занимаем всё пространство
            )

        total = sum(item['count'] for item in filtered_data)
        normal_radius = 90
        hover_radius = 100

        sections = []
        for item in filtered_data:
            percent = (item['count'] / total) * 100
            sections.append(
                ft.PieChartSection(
                    percent,
                    title=f"{item['count']} ({round(percent)}%)",
                    title_style=ft.TextStyle(
                        size=0,  # Изначально скрываем текст
                        color=ft.colors.WHITE,
                        weight=ft.FontWeight.BOLD
                    ),
                    color=status_colors.get(item['status'], ft.colors.GREY),
                    radius=normal_radius
                )
            )

        def on_chart_event(e: ft.PieChartEvent):
            for idx, section in enumerate(chart.sections):
                if idx == e.section_index:
                    section.radius = hover_radius
                    section.title_style = ft.TextStyle(
                        size=14,
                        color=ft.colors.WHITE,
                        weight=ft.FontWeight.BOLD,
                        shadow=ft.BoxShadow(blur_radius=2, color=ft.colors.BLACK54)
                    )
                else:
                    section.radius = normal_radius
                    section.title_style = ft.TextStyle(size=0)
            chart.update()

        chart = ft.PieChart(
            sections=sections,
            sections_space=2,
            center_space_radius=40,
            on_chart_event=on_chart_event,
            expand=True,
        )

        # Создаем легенду
        legend = ft.Row(
            wrap=True,
            spacing=20,
            run_spacing=10,
            controls=[
                ft.Row(
                    spacing=5,
                    controls=[
                        ft.Container(
                            width=20,
                            height=20,
                            bgcolor=status_colors[item['status']],
                            border_radius=5
                        ),
                        ft.Text(
                            f"{item['status']} ({item['count']})",
                            size=14,
                            color=ft.colors.BLACK87
                        )
                    ]
                ) for item in filtered_data
            ]
        )

        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(f"Всего задач: {total}",
                            size=18,
                            color=ft.colors.BLUE_GREY_600),
                    ft.Container(
                        chart,
                        height=250,
                        alignment=ft.alignment.center
                    ),
                    legend
                ],
                spacing=15,
                # horizontal_alignment=ft.CrossAxisAlignment.CENTER
            ),
            padding=20,
            expand=True,
            height=550,
            bgcolor=ft.colors.WHITE,
            border_radius=15,
        )

    def create_bar_chart(data):
        employee_stats = data.get('employee_stats', [])
        if not employee_stats:
            return ft.Container(
                content=ft.Text("Нет данных по сотрудникам"),
                alignment=ft.alignment.center
            )

        max_tasks = max(emp['completed_tasks'] for emp in employee_stats)
        bar_width = 20

        chart = ft.BarChart(
            bar_groups=[
                ft.BarChartGroup(
                    x=i,
                    bar_rods=[
                        ft.BarChartRod(
                            from_y=-0.2,
                            to_y=emp['completed_tasks'],
                            color=ft.colors.BLUE,
                            width=bar_width,
                            tooltip=f"{emp['employee_name'].replace(chr(10), ' ')}\nЗадач: {emp['completed_tasks']}",
                            border_radius=5,
                        )
                    ],
                ) for i, emp in enumerate(employee_stats)
            ],
            left_axis=ft.ChartAxis(
                labels=[
                    ft.ChartAxisLabel(
                        value=value,
                        label=ft.Text(str(int(value)), size=12),
                    ) for value in range(0, max_tasks + 2, 2)
                ],
                labels_size=20,
                title=ft.Container(  # Добавил контейнер для отступа
                    content=ft.Text("Количество задач", size=12),
                ),
            ),
            bottom_axis=ft.ChartAxis(
                labels_size=0  # Полностью скрываем нижние подписи
            ),
            horizontal_grid_lines=ft.ChartGridLines(
                color=ft.colors.GREY_300,
                width=1,
                dash_pattern=[3, 3]
            ),
            border=ft.border.all(1, ft.colors.GREY_400),
            expand=True,
        )

        return ft.Container(
            ft.Column([
                ft.Text("Статистика сотрудников", size=22, weight=ft.FontWeight.BOLD),
                ft.Container(
                    chart,
                    padding=ft.padding.only(top=20, right=20),
                    expand=True
                )
            ], expand=True, spacing=15),
            expand=True,
            height=550,
            bgcolor=ft.colors.WHITE,
            border_radius=15,
            padding=20,
            margin=ft.margin.only(10, 5, 10, 5),
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=10,
                color=ft.colors.BLUE_GREY_300,
                offset=ft.Offset(2, 2)
            ),
            visible=True
        )

    russian_months = {
        'янв': 1, 'фев': 2, 'мар': 3, 'апр': 4,
        'май': 5, 'июн': 6, 'июл': 7, 'авг': 8,
        'сен': 9, 'окт': 10, 'ноя': 11, 'дек': 12
    }

    russian_months_reversed = {v: k.upper() for k, v in russian_months.items()}

    def create_line_chart(raw_data):
        tasks_by_month = raw_data.get('tasks_by_month', [])
        parsed_data = []
        for item in tasks_by_month:
            try:
                raw_date = item['month'].strip().lower()

                # Универсальный парсинг для разных форматов
                if any(c in raw_date for c in ['-', '.', ' ']):
                    parts = re.split(r'[-\.\s]+', raw_date)
                    if len(parts) != 2:
                        raise ValueError("Некорректный формат даты")

                    month_part, year_part = parts

                    # Парсим месяц
                    if month_part.isdigit():
                        month = int(month_part)
                    else:
                        month = russian_months.get(month_part[:3])
                        if not month:
                            raise ValueError(f"Неизвестный месяц: {month_part}")

                    # Парсим год
                    year = int(year_part)

                else:
                    # Формат ГГГГММ
                    if len(raw_date) != 6 or not raw_date.isdigit():
                        raise ValueError("Некорректный формат ГГГГММ")

                    year = int(raw_date[:4])
                    month = int(raw_date[4:6])

                # Валидация диапазонов
                if not (1 <= month <= 12):
                    raise ValueError(f"Некорректный месяц: {month}")

                if year < 2000 or year > 2100:
                    raise ValueError(f"Некорректный год: {year}")

                # Создаем метку на русском
                month_label = russian_months_reversed.get(month, '???')
                label = f"{month_label} {year}".upper()

                parsed_data.append({
                    "date": datetime(year, month, 1),
                    "count": item['count'],
                    "label": label
                })

            except Exception as e:
                print(f"Ошибка обработки даты '{item['month']}': {str(e)}")
                continue

        # Сортируем данные по дате
        parsed_data.sort(key=lambda x: x['date'])

        if not parsed_data:
            return ft.Container(content=ft.Text("No data available"), padding=20)

        # Подготовка данных для осей
        counts = [item['count'] for item in parsed_data]
        labels = [item['label'] for item in parsed_data]

        min_y = 0
        max_y = max(counts) if counts else 0
        max_x = len(parsed_data) - 1

        y_step = max(1, (max_y // 5))  # 5 промежутков на оси Y
        y_labels = [
            ft.ChartAxisLabel(
                value=y,
                label=ft.Text(
                    str(y),
                    size=14,
                    weight=ft.FontWeight.BOLD,
                    color=ft.colors.BLUE_GREY_600
                )
            ) for y in range(min_y, max_y + y_step, y_step)
        ]

        total_labels = len(labels)
        label_step = max(1, total_labels // 5)  # Не более 5 меток

        # Создаем фильтрованный список меток
        filtered_labels = [
            (i, label) for i, label in enumerate(labels)
            if i % label_step == 0 or i == total_labels - 1
        ]
        # Создаем метки для оси X с поворотом текста
        x_labels = [
            ft.ChartAxisLabel(
                value=i,
                label=ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                parts[0],
                                size=10,
                                weight=ft.FontWeight.BOLD,
                                color=ft.colors.BLUE_GREY_800,
                            ),
                            ft.Text(
                                parts[1],
                                size=8,
                                color=ft.colors.BLUE_GREY_600
                            )
                        ],
                        spacing=2,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER
                    ),
                    width=80,
                    padding=ft.padding.only(bottom=10)
                )
            )
            for i, label in filtered_labels
            for parts in [label.split()]
        ]

        # Создание графика
        line_chart = ft.LineChart(
            data_series=[
                ft.LineChartData(
                    data_points=[
                        ft.LineChartDataPoint(i, count)
                        for i, count in enumerate(counts)
                    ],
                    color=ft.colors.BLUE,
                    stroke_width=4,
                    curved=True,
                    stroke_cap_round=True,
                )
            ],
            left_axis=ft.ChartAxis(
                labels=y_labels,
                labels_size=50,
            ),
            bottom_axis=ft.ChartAxis(
                labels=x_labels,
                labels_size=80,  # Увеличиваем размер области для меток
                show_labels=True,
                labels_interval=1  # Принудительно показываем все отфильтрованные метки
            ),
            horizontal_grid_lines=ft.ChartGridLines(
                color=ft.colors.GREY_300,
                width=1,
                dash_pattern=[2, 2]
            ),
            vertical_grid_lines=ft.ChartGridLines(
                color=ft.colors.GREY_300,
                width=1,
                dash_pattern=[2, 2]
            ),
            min_y=min_y,
            max_y=max_y + y_step,
            min_x=0,
            max_x=max_x,
            border=ft.border.all(1, ft.colors.GREY_400),
            height=250
        )

        return ft.Container(
            ft.Column([
                ft.Text("Динамика по месяцам", size=18, weight=ft.FontWeight.BOLD),
                ft.Container(
                    line_chart,
                    padding=ft.padding.only(top=20, right=20),
                    expand=True
                )
            ]),
            bgcolor=ft.colors.WHITE,
            border_radius=15,
            padding=20,
            margin=ft.margin.only(10, 0, 10, 10),
            expand=True,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=10,
                color=ft.colors.BLUE_GREY_300,
                offset=ft.Offset(2, 2)
            )
        )

    def create_stat_card(title, value, color):
        return ft.Container(
            ft.Column([
                ft.Text(title, size=14, color=ft.colors.GREY_600),
                ft.Text(str(value), size=24, weight=ft.FontWeight.BOLD, color=color)
            ], spacing=5),
            padding=15,
            bgcolor=ft.colors.WHITE,
            border_radius=10,
            shadow=ft.BoxShadow(blur_radius=5, color=ft.colors.GREY_300)
        )

    def update_graphs(e, initial_load=False):
        try:
            nonlocal raw_data
            raw_data = load_data(force_all=initial_load)

            if not raw_data:
                graphs_column.controls.clear()
                graphs_column.controls.append(
                    ft.Row(
                        controls=[
                            ft.Container(
                                content=ft.Column(
                                    [
                                        ft.Row(
                                            [
                                                ft.Icon(ft.icons.REFRESH, size=40),

                                            ], alignment=ft.MainAxisAlignment.CENTER
                                        ),
                                        ft.Row(
                                            [
                                                ft.Text("Нет данных для отображения", size=24),
                                            ], alignment=ft.MainAxisAlignment.CENTER
                                        )
                                    ],
                                    expand=True,
                                    alignment=ft.MainAxisAlignment.CENTER
                                ),
                                alignment=ft.alignment.center,
                                height=550,
                                width=800,
                                border_radius=15,
                                padding=20,
                            )
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,  # Центр по горизонтали
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,  # Центр по вертикали
                        expand=True  # Занимаем всё пространство
                    )
                )
                page.update()
                raise Exception("No data received")

            general_stats = raw_data.get('general_stats', {})
            stats_controls = []
            if general_stats:
                stats_controls = [
                    create_stat_card("Всего задач", general_stats.get('total_tasks', 0), ft.colors.BLUE),
                    create_stat_card("Просрочено", general_stats.get('overdue_tasks', 0), ft.colors.RED),
                    create_stat_card("Выполнено", general_stats.get('completed_tasks', 0), ft.colors.GREEN),
                    create_stat_card("Среднее время", f"{general_stats.get('avg_completion_time', 0)} дн",
                                     ft.colors.ORANGE)
                ]
            stats_row = ft.Row(stats_controls, spacing=15) if stats_controls else None

            pie_chart = create_pie_chart(raw_data['tasks_by_status'])

            line_chart = create_line_chart(raw_data)

            show_bar_chart = employees.value == "Все сотрудники"
            bar_chart_container = create_bar_chart(raw_data)

            print(show_bar_chart)
            print(employees.value)

            if show_bar_chart:
                bar_chart_container.visible = show_bar_chart
            else:
                bar_chart_container.visible = show_bar_chart

            graphs_column.controls.clear()
            if stats_row:
                graphs_column.controls.extend([
                    ft.Container(
                        content=ft.Column(
                            [
                                # stats_row,
                                ft.Row(
                                    [
                                        ft.Container(
                                            ft.Column([
                                                ft.Text("Статусы задач", size=22, weight=ft.FontWeight.BOLD),
                                                pie_chart
                                            ], expand=True),
                                            expand=True,
                                            height=550,
                                            bgcolor=ft.colors.WHITE,
                                            border_radius=15,
                                            padding=20,
                                            margin=ft.margin.only(10, 5, 10, 5),
                                            shadow=ft.BoxShadow(
                                                spread_radius=1,
                                                blur_radius=10,
                                                color=ft.colors.BLUE_GREY_300,
                                                offset=ft.Offset(2, 2)
                                            ),
                                        ),
                                        bar_chart_container
                                    ],
                                    expand=True,  # Занимает всё доступное пространство
                                    spacing=20,  # Отступ между контейнерами
                                    alignment=ft.MainAxisAlignment.CENTER  # Выравнивание
                                ),
                                line_chart
                            ]
                        )
                    )
                ])

            page.update()

        except Exception as ex:
            print(f"Error updating graphs: {ex}")
            page.snack_bar = ft.SnackBar(ft.Text(f"Ошибка: {str(ex)}"))
            page.snack_bar.open = True
            page.update()

    raw_data = load_data(force_all=True)

    employees.options = [
                            ft.dropdown.Option("Все сотрудники")
                        ] + [
                            ft.dropdown.Option(
                                text=emp['employee_name'],
                                key=str(emp['employee_id'])
                            ) for emp in raw_data.get('employee_stats', [])
                        ]

    # Стиль кнопки
    button_style = ft.ButtonStyle(
        bgcolor=ft.colors.PRIMARY,
        color=ft.colors.WHITE,
        padding=20,
        shape=ft.RoundedRectangleBorder(radius=10),
    )

    # Основной контейнер
    main_container = ft.Container(
        content=ft.Row(
            controls=[
                # Панель фильтров
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                "Настройки графиков",
                                size=20,
                                weight=ft.FontWeight.BOLD,
                                color=ft.colors.PRIMARY,
                                text_align=ft.TextAlign.CENTER
                            ),
                            date_from,
                            date_to,
                            ft.Container(employees, margin=0, padding=0),
                            # ft.Container(graph_dropdown, margin=0, padding=0),
                            ft.Row(
                                [
                                    ft.ElevatedButton(
                                        "Обновить",
                                        on_click=update_graphs,
                                        style=button_style,
                                        elevation=5,
                                        expand=True,
                                        height=45,
                                    )
                                ],
                                # expand=True,
                                alignment=ft.MainAxisAlignment.START
                            )
                        ],
                        spacing=15,
                        alignment=ft.MainAxisAlignment.START,  # Прижимаем все к верху
                    ),
                    bgcolor=ft.colors.WHITE,
                    border_radius=15,
                    padding=20,
                    shadow=ft.BoxShadow(
                        spread_radius=1,
                        blur_radius=10,
                        color=ft.colors.BLUE_GREY_300,
                        offset=ft.Offset(2, 2)
                    ),
                    width=300,
                    height=page.height
                ),

                # Область графиков
                ft.Container(
                    content=graphs_column,
                    expand=True,
                    # padding=10,
                    # height=page.height
                )
            ],
            expand=True,
            vertical_alignment=ft.CrossAxisAlignment.START
        ),
        padding=10,
        expand=True
    )

    update_graphs(None, initial_load=True)

    return main_container
