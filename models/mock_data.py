MOCK_DATA = {
    "deposits": [
        {"id": "dep1", "name": "Накопительный", "amount": 50000, "status": "ACTIVE"},
        {"id": "dep2", "name": "Пенсионный", "amount": 100000, "status": "ACTIVE"}
    ],
    "accounts": [
        {"id": "acc1", "accountNumber": "1234567890", "amount": 150000, "availableAmount": 120000, "status": "ACTIVE"},
        {"id": "acc2", "accountNumber": "0987654321", "amount": 50000, "availableAmount": 50000, "status": "ACTIVE"}
    ],
    "products": [
        {"id": "prod1", "name": "Вклад 'Стандарт'", "code": "DEP_STANDARD", "type": "DEPOSIT"},
        {"id": "prod2", "name": "Вклад 'Премиум'", "code": "DEP_PREMIUM", "type": "DEPOSIT"},
        {"id": "prod3", "name": "Кредит 'Базовый'", "code": "CRD_BASIC", "type": "CREDIT"}
    ]
}