"""
Модульные и интеграционные тесты для класса CurrencyConverter.
Запуск:  pytest test_converter.py -v
"""

import pytest
import requests as req
from unittest.mock import patch, Mock
from converter import CurrencyConverter


# ============================================================
#  ФИКСТУРЫ (подготовка данных, общих для многих тестов)
# ============================================================

@pytest.fixture
def converter():
    """Создаёт экземпляр конвертера для каждого теста."""
    return CurrencyConverter()


@pytest.fixture
def mock_api_success():
    """Имитация успешного ответа API с фиксированными курсами."""
    mock_resp = Mock()
    mock_resp.status_code = 200
    mock_resp.raise_for_status = Mock()
    mock_resp.json.return_value = {
        "result": "success",
        "base_code": "USD",
        "rates": {
            "USD": 1.0,
            "EUR": 0.85,
            "RUB": 92.5,
            "GBP": 0.73,
            "JPY": 149.5,
            "CNY": 7.25,
        }
    }
    return mock_resp


# ============================================================
#  ПОЗИТИВНЫЕ ТЕСТЫ — метод convert
# ============================================================

class TestConvertPositive:
    """Проверка корректной работы convert при допустимых входных данных."""

    @patch("converter.requests.get")
    def test_usd_to_rub_correct_value(self, mock_get, mock_api_success, converter):
        """100 USD при курсе 92.5 должны дать 9250.0 RUB."""
        mock_get.return_value = mock_api_success
        result = converter.convert(100, "USD", "RUB")
        assert result == 9250.0

    @patch("converter.requests.get")
    def test_usd_to_eur_correct_value(self, mock_get, mock_api_success, converter):
        """100 USD при курсе 0.85 должны дать 85.0 EUR."""
        mock_get.return_value = mock_api_success
        result = converter.convert(100, "USD", "EUR")
        assert result == 85.0

    @patch("converter.requests.get")
    def test_same_currency_returns_same_amount(self, mock_get, mock_api_success, converter):
        """Конвертация валюты в саму себя возвращает исходную сумму."""
        mock_get.return_value = mock_api_success
        result = converter.convert(250, "USD", "USD")
        assert result == 250.0

    @patch("converter.requests.get")
    def test_zero_amount_returns_zero(self, mock_get, mock_api_success, converter):
        """Конвертация нулевой суммы всегда возвращает 0.0."""
        mock_get.return_value = mock_api_success
        result = converter.convert(0, "USD", "EUR")
        assert result == 0.0

    @patch("converter.requests.get")
    def test_fractional_amount(self, mock_get, mock_api_success, converter):
        """Дробная сумма корректно конвертируется и округляется до 2 знаков."""
        mock_get.return_value = mock_api_success
        result = converter.convert(33.33, "USD", "EUR")
        expected = round(33.33 * 0.85, 2)
        assert result == expected

    @patch("converter.requests.get")
    def test_lowercase_currency_accepted(self, mock_get, mock_api_success, converter):
        """Коды валют в нижнем регистре обрабатываются корректно."""
        mock_get.return_value = mock_api_success
        result = converter.convert(100, "usd", "eur")
        assert result == 85.0

# ============================================================
#  НЕГАТИВНЫЕ ТЕСТЫ — метод convert
# ============================================================

class TestConvertNegative:
    """Проверка обработки некорректных входных данных в convert."""

    def test_negative_amount_raises_error(self, converter):
        """Отрицательная сумма вызывает ValueError."""
        with pytest.raises(ValueError, match="не может быть отрицательной"):
            converter.convert(-100, "USD", "EUR")

    def test_string_amount_raises_error(self, converter):
        """Строка вместо суммы вызывает TypeError."""
        with pytest.raises(TypeError, match="должна быть числом"):
            converter.convert("сто", "USD", "EUR")

    def test_none_amount_raises_error(self, converter):
        """None вместо суммы вызывает TypeError."""
        with pytest.raises(TypeError, match="должна быть числом"):
            converter.convert(None, "USD", "EUR")

    def test_list_amount_raises_error(self, converter):
        """Список вместо суммы вызывает TypeError."""
        with pytest.raises(TypeError, match="должна быть числом"):
            converter.convert([100], "USD", "EUR")

    @patch("converter.requests.get")
    def test_nonexistent_currency_raises_error(self, mock_get, mock_api_success, converter):
        """Несуществующий код целевой валюты вызывает ValueError."""
        mock_get.return_value = mock_api_success
        with pytest.raises(ValueError, match="не найдена"):
            converter.convert(100, "USD", "XYZ")

    def test_empty_from_currency_raises_error(self, converter):
        """Пустая строка вместо исходной валюты вызывает ValueError."""
        with pytest.raises(ValueError, match="не может быть пустым"):
            converter.convert(100, "", "EUR")

    def test_empty_to_currency_raises_error(self, converter):
        """Пустая строка вместо целевой валюты вызывает ValueError."""
        with pytest.raises(ValueError, match="не может быть пустым"):
            converter.convert(100, "USD", "")

    def test_numeric_currency_code_raises_error(self, converter):
        """Число вместо кода валюты вызывает TypeError."""
        with pytest.raises(TypeError, match="должен быть строкой"):
            converter.convert(100, 123, "EUR")


