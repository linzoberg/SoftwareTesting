"""
Модуль конвертера валют.
Получает актуальные курсы из открытого API open.er-api.com.
"""

import requests


class CurrencyConverter:
    """Класс для конвертации валют с использованием внешнего API."""

    API_URL = "https://open.er-api.com/v6/latest"

    def get_rate(self, from_currency: str, to_currency: str) -> float:
        """
        Получает текущий курс обмена между двумя валютами.

        :param from_currency: код исходной валюты (например, "USD")
        :param to_currency: код целевой валюты (например, "EUR")
        :return: курс обмена (float)
        :raises TypeError: если код валюты не является строкой
        :raises ValueError: если код пуст или валюта не найдена
        :raises ConnectionError: если API недоступен
        """
        if not isinstance(from_currency, str) or not isinstance(to_currency, str):
            raise TypeError("Код валюты должен быть строкой")

        from_currency = from_currency.strip().upper()
        to_currency = to_currency.strip().upper()

        if not from_currency or not to_currency:
            raise ValueError("Код валюты не может быть пустым")

        url = f"{self.API_URL}/{from_currency}"

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Ошибка соединения с API: {e}")

        data = response.json()

        if data.get("result") != "success":
            raise ValueError(f"API вернул ошибку для валюты '{from_currency}'")

        rates = data.get("rates", {})

        if to_currency not in rates:
            raise ValueError(f"Валюта '{to_currency}' не найдена в списке доступных")

        return float(rates[to_currency])

    def convert(self, amount, from_currency: str, to_currency: str) -> float:
        """
        Конвертирует денежную сумму из одной валюты в другую.

        :param amount: сумма для конвертации (int или float, >= 0)
        :param from_currency: код исходной валюты
        :param to_currency: код целевой валюты
        :return: сконвертированная сумма, округлённая до 2 знаков
        :raises TypeError: если сумма не является числом
        :raises ValueError: если сумма отрицательна
        """
        if not isinstance(amount, (int, float)):
            raise TypeError("Сумма должна быть числом")

        if amount < 0:
            raise ValueError("Сумма не может быть отрицательной")

        if amount == 0:
            return 0.0

        rate = self.get_rate(from_currency, to_currency)
        return round(amount * rate, 2)

    def get_available_currencies(self) -> list:
        """
        Возвращает список кодов всех доступных валют.

        :return: список строк с кодами валют (например, ["USD", "EUR", ...])
        :raises ConnectionError: если API недоступен
        """
        url = f"{self.API_URL}/USD"

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Ошибка соединения с API: {e}")

        data = response.json()

        if data.get("result") != "success":
            raise ValueError("Не удалось получить список валют от API")

        return list(data.get("rates", {}).keys())


if __name__ == "__main__":
    conv = CurrencyConverter()
    print("Получаю курсы валют...")
    currencies = conv.get_available_currencies()
    print(f"Доступно валют: {len(currencies)}")
    currencies_from = ["USD", "EUR", "GBP", "CNY", "AMD", "BYN", "INR", "RSD", "KZT"]
    for cur in currencies_from:
        result = conv.convert(100, cur, "RUB")
        print(f"100 {cur} = {result} RUB")
