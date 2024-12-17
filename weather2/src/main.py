import flet as ft
import requests
import sqlite3
import json

# 気象庁APIのURL設定
AREA_JSON_URL = "https://www.jma.go.jp/bosai/common/const/area.json"
FORECAST_URL_TEMPLATE = "https://www.jma.go.jp/bosai/forecast/data/forecast/{code}.json"

# SQLiteデータベース接続およびテーブル作成関数
def setup_database():
    conn = sqlite3.connect("weather_data.db")
    cursor = conn.cursor()

    # Weatherテーブル作成
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Weather (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        city TEXT NOT NULL,
        temperature INTEGER,
        condition TEXT,
        date TEXT NOT NULL
    )
    ''')

    conn.commit()
    conn.close()

# データ保存関数
def save_forecast_to_db(city, temperature, condition, date):
    conn = sqlite3.connect("weather_data.db")
    cursor = conn.cursor()

    cursor.execute('''
    INSERT INTO Weather (city, temperature, condition, date)
    VALUES (?, ?, ?, ?)
    ''', (city, temperature, condition, date))

    conn.commit()
    conn.close()

# 地域データを取得する関数
def fetch_area_data():
    response = requests.get(AREA_JSON_URL)
    if response.status_code == 200:
        return response.json()
    return None

# 指定地域の天気予報データを取得する関数
def fetch_weather_forecast(area_code):
    forecast_url = FORECAST_URL_TEMPLATE.format(code=area_code)
    response = requests.get(forecast_url)
    if response.status_code == 200:
        return response.json()
    return None

# Fletアプリケーションのメイン部分
def main(page: ft.Page):
    page.title = "天気予報アプリ"
    page.vertical_alignment = ft.MainAxisAlignment.START

    # UIコンポーネント
    area_dropdown = ft.Dropdown(label="地域を選択", width=300)
    forecast_output = ft.Column(spacing=10)
    error_text = ft.Text("", color="red")

    area_data = fetch_area_data()
    area_codes = {}

    if area_data:
        # 都道府県レベルの地域コードを取得
        for office_code, office_data in area_data["offices"].items():
            name = office_data["name"]
            area_dropdown.options.append(ft.dropdown.Option(name))
            area_codes[name] = office_code
    else:
        error_text.value = "地域データの取得に失敗しました。"

    def show_forecast(e):
        selected_area = area_dropdown.value

        if not selected_area:
            error_text.value = "地域を選択してください。"
            page.update()
            return

        area_code = area_codes.get(selected_area)
        if not area_code:
            error_text.value = "地域コードが見つかりません。"
            page.update()
            return

        forecast_data = fetch_weather_forecast(area_code)

        if not forecast_data:
            error_text.value = "天気予報データの取得に失敗しました。"
            page.update()
            return

        forecast_output.controls.clear()
        error_text.value = ""

        try:
            time_series = forecast_data[0]["timeSeries"]
            for ts in time_series:
                if "weathers" in ts["areas"][0]:
                    weather_output = []
                    for area in ts["areas"]:
                        area_name = area["area"]["name"]
                        weather_info = "\n".join(area["weathers"])
                        weather_output.append(f"{area_name}:\n{weather_info}")
                    forecast_text = ft.Text("\n\n".join(weather_output))

                    forecast_output.controls.append(forecast_text)

                    # データベースに保存する処理
                    temperature = int(ts['areas'][0].get("weathers", [{"temperature": None}])[0])
                    save_forecast_to_db(
                        city=area_name,
                        temperature=temperature,
                        condition="\n".join(weather_info),
                        date="Today"
                    )

        except Exception as ex:
            error_text.value = f"データ解析エラー: {str(ex)}"

        page.update()

    show_button = ft.ElevatedButton("天気予報を表示", on_click=show_forecast)

    # ページにコンポーネントを追加する部分
    page.add(
        ft.Text("日本の天気予報", size=24),
        area_dropdown,
        show_button,
        error_text,
        ft.Divider(),
        forecast_output
    )

# 初回起動処理およびUIスタート
if __name__ == "__main__":
    setup_database()  # データベース初期化
    ft.app(target=main)
