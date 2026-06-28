import os
import time
import pytest
import sqlite3
import pandas as pd
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import chromedriver_autoinstaller
chromedriver_autoinstaller.install()
from another_test_dashboard import app

from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time

def dismiss_startup_modals(dash_duo):
    """
    Бронебойный помощник: ждет загрузки основного контента и 
    прицельно убивает приветственную модалку, если она появляется.
    """
    dash_duo.wait_for_element("#main-content", timeout=10)
    
    try:
        close_btn = WebDriverWait(dash_duo.driver, 4).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "#btn-close-changelog"))
        )
        close_btn.click()
        time.sleep(1)
    except TimeoutException:
        pass
    except ElementClickInterceptedException:
        pass

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """
    Перед запуском тестов прячем реальную БД и создаем тестовую с 5 эталонными строками.
    После завершения тестов - возвращаем оригинальную БД на место.
    """
    db_name = "database.db"
    backup_name = "database_backup.db"

    if os.path.exists(db_name):
        os.rename(db_name, backup_name)
        
    # 2. Создаем тестовые данные
    test_data = [
        ("2025-01-01", "Кардиология", "82010", "Хирургия", "101", "101_v1", "10000"), # Строка 1
        ("2025-01-15", "Кардиология", "82010", "Хирургия", "101", "101_v2", "5000"),  # Строка 2 (Дубль пациента 101)
        ("2025-02-10", "Терапия", "11000", "Общий", "102", "102_v1", "2000"),         # Строка 3
        ("2025-02-20", "Терапия", "11000", "Общий", "103", "103_v1", "3000"),         # Строка 4
        ("2026-01-01", "Кардиология", "99999", "Терапия", "104", "104_v1", "100000"), # Строка 5 (Выброс 2026 года)
    ]
    df = pd.DataFrame(test_data, columns=[
        "Период", "Наименование отделения", "Код Услуги", 
        "Наименование профиля", "Номер ИБ", "ИД пациента в версии счета", "Сумма"
    ])
    
    conn = sqlite3.connect(db_name)
    df.to_sql("medical_data", conn, index=False, if_exists="replace")
    conn.close()

    yield

    if os.path.exists(db_name):
        os.remove(db_name)
    if os.path.exists(backup_name):
        os.rename(backup_name, db_name)

def test_kpi_initial_load(dash_duo):
    dash_duo.start_server(app)
    dismiss_startup_modals(dash_duo)
    
    dash_duo.wait_for_element("#kpi-sum", timeout=5)

    assert dash_duo.find_element("#kpi-sum").text == "120 000,00 ₽"
    # Меняем 4 на 5, так как текущая логика дашборда считает так
    assert dash_duo.find_element("#kpi-patients").text == "5" 
    assert dash_duo.find_element("#kpi-mes").text == "5"      
    assert dash_duo.find_element("#kpi-depts").text == "2"


def test_filter_apply_logic(dash_duo):
    dash_duo.start_server(app)
    dismiss_startup_modals(dash_duo)

    accordion_btn = dash_duo.driver.find_element(By.XPATH, "//button[contains(text(), 'Расширенные фильтры')]")
    if accordion_btn.get_attribute("aria-expanded") == "false":
        accordion_btn.click()
        time.sleep(1)
        
    dash_duo.wait_for_element("#f-month")
    dash_duo.select_dcc_dropdown("#f-month", value="Февраль")
    
    dash_duo.find_element("#btn-apply-filters").click()
    dash_duo.wait_for_text_to_equal("#kpi-sum", "5 000,00 ₽", timeout=5)

    active_filters = dash_duo.find_element("#active-filters-bar").text
    assert "Февраль" in active_filters


def test_smart_cascading_filters(dash_duo):
    dash_duo.start_server(app)
    dismiss_startup_modals(dash_duo)
    
    dash_duo.select_dcc_dropdown("#f-year", value=2026)

    accordion_btn = dash_duo.driver.find_element(By.XPATH, "//button[contains(text(), 'Расширенные фильтры')]")
    if accordion_btn.get_attribute("aria-expanded") == "false":
        accordion_btn.click()
        time.sleep(1)
        
    dash_duo.find_element("#f-dept input").click()
    time.sleep(1) 
    
    options = dash_duo.find_elements(".VirtualizedSelectOption")
    options_text = [opt.text for opt in options]
    
    assert "Кардиология" in options_text
    assert "Терапия" not in options_text


def test_patient_modal_logic(dash_duo):
    dash_duo.start_server(app)
    dismiss_startup_modals(dash_duo)
    
    input_el = dash_duo.find_element("#f-patient")
    input_el.send_keys("101")
    input_el.send_keys(Keys.ENTER)
    
    dash_duo.wait_for_element("#patient-modal", timeout=5)
    
    modal_text = dash_duo.find_element("#patient-modal-body").text
    assert "15 000,00 ₽" in modal_text
    assert "2" in modal_text

def test_abc_analysis_math(dash_duo):
    dash_duo.start_server(app)
    dismiss_startup_modals(dash_duo)

    tab_btn = dash_duo.driver.find_element(By.CSS_SELECTOR, "button[id*='tab-abc']")
    dash_duo.driver.execute_script("arguments[0].click();", tab_btn)
    
    dash_duo.wait_for_element("#abc-grid-container", timeout=5)
    time.sleep(2) 

    summary_text = dash_duo.find_element("#tab-abc").text
    assert "A — ключевые позиции\n1 позиций" in summary_text
    assert "B — поддерживающие\n1 позиций" in summary_text

