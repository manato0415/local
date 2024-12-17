import flet as ft
import requests

# 気象庁APIのURL
AREA_JSON_URL = "https://www.jma.go.jp/bosai/common/const/area.json"
FORECAST_URL_TEMPLATE = "https://www.jma.go.jp/bosai/forecast/data/forecast/{code}.json"


def fetch_area_data():
    """地域データを取得"""
    response = requests.get(AREA_JSON_URL)
    if response.status_code == 200:
        return response.json()
    return None


def fetch_weather_forecast(area_code):
    """指定地域の天気予報データを取得"""
    forecast_url = FORECAST_URL_TEMPLATE.format(code=area_code)
    response = requests.get(forecast_url)
    if response.status_code == 200:
        return response.json()
    return None


def main(page: ft.Page):
    page.title = "天気予報アプリ"
    page.vertical_alignment = ft.MainAxisAlignment.START

    # UIコンポーネント
    area_dropdown = ft.Dropdown(label="地域を選択", width=300)
    forecast_output = ft.Column(spacing=10)
    error_text = ft.Text("", color="red")

    # 地域データの取得
    area_data = fetch_area_data()
    area_codes = {}  # 地域名とコードの辞書

    if area_data:
        # 正しい都道府県レベルの地域コードを取得
        for office_code, office_data in area_data["offices"].items():
            name = office_data["name"]
            # officesの直下のコードを使用
            area_dropdown.options.append(ft.dropdown.Option(name))
            area_codes[name] = office_code
    else:
        error_text.value = "地域データの取得に失敗しました。"

    # 天気予報を取得して表示する関数
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

        # 天気情報を解析して表示
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
                    forecast_output.controls.append(ft.Text("\n\n".join(weather_output)))
                    break
        except Exception as ex:
            error_text.value = f"データ解析エラー: {str(ex)}"

        page.update()

    # イベントハンドラ設定
    show_button = ft.ElevatedButton("天気予報を表示", on_click=show_forecast)

    # ページにコンポーネントを追加
    page.add(
        ft.Text("日本の天気予報", size=24),
        area_dropdown,
        show_button,
        error_text,
        ft.Divider(),
        forecast_output,
    )


# Fletアプリケーションの起動
if __name__ == "__main__":
    ft.app(target=main)