# ============================================================
#  ТЕСТЫ — метод get_rate
# ============================================================

class TestGetRate:
    """Проверка метода получения курса обмена."""

    @patch("converter.requests.get")
    def test_same_currency_rate_equals_one(self, mock_get, mock_api_success, converter):
        """Курс валюты к самой себе равен 1.0."""
        mock_get.return_value = mock_api_success
        rate = converter.get_rate("USD", "USD")
        assert rate == 1.0

    @patch("converter.requests.get")
    def test_known_rate_value(self, mock_get, mock_api_success, converter):
        """Курс соответствует значению из мок-ответа."""
        mock_get.return_value = mock_api_success
        rate = converter.get_rate("USD", "JPY")
        assert rate == 149.5


# ============================================================
#  ТЕСТЫ — метод get_available_currencies
# ============================================================

class TestGetAvailableCurrencies:
    """Проверка метода получения списка доступных валют."""

    @patch("converter.requests.get")
    def test_returns_list(self, mock_get, mock_api_success, converter):
        """Метод возвращает объект типа list."""
        mock_get.return_value = mock_api_success
        result = converter.get_available_currencies()
        assert isinstance(result, list)

    @patch("converter.requests.get")
    def test_contains_major_currencies(self, mock_get, mock_api_success, converter):
        """Список содержит основные мировые валюты (USD, EUR)."""
        mock_get.return_value = mock_api_success
        result = converter.get_available_currencies()
        assert "USD" in result
        assert "EUR" in result

    @patch("converter.requests.get")
    def test_all_elements_are_strings(self, mock_get, mock_api_success, converter):
        """Все элементы списка — строки."""
        mock_get.return_value = mock_api_success
        result = converter.get_available_currencies()
        for code in result:
            assert isinstance(code, str)


# ============================================================
#  ТЕСТЫ ВЗАИМОДЕЙСТВИЯ С ВНЕШНИМ API
# ============================================================

class TestAPIInteraction:
    """Проверка корректности взаимодействия с внешним сервисом курсов."""

    @patch("converter.requests.get")
    def test_correct_url_called(self, mock_get, mock_api_success, converter):
        """Запрос к API формируется с правильным URL и таймаутом."""
        mock_get.return_value = mock_api_success
        converter.get_rate("USD", "EUR")
        mock_get.assert_called_once_with(
            "https://open.er-api.com/v6/latest/USD",
            timeout=10
        )

    @patch("converter.requests.get")
    def test_connection_error_handled(self, mock_get, converter):
        """При потере соединения выбрасывается ConnectionError."""
        mock_get.side_effect = req.exceptions.ConnectionError("Нет соединения")
        with pytest.raises(ConnectionError, match="Ошибка соединения"):
            converter.get_rate("USD", "EUR")

    @patch("converter.requests.get")
    def test_timeout_handled(self, mock_get, converter):
        """При таймауте запроса выбрасывается ConnectionError."""
        mock_get.side_effect = req.exceptions.Timeout("Превышено время ожидания")
        with pytest.raises(ConnectionError, match="Ошибка соединения"):
            converter.get_rate("USD", "EUR")

    @patch("converter.requests.get")
    def test_api_error_response_handled(self, mock_get, converter):
        """При ошибочном ответе API (result != success) — ValueError."""
        mock_resp = Mock()
        mock_resp.raise_for_status = Mock()
        mock_resp.json.return_value = {
            "result": "error",
            "error-type": "unsupported-code"
        }
        mock_get.return_value = mock_resp
        with pytest.raises(ValueError, match="API вернул ошибку"):
            converter.get_rate("INVALID", "EUR")

    @patch("converter.requests.get")
    def test_http_error_handled(self, mock_get, converter):
        """При HTTP-ошибке (например, 500) выбрасывается ConnectionError."""
        mock_get.side_effect = req.exceptions.HTTPError("500 Server Error")
        with pytest.raises(ConnectionError, match="Ошибка соединения"):
            converter.get_rate("USD", "EUR")


# ============================================================
#  ИНТЕГРАЦИОННЫЕ ТЕСТЫ (реальные запросы к API)
# ============================================================

@pytest.mark.integration
class TestRealAPI:
    """
    Тесты с реальными запросами к API.
    Требуют подключения к интернету.
    Запуск:  pytest test_converter.py -v -m integration
    """

    def test_real_convert_usd_to_eur(self, converter):
        """Реальная конвертация 100 USD → EUR возвращает положительное число."""
        result = converter.convert(100, "USD", "EUR")
        assert isinstance(result, float)
        assert result > 0

    def test_real_rate_usd_to_rub_in_range(self, converter):
        """Реальный курс USD → RUB находится в разумном диапазоне (50–200)."""
        rate = converter.get_rate("USD", "RUB")
        assert 50 < rate < 200

    def test_real_currencies_list_size(self, converter):
        """Реальный API возвращает список из более чем 50 валют."""
        currencies = converter.get_available_currencies()
        assert len(currencies) > 50
        assert "USD" in currencies
        assert "EUR" in currencies
        assert "RUB" in currencies