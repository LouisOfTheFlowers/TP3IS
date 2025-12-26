import requests
import pandas as pd

URL = "https://data.cityofnewyork.us/resource/h9gi-nx95.json"

PARAMS = {
    "$limit": 100000,   
    "$order": "crash_date DESC"
}

response = requests.get(URL, params=PARAMS)
data = response.json()

df = pd.DataFrame(data)

# selecionar e renomear colunas
columns = {
    "crash_date": "crash_date",
    "crash_time": "crash_time",
    "number_of_persons_injured": "persons_injured",
    "number_of_persons_killed": "persons_killed",
    "number_of_pedestrians_injured": "pedestrians_injured",
    "number_of_pedestrians_killed": "pedestrians_killed",
    "number_of_cyclist_injured": "cyclists_injured",
    "number_of_cyclist_killed": "cyclists_killed",
    "number_of_motorist_injured": "motorists_injured",
    "number_of_motorist_killed": "motorists_killed",
    "contributing_factor_vehicle_1": "factor_1",
    "contributing_factor_vehicle_2": "factor_2",
    "contributing_factor_vehicle_3": "factor_3",
    "contributing_factor_vehicle_4": "factor_4",
    "contributing_factor_vehicle_5": "factor_5",
    "vehicle_type_code1": "vehicle_1",
    "vehicle_type_code2": "vehicle_2",
    "vehicle_type_code3": "vehicle_3",
    "vehicle_type_code4": "vehicle_4",
    "vehicle_type_code5": "vehicle_5",
}# garantir que todas as colunas existem
for col in columns.keys():
    if col not in df.columns:
        df[col] = None

# agora sim, selecionar e renomear
df = df[list(columns.keys())].rename(columns=columns)

df.to_csv("collisions_raw.csv", index=False)

print("✅ CSV de colisões criado")


