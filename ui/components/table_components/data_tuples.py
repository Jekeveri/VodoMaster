import json

import pandas as pd


def load_data_from_tuples(
        data_tuples,
        columns,
        exclude_columns=None,
        date_columns=None,
        numeric_columns=None,
        string_columns=None,
        json_columns=None
):
    """
    Загружает данные из кортежей в DataFrame с преобразованием типов.

    Параметры:
        data_tuples: Список кортежей с исходными данными
        columns: Список названий колонок (порядок должен соответствовать данным)
        exclude_columns: Список колонок для исключения (по умолчанию None)
        date_columns: Список колонок с датами для преобразования (по умолчанию None)
        numeric_columns: Список числовых колонок для преобразования (по умолчанию None)
        string_columns: Список строковых колонок для обработки (по умолчанию None)
        json_columns: Список JSON колонок для преобразования (по умолчанию None)

    Возвращает:
        pandas DataFrame с обработанными данными
    """
    # Validate input types
    if not isinstance(data_tuples, list):
        raise TypeError(f"data_tuples must be a list, got {type(data_tuples)}")

    if not isinstance(columns, list):
        raise TypeError(f"columns must be a list, got {type(columns)}")

    # Handle empty input
    if not data_tuples:
        return pd.DataFrame(columns=columns)

    # Инициализация параметров по умолчанию
    exclude_columns = exclude_columns or []
    date_columns = date_columns or []
    numeric_columns = numeric_columns or []
    string_columns = string_columns or []
    json_columns = json_columns or []

    # Формируем список активных колонок
    active_columns = [col for col in columns if col not in exclude_columns]

    # Проверка соответствия длины кортежей и колонок
    if any(len(tup) != len(columns) for tup in data_tuples):
        raise ValueError("Длина каждого кортежа должна соответствовать длине списка columns")

    # Получаем индексы нужных колонок в исходных данных
    column_indices = [columns.index(col) for col in active_columns]

    # Фильтруем данные
    filtered_data = [tuple(tup[i] for i in column_indices) for tup in data_tuples]

    # Создаем DataFrame
    df = pd.DataFrame(filtered_data, columns=active_columns)

    # Функция для обработки дат
    def convert_dates(column: str) -> None:
        df[column] = pd.to_datetime(df[column], errors='coerce', format='%Y-%m-%d')  # Add specific format
        # Optional: Replace NaT with None or a default date if needed
        # df[column] = df[column].fillna(pd.Timestamp('1900-01-01'))

    # Функция для обработки чисел
    def convert_numeric(column):
        df[column] = pd.to_numeric(df[column], errors='coerce')

    # Функция для обработки строк
    def convert_strings(column):
        df[column] = df[column].apply(
            lambda x: '' if pd.isna(x) or x in (None, '', ' ')
            else str(x).strip() if isinstance(x, str)
            else str(x)
        )

    # Функция для обработки JSON
    def convert_json(column):
        def parse_json(value):
            if pd.isna(value) or value in (None, '', ' '):
                return None
            try:
                # Если значение уже словарь или список, возвращаем как есть
                if isinstance(value, (dict, list)):
                    return value
                # Пытаемся распарсить JSON
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                # Если не удалось распарсить, возвращаем оригинальное значение
                return value

        df[column] = df[column].apply(parse_json)

    # Применяем преобразования
    conversion_order = [
        (date_columns, convert_dates),
        (numeric_columns, convert_numeric),
        (string_columns, convert_strings),
        (json_columns, convert_json)
    ]

    for columns_list, converter in conversion_order:
        for col in columns_list:
            if col in df.columns:
                converter(col)

    return df