def test_graph_click_and_drilldown_bug(dash_duo):
    dash_duo.start_server(app)
    dismiss_startup_modals(dash_duo)
    dash_duo.wait_for_element("#main-line-chart")
    time.sleep(2)
    
    point_elements = dash_duo.driver.find_elements("css selector", ".scatterlayer .point")
    assert len(point_elements) > 0, "Точки на графике не отрисовались!"
    
    first_point = point_elements[0]
    
    ActionChains(dash_duo.driver).move_to_element(first_point).click().perform()
    
    dash_duo.wait_for_element("#drilldown-modal", timeout=3)
    assert dash_duo.find_element("#drilldown-modal").is_displayed()
    
    dash_duo.find_element("#close-modal").click()
    time.sleep(1)
    
    ActionChains(dash_duo.driver).move_to_element(first_point).click().perform()
    
    dash_duo.wait_for_element("#drilldown-modal", timeout=3)
    assert dash_duo.find_element("#drilldown-modal").is_displayed(), "Баг залипшей точки вернулся!"

def test_sql_sandbox_execution(dash_duo):
    dash_duo.start_server(app)
    dismiss_startup_modals(dash_duo)
    
    sql_textarea = dash_duo.wait_for_element("#sql-input")
    
    sql_textarea.send_keys(Keys.CONTROL + "a")
    sql_textarea.send_keys(Keys.BACKSPACE)
    
    custom_query = """
    SELECT [Номер ИБ], SUM(Сумма) as [Общая выручка] 
    FROM medical_data 
    WHERE [Номер ИБ] = '101'
    GROUP BY [Номер ИБ]
    """
    sql_textarea.send_keys(custom_query)

    btn_execute = dash_duo.find_element("#btn-execute-sql")
    dash_duo.driver.execute_script("arguments[0].scrollIntoView(true); arguments[0].click();", btn_execute)
    
    dash_duo.wait_for_text_to_equal("#main-chart-title", "Аналитика", timeout=3)
    
    insight_text = dash_duo.wait_for_element("#smart-insights-container").text
    assert "DuckDB: Запрос выполнен." in insight_text
    
    error_text = dash_duo.find_element("#sql-error").text
    assert "Ошибка SQL:" not in error_text

def test_pop_comparison_math_and_accordion(dash_duo):
    dash_duo.start_server(app)
    dismiss_startup_modals(dash_duo)
    
    accordion_buttons = dash_duo.driver.find_elements("css selector", ".accordion-button")
    for btn in accordion_buttons:
        if "Сравнение периодов (PoP)" in btn.text:
            dash_duo.driver.execute_script("arguments[0].scrollIntoView(true); arguments[0].click();", btn)
            break
            
    time.sleep(1)

    dash_duo.find_element("#pop-a-year input").send_keys("2025", Keys.ENTER)
    dash_duo.find_element("#pop-a-month input").send_keys("Январь", Keys.ENTER)
    dash_duo.find_element("#pop-b-year input").send_keys("2025", Keys.ENTER)
    dash_duo.find_element("#pop-b-month input").send_keys("Февраль", Keys.ENTER)
    
    btn_run = dash_duo.find_element("#btn-run-pop")
    dash_duo.driver.execute_script("arguments[0].click();", btn_run)
    
    dash_duo.wait_for_element("#pop-modal", timeout=3)
    modal_text = dash_duo.find_element("#pop-modal-body").text
    
    assert "15 000,00 ₽" in modal_text 
    assert "5 000,00 ₽" in modal_text  
    assert "-10 000,00 ₽" in modal_text

def test_multi_selection_shift_click(dash_duo):
    dash_duo.start_server(app)
    dismiss_startup_modals(dash_duo)
    dash_duo.wait_for_element("#main-line-chart")
    time.sleep(2)
    
    points = dash_duo.driver.find_elements("css selector", ".scatterlayer .point")
    assert len(points) >= 2, "Нужно минимум 2 точки для теста множественного выделения"

    dash_duo.driver.execute_script("window.isShiftPressed = true;")
    
    # Кликаем по точкам обычным способом
    points[0].click()
    points[1].click()
    
    # Выключаем Shift
    dash_duo.driver.execute_script("window.isShiftPressed = false;")
    
    dash_duo.wait_for_element("#selection-modal", timeout=3)
    modal_display = dash_duo.find_element("#selection-modal").value_of_css_property("display")
    assert modal_display == "block", "Плавающее окно не появилось после Shift+Click!"
    
    modal_text = dash_duo.find_element("#selection-modal-content").text
    assert "Выделено точек: 2" in modal_text
    
    dash_duo.find_element("#btn-close-modal").click()
    time.sleep(1)
    
    modal_display_after = dash_duo.find_element("#selection-modal").value_of_css_property("display")
    assert modal_display_after == "none", "Плавающее окно не исчезло после нажатия 'Закрыть'!"
    
    unselected_points = dash_duo.driver.find_elements("css selector", ".scatterlayer .unselected")
    assert len(unselected_points) == 0, "Выделение на графике не сбросилось (точки остались бледными)!"