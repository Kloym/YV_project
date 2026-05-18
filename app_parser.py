import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
import sqlite3
import logging
import os
import sys
from typing import Tuple

# --- КОНФИГУРАЦИЯ ---
DB_NAME = "database.db"
TABLE_NAME = "medical_data"
ROWS_TO_SKIP = [0, 1, 2, 3, 5]

# --- НАСТРОЙКА ЛОГИРОВАНИЯ ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("parser_app.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


def clean_dataframe(df: pd.DataFrame, file_name: str) -> pd.DataFrame:
    """
    Легкая очистка данных перед вставкой в БД.
    """
    df.columns = (
        df.columns.str.replace(r"\n|\r", " ", regex=True)
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )

    df = df.dropna(how="all", axis=0).dropna(how="all", axis=1)

    if df.empty:
        return df

    if "Наименование отделения" in df.columns:
        df = df.dropna(subset=["Наименование отделения"])

    if "Период" in df.columns:
        mask_total = (
            df["Период"].astype(str).str.contains("Итого", case=False, na=False)
        )
        df = df[~mask_total]

    if "Сумма" in df.columns:
        df["Сумма"] = pd.to_numeric(
            df["Сумма"].astype(str).str.replace(",", ".").str.replace(" ", ""),
            errors="coerce",
        ).fillna(0)

    str_cols = df.select_dtypes(include=["object", "string"]).columns
    for col in str_cols:
        df[col] = df[col].replace({r"\r\n": " ", r"\n": " ", r"\r": " "}, regex=True)
        mask = df[col].notna()
        df.loc[mask, col] = df.loc[mask, col].astype(str).str.strip()

    return df


def process_excel_files(file_paths: Tuple[str, ...]) -> Tuple[int, int]:
    """
    Обрабатывает Excel-файлы, безопасно заменяет старые данные на новые
    через транзакции и ведет детальный лог изменений.
    """
    success_count = 0
    total_rows_inserted = 0

    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()

        for file_path in file_paths:
            file_name = os.path.basename(file_path)
            logger.info(f"Начало обработки файла: {file_name}")

            try:
                df = pd.read_excel(file_path, skiprows=ROWS_TO_SKIP)
                df_cleaned = clean_dataframe(df, file_name)

                if df_cleaned.empty:
                    logger.warning(
                        f"Файл {file_name} пуст или не содержит полезных данных. Пропуск."
                    )
                    continue

                if (
                    "Период" not in df_cleaned.columns
                    or "Наименование отделения" not in df_cleaned.columns
                    or "Наименование профиля" not in df_cleaned.columns
                ):
                    logger.error(
                        f"В файле {file_name} отсутствуют ключевые колонки (Период, Отделение или Профиль). Файл пропущен."
                    )
                    continue

                cursor.execute("BEGIN TRANSACTION")

                cursor.execute(
                    "SELECT count(name) FROM sqlite_master WHERE type='table' AND name=?",
                    (TABLE_NAME,),
                )
                table_exists = cursor.fetchone()[0] == 1

                if table_exists:
                    unique_groups = (
                        df_cleaned[
                            ["Период", "Наименование отделения", "Наименование профиля"]
                        ]
                        .dropna()
                        .drop_duplicates()
                    )

                    changes_log = []
                    deleted_total = 0

                    for _, row in unique_groups.iterrows():
                        period = str(row["Период"]).strip()
                        dept = str(row["Наименование отделения"]).strip()
                        profile = str(row["Наименование профиля"]).strip()

                        if not period or not dept or not profile:
                            continue

                        cursor.execute(
                            f'DELETE FROM {TABLE_NAME} WHERE "Период" = ? AND "Наименование отделения" = ? AND "Наименование профиля" = ?',
                            (period, dept, profile),
                        )

                        deleted_rows = cursor.rowcount
                        if deleted_rows > 0:
                            deleted_total += deleted_rows
                            changes_log.append(
                                f"[{period} | {dept} | {profile}] удалено старых строк: {deleted_rows}"
                            )

                    if changes_log:
                        logger.info(
                            f"Обнаружено перекрытие данных! Очищено {deleted_total} старых записей перед обновлением:"
                        )
                        for log_msg in changes_log:
                            logger.info(f"   -> {log_msg}")

                df_cleaned.to_sql(
                    TABLE_NAME, conn, if_exists="append", index=False, chunksize=10000
                )

                conn.commit()

                rows_added = len(df_cleaned)
                total_rows_inserted += rows_added
                success_count += 1

                logger.info(
                    f"Успех! Файл {file_name} обработан. Записано свежих строк: {rows_added}"
                )

            except Exception as e:
                conn.rollback()
                logger.error(
                    f"Критическая ошибка при обработке {file_name}. "
                    f"Все изменения (удаления и записи) ОТМЕНЕНЫ! Ошибка: {str(e)}",
                    exc_info=True,
                )

    return success_count, total_rows_inserted


def main():
    root = tk.Tk()
    root.withdraw()

    file_paths = filedialog.askopenfilenames(
        title="Выберите отчеты Excel (xlsx)",
        filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
    )

    if not file_paths:
        logger.info("Пользователь отменил выбор файлов.")
        return

    try:
        logger.info(f"Запущена пакетная обработка. Выбрано файлов: {len(file_paths)}")
        success_count, total_rows = process_excel_files(file_paths)

        if success_count > 0:
            msg = (
                f"Обработка завершена!\n\n"
                f"Успешно обработано файлов: {success_count} из {len(file_paths)}\n"
                f"Добавлено чистых записей: {total_rows}\n\n"
                f"База данных: {DB_NAME}"
            )
            messagebox.showinfo("Отчет о загрузке", msg)
        else:
            messagebox.showwarning(
                "Внимание", "Не удалось загрузить данные. Проверьте parser_app.log"
            )

    except Exception as e:
        error_msg = f"Произошла критическая ошибка:\n{str(e)}"
        logger.critical(error_msg, exc_info=True)
        messagebox.showerror("Фатальная ошибка", error_msg)


if __name__ == "__main__":
    main()
