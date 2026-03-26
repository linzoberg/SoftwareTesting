import os
import time
import tempfile
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC


class TestRegistrationForm:
    """Тесты формы регистрации demoqa.com/automation-practice-form"""

    # =============================================================
    # Подготовка и завершение
    # =============================================================
    def setup_method(self):
        """Открыть браузер и перейти на страницу перед каждым тестом"""
        self.driver = webdriver.Chrome()
        self.driver.maximize_window()
        self.driver.get("https://demoqa.com/automation-practice-form")
        # Удалить рекламу, которая перекрывает элементы формы
        self.driver.execute_script("""
            var ads = document.querySelectorAll(
                'iframe, #adplus-anchor, #fixedban, footer'
            );
            ads.forEach(function(el) { el.remove(); });
        """)

    def teardown_method(self):
        """Закрыть браузер после каждого теста"""
        self.driver.quit()

    # =============================================================
    # Вспомогательные методы
    # =============================================================
    def fill_required_fields(self):
        """Заполнить только обязательные поля (имя, фамилия, пол, телефон)"""
        d = self.driver
        d.find_element(By.ID, "firstName").send_keys("Ivan")
        d.find_element(By.ID, "lastName").send_keys("Petrov")
        d.find_element(
            By.CSS_SELECTOR, "label[for='gender-radio-1']"
        ).click()
        d.find_element(By.ID, "userNumber").send_keys("9001234567")

    def scroll_and_submit(self):
        """Прокрутить страницу до кнопки Submit и нажать её"""
        btn = self.driver.find_element(By.ID, "submit")
        self.driver.execute_script("arguments[0].scrollIntoView();", btn)
        time.sleep(0.5)
        btn.click()

    def get_modal_text(self):
        """Дождаться модального окна и вернуть его текст"""
        wait = WebDriverWait(self.driver, 5)
        wait.until(EC.visibility_of_element_located(
            (By.ID, "example-modal-sizes-title-lg")
        ))
        return self.driver.find_element(By.CLASS_NAME, "modal-body").text

    # =============================================================
    # ТК-1  ФП-1: Отображение элементов формы
    # =============================================================
    def test_elements_present(self):
        """Все 17 ключевых элементов формы отображаются на странице"""
        d = self.driver
        elements = {
            "First Name":    (By.ID, "firstName"),
            "Last Name":     (By.ID, "lastName"),
            "Email":         (By.ID, "userEmail"),
            "Gender Male":   (By.CSS_SELECTOR, "label[for='gender-radio-1']"),
            "Gender Female": (By.CSS_SELECTOR, "label[for='gender-radio-2']"),
            "Gender Other":  (By.CSS_SELECTOR, "label[for='gender-radio-3']"),
            "Mobile":        (By.ID, "userNumber"),
            "Date of Birth": (By.ID, "dateOfBirthInput"),
            "Subjects":      (By.ID, "subjectsContainer"),
            "Hobby Sports":  (By.CSS_SELECTOR, "label[for='hobbies-checkbox-1']"),
            "Hobby Reading": (By.CSS_SELECTOR, "label[for='hobbies-checkbox-2']"),
            "Hobby Music":   (By.CSS_SELECTOR, "label[for='hobbies-checkbox-3']"),
            "Picture":       (By.ID, "uploadPicture"),
            "Address":       (By.ID, "currentAddress"),
            "State":         (By.ID, "state"),
            "City":          (By.ID, "city"),
            "Submit":        (By.ID, "submit"),
        }
        for name, locator in elements.items():
            element = d.find_element(*locator)
            assert element.is_displayed(), f"Элемент '{name}' не найден"

    # =============================================================
    # ТК-2  ФП-2: Успешная регистрация с заполнением всех полей
    # =============================================================
    def test_successful_registration(self):
        """Заполнить все поля формы, отправить, проверить данные"""
        d = self.driver

        # Текстовые поля
        d.find_element(By.ID, "firstName").send_keys("Ivan")
        d.find_element(By.ID, "lastName").send_keys("Petrov")
        d.find_element(By.ID, "userEmail").send_keys("ivan@mail.ru")
        d.find_element(By.ID, "userNumber").send_keys("9001234567")
        d.find_element(By.ID, "currentAddress").send_keys(
            "Moscow, Main St. 1"
        )

        # Radio-кнопка пола
        d.find_element(
            By.CSS_SELECTOR, "label[for='gender-radio-1']"
        ).click()

        # Автозаполнение предметов
        subj = d.find_element(By.ID, "subjectsInput")
        subj.send_keys("Maths")
        time.sleep(0.5)
        subj.send_keys(Keys.ENTER)

        # Чекбокс хобби
        d.find_element(
            By.CSS_SELECTOR, "label[for='hobbies-checkbox-1']"
        ).click()

        # Выпадающие списки штат/город
        d.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(0.5)
        d.find_element(By.ID, "state").click()
        time.sleep(0.3)
        d.find_element(By.XPATH, "//*[text()='NCR']").click()
        d.find_element(By.ID, "city").click()
        time.sleep(0.3)
        d.find_element(By.XPATH, "//*[text()='Delhi']").click()

        # Отправить
        self.scroll_and_submit()
        result = self.get_modal_text()

        # Проверить все данные в модальном окне
        assert "Ivan Petrov" in result,  "Имя/фамилия не совпадают"
        assert "ivan@mail.ru" in result, "Email не совпадает"
        assert "Male" in result,         "Пол не совпадает"
        assert "9001234567" in result,   "Телефон не совпадает"
        assert "Maths" in result,        "Предмет не совпадает"
        assert "Sports" in result,       "Хобби не совпадает"
        assert "NCR Delhi" in result,    "Штат/город не совпадают"
        assert "Moscow" in result,       "Адрес не совпадает"

    # =============================================================
    # ТК-3  ФП-2: Валидация обязательных полей
    # =============================================================
    def test_empty_form(self):
        """Пустая форма не отправляется, поля подсвечиваются красным"""
        d = self.driver

        self.scroll_and_submit()
        time.sleep(1)

        # Модальное окно НЕ появилось
        modals = d.find_elements(By.ID, "example-modal-sizes-title-lg")
        assert len(modals) == 0, "Пустая форма была отправлена"

        # Обязательные поля подсвечены красным (rgb(220, 53, 69))
        border = d.find_element(By.ID, "firstName") \
            .value_of_css_property("border-color")
        assert "rgb(220, 53, 69)" in border, \
            "Поле First Name не подсвечено красным"

    # =============================================================
    # ТК-4  ФП-3: Валидация формата email
    # =============================================================
    def test_invalid_email(self):
        """Некорректный email отклоняется"""
        d = self.driver

        self.fill_required_fields()
        d.find_element(By.ID, "userEmail").send_keys("bad-email")

        self.scroll_and_submit()
        time.sleep(1)

        modals = d.find_elements(By.ID, "example-modal-sizes-title-lg")
        assert len(modals) == 0, "Форма принята с невалидным email"

        border = d.find_element(By.ID, "userEmail") \
            .value_of_css_property("border-color")
        assert "rgb(220, 53, 69)" in border, \
            "Поле email не подсвечено красным"

    # =============================================================
    # ТК-5  ФП-3: Валидация формата телефона
    # =============================================================
    def test_invalid_phone(self):
        """Номер телефона короче 10 цифр отклоняется"""
        d = self.driver

        d.find_element(By.ID, "firstName").send_keys("Ivan")
        d.find_element(By.ID, "lastName").send_keys("Petrov")
        d.find_element(
            By.CSS_SELECTOR, "label[for='gender-radio-1']"
        ).click()
        d.find_element(By.ID, "userNumber").send_keys("123")

        self.scroll_and_submit()
        time.sleep(1)

        modals = d.find_elements(By.ID, "example-modal-sizes-title-lg")
        assert len(modals) == 0, "Форма принята с коротким номером"

        border = d.find_element(By.ID, "userNumber") \
            .value_of_css_property("border-color")
        assert "rgb(220, 53, 69)" in border, \
            "Поле телефона не подсвечено красным"

    # =============================================================
    # ТК-6  ФП-4: Работа radio-кнопок (переключение пола)
    # =============================================================
    def test_gender_radio_buttons(self):
        """При выборе одного пола предыдущий сбрасывается"""
        d = self.driver

        # Выбрать Male
        d.find_element(
            By.CSS_SELECTOR, "label[for='gender-radio-1']"
        ).click()
        assert d.find_element(By.ID, "gender-radio-1").is_selected(), \
            "Male не выбран"

        # Переключить на Female → Male должен сброситься
        d.find_element(
            By.CSS_SELECTOR, "label[for='gender-radio-2']"
        ).click()
        assert d.find_element(By.ID, "gender-radio-2").is_selected(), \
            "Female не выбран"
        assert not d.find_element(By.ID, "gender-radio-1").is_selected(), \
            "Male не сбросился"

        # Переключить на Other → Female должен сброситься
        d.find_element(
            By.CSS_SELECTOR, "label[for='gender-radio-3']"
        ).click()
        assert d.find_element(By.ID, "gender-radio-3").is_selected(), \
            "Other не выбран"
        assert not d.find_element(By.ID, "gender-radio-2").is_selected(), \
            "Female не сбросился"

    # =============================================================
    # ТК-7  ФП-4: Работа чекбоксов (множественный выбор хобби)
    # =============================================================
    def test_hobbies_checkboxes(self):
        """Чекбоксы можно выбирать одновременно и снимать по одному"""
        d = self.driver

        # Выбрать Sports
        d.find_element(
            By.CSS_SELECTOR, "label[for='hobbies-checkbox-1']"
        ).click()
        assert d.find_element(By.ID, "hobbies-checkbox-1").is_selected(), \
            "Sports не выбран"

        # Выбрать Reading → Sports остаётся выбранным
        d.find_element(
            By.CSS_SELECTOR, "label[for='hobbies-checkbox-2']"
        ).click()
        assert d.find_element(By.ID, "hobbies-checkbox-2").is_selected(), \
            "Reading не выбран"
        assert d.find_element(By.ID, "hobbies-checkbox-1").is_selected(), \
            "Sports сбросился при выборе Reading"

        # Снять Sports → Reading остаётся
        d.find_element(
            By.CSS_SELECTOR, "label[for='hobbies-checkbox-1']"
        ).click()
        assert not d.find_element(By.ID, "hobbies-checkbox-1").is_selected(), \
            "Sports не снялся"
        assert d.find_element(By.ID, "hobbies-checkbox-2").is_selected(), \
            "Reading сбросился при снятии Sports"

    # =============================================================
    # ТК-8  ФП-5: Работа элемента выбора даты рождения
    # =============================================================
    def test_date_of_birth(self):
        """Через календарь можно выбрать месяц, год и день"""
        d = self.driver

        # Открыть календарь
        d.find_element(By.ID, "dateOfBirthInput").click()
        time.sleep(0.5)

        # Выбрать месяц — январь (значение "0")
        Select(d.find_element(
            By.CLASS_NAME, "react-datepicker__month-select"
        )).select_by_value("0")

        # Выбрать год — 2000
        Select(d.find_element(
            By.CLASS_NAME, "react-datepicker__year-select"
        )).select_by_value("2000")

        # Кликнуть 15-е число
        d.find_element(By.CSS_SELECTOR,
            ".react-datepicker__day--015"
            ":not(.react-datepicker__day--outside-month)"
        ).click()

        # Проверить, что дата установилась
        date_val = d.find_element(
            By.ID, "dateOfBirthInput"
        ).get_attribute("value")
        assert "15" in date_val and "2000" in date_val, \
            f"Дата не установилась: {date_val}"

    # =============================================================
    # ТК-9  ФП-5: Работа автозаполнения (предметы)
    # =============================================================
    def test_subjects_autocomplete(self):
        """Можно ввести текст, выбрать предмет и добавить несколько"""
        d = self.driver

        subj = d.find_element(By.ID, "subjectsInput")

        # Ввести "Maths" и подтвердить
        subj.send_keys("Maths")
        time.sleep(0.5)
        subj.send_keys(Keys.ENTER)

        # Ввести "Physics" и подтвердить
        subj.send_keys("Physics")
        time.sleep(0.5)
        subj.send_keys(Keys.ENTER)

        # Оба предмета должны отображаться
        container_text = d.find_element(By.ID, "subjectsContainer").text
        assert "Maths" in container_text, "Maths не добавлен"
        assert "Physics" in container_text, "Physics не добавлен"

    # =============================================================
    # ТК-10  ФП-5: Загрузка файла
    # =============================================================
    def test_file_upload(self):
        """Файл прикрепляется и его имя отображается"""
        d = self.driver

        # Создать временный файл
        temp = tempfile.NamedTemporaryFile(
            suffix=".png", delete=False, prefix="test_photo_"
        )
        temp.write(b"\x89PNG")
        temp_path = temp.name
        temp.close()
        file_name = os.path.basename(temp_path)

        try:
            # Прикрепить файл через send_keys
            d.find_element(By.ID, "uploadPicture").send_keys(temp_path)
            time.sleep(0.5)

            # Имя файла должно отобразиться в поле
            value = d.find_element(
                By.ID, "uploadPicture"
            ).get_attribute("value")
            assert file_name in value, \
                f"Имя файла '{file_name}' не найдено в '{value}'"
        finally:
            os.unlink(temp_path)

    # =============================================================
    # ТК-11  ФП-5: Зависимые выпадающие списки (штат → город)
    # =============================================================
    def test_state_city_dependency(self):
        """Список городов зависит от выбранного штата"""
        d = self.driver

        d.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(0.5)

        # До выбора штата город показывает placeholder
        city_text = d.find_element(By.ID, "city").text
        assert "Select City" in city_text, \
            "Город доступен до выбора штата"

        # --- Выбрать штат NCR ---
        d.find_element(By.ID, "state").click()
        time.sleep(0.3)
        d.find_element(By.XPATH, "//*[text()='NCR']").click()
        time.sleep(0.3)

        # Открыть список городов и получить все варианты
        d.find_element(By.ID, "city").click()
        time.sleep(0.3)
        ncr_options = d.find_elements(
            By.XPATH, "//div[@id='city']//div[contains(@class, 'option')]"
        )
        ncr_cities = [opt.text for opt in ncr_options]

        assert "Delhi" in ncr_cities, \
            f"Delhi нет в списке городов NCR: {ncr_cities}"
        assert "Agra" not in ncr_cities, \
            f"Agra есть в NCR — это город Uttar Pradesh: {ncr_cities}"

        # Выбрать Delhi
        d.find_element(By.XPATH, "//*[text()='Delhi']").click()
        time.sleep(0.3)
        assert "Delhi" in d.find_element(By.ID, "city").text, \
            "Delhi не выбран"

        # --- Сменить штат на Uttar Pradesh ---
        d.find_element(By.ID, "state").click()
        time.sleep(0.3)
        d.find_element(By.XPATH, "//*[text()='Uttar Pradesh']").click()
        time.sleep(0.3)

        # Открыть список городов и получить все варианты
        d.find_element(By.ID, "city").click()
        time.sleep(0.3)
        up_options = d.find_elements(
            By.XPATH, "//div[@id='city']//div[contains(@class, 'option')]"
        )
        up_cities = [opt.text for opt in up_options]

        assert "Agra" in up_cities, \
            f"Agra нет в списке Uttar Pradesh: {up_cities}"
        assert "Delhi" not in up_cities, \
            f"Delhi доступен для Uttar Pradesh: {up_cities}"

        # Выбрать Agra
        d.find_element(By.XPATH, "//*[text()='Agra']").click()
        time.sleep(0.3)
        assert "Agra" in d.find_element(By.ID, "city").text, \
            "Agra не выбран"