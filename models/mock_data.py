import ast
import json
import re

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

import gzip
import sqlite3

gz_file_path = r'D:\Users\User\Downloads\Telegram Desktop\b_user.sql.gz'

# with gzip.open(gz_file_path, 'rt', encoding='utf-8') as f:
#     for line in f:
#         if True:
#             try:
#                 start = line.find('(')
#                 end = line.rfind(')') + 1
#                 tuple_str = line[start:end]
#
#                 tuple_str = tuple_str.replace('NULL', 'None')
#
#                 t = ast.literal_eval(tuple_str)
#
#                 # print(f"{t[6]} {t[7]}")
#                 # print(f"Email: {t[8]}")
#                 # print(f"Link: {t[13]}")
#                 if t[46] not in ("None", None) and len(t) >= 46:
#                     print(f"Link: {t[46]}")
#                     print(line)
#                     print("---")
#             except Exception as e:
#                 pass