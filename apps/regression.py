import pandas as pd
import numpy as np
import joblib
import plotly.express as px
from dash import dcc, html, no_update
from dash.dependencies import Input, Output, State
import json
import gdown
import os
from app import app

# --- ۱. بارگذاری داده‌ها و تمام فایل‌های مدل ---

# ==============================================================================
# ## بخش سفارشی‌سازی ##
# !!! مهم: لطفاً مقادیر زیر را با اطلاعات واقعی پروژه خودتان جایگزین کنید
# ==============================================================================
# شناسه فایل (File ID) مربوط به فایل "final_dashboard_dataset.csv" در گوگل درایو
FILE_ID = '1LP5xE44rZJ0ep3N3Q5dxGci4EOT_-NV0'

# نام ستون قیمت واقعی در فایل CSV شما
ACTUAL_PRICE_COL = 'Price'

# نام ستون قیمت پیش‌بینی شده
PREDICTED_PRICE_COL = 'predicted'

# نام ستون برند
BRAND_COL = 'Brand'

# نام ستون دسته‌بندی
CATEGORY_COL = 'Category1'
# ==============================================================================

output_filename = 'final_dashboard_dataset.csv'

# دانلود هوشمند فایل (فقط بار اول)
if not os.path.exists(output_filename):
    print(f"در حال دانلود فایل نهایی داشبورد...")
    print("این فرآیند فقط یک بار انجام می‌شود و ممکن است چند دقیقه طول بکشد.")
    shareable_url = f'https://drive.google.com/uc?id={FILE_ID}'
    gdown.download(url=shareable_url, output=output_filename, quiet=False)
else:
    print(f"فایل '{output_filename}' از قبل وجود دارد. در حال خواندن...")

# خواندن دیتافریم و بارگذاری فایل‌های مدل
try:
    df = pd.read_csv(output_filename).dropna(subset=[BRAND_COL, CATEGORY_COL])
    model = joblib.load('your_model.pkl')
    scaler = joblib.load('scaler.pkl')
    with open('model_columns.json', 'r') as f:
        model_columns = json.load(f)
    # بارگذاری مقادیر پیش‌فرض برای پیش‌بینی دقیق
    with open('default_numeric_values.json', 'r') as f:
        default_numeric_values = json.load(f)
    print("تمام فایل‌های لازم با موفقیت بارگذاری شدند.")
except Exception as e:
    print(f"خطا در بارگذاری فایل‌ها: {e}")
    # در صورت بروز خطا، متغیرها را خالی مقداردهی می‌کنیم تا برنامه متوقف نشود
    df = pd.DataFrame({ACTUAL_PRICE_COL: [], PREDICTED_PRICE_COL: [], BRAND_COL: [], CATEGORY_COL: []})
    model, scaler, model_columns, default_numeric_values = None, None, None, None

# --- ۲. ساخت نمودارها ---
fig_scatter = px.scatter()
if not df.empty:
    fig_scatter = px.scatter(
        df, x=ACTUAL_PRICE_COL, y=PREDICTED_PRICE_COL,
        title='مقایسه قیمت واقعی و پیش‌بینی شده',
        labels={ACTUAL_PRICE_COL: 'قیمت واقعی (تومان)', PREDICTED_PRICE_COL: 'قیمت پیش‌بینی شده (تومان)'},
        hover_data=[BRAND_COL, CATEGORY_COL],
        trendline='ols', trendline_color_override='red'
    )

fig_importance = px.bar(title='اهمیت ویژگی‌ها (در حال توسعه)')

# --- ۳. تعریف چیدمان (Layout) داشبورد ---
layout = html.Div([
    html.H2('تحلیل مدل پیش‌بینی قیمت'), html.Hr(),
    html.Div([
        dcc.Graph(id='scatter-plot', figure=fig_scatter, style={'width': '60%', 'display': 'inline-block'}),
        dcc.Graph(id='importance-plot', figure=fig_importance, style={'width': '40%', 'display': 'inline-block'}),
    ]), html.Hr(),
    html.Div([
        html.H3('پیش‌بینی تعاملی قیمت'),
        dcc.Dropdown(
            id='category-dropdown',
            options=[{'label': c, 'value': c} for c in sorted(df[CATEGORY_COL].unique())],
            placeholder="ابتدا یک دسته‌بندی انتخاب کنید...", style={'marginBottom': 10}
        ),
        dcc.Dropdown(
            id='brand-dropdown',
            placeholder="یک برند انتخاب کنید...", style={'marginBottom': 10}
            # گزینه‌های این منو به صورت پویا و وابسته آپدیت می‌شود
        ),
        html.Button('پیش‌بینی کن', id='predict-button', n_clicks=0, style={'marginTop': 10}),
        html.Div(id='prediction-output', style={'marginTop': 20, 'fontSize': 20, 'fontWeight': 'bold'})
    ])
])

# --- ۴. تعریف Callback ها ---

# Callback برای آپدیت کردن گزینه‌های برند بر اساس دسته‌بندی (Dropdown وابسته)
@app.callback(
    [Output('brand-dropdown', 'options'),
     Output('brand-dropdown', 'value')],
    [Input('category-dropdown', 'value')]
)
def update_brand_options(selected_category):
    if selected_category is None:
        return [], None # اگر دسته‌بندی انتخاب نشده، لیست برندها خالی است

    filtered_df = df[df[CATEGORY_COL] == selected_category]
    brand_options = [{'label': b, 'value': b} for b in sorted(filtered_df[BRAND_COL].unique())]
    
    return brand_options, None # گزینه‌های جدید را برمی‌گردانیم و انتخاب قبلی را پاک می‌کنیم

# Callback برای پیش‌بینی تعاملی با منطق حرفه‌ای
@app.callback(
    Output('prediction-output', 'children'),
    Input('predict-button', 'n_clicks'),
    [State('brand-dropdown', 'value'), State('category-dropdown', 'value')]
)
def update_prediction(n_clicks, brand, category):
    if n_clicks > 0:
        if not all([brand, category]): return "لطفاً تمام ویژگی‌ها را انتخاب کنید."
        if not all([model, scaler, model_columns, default_numeric_values]): return "فایل‌های مدل به درستی بارگذاری نشده‌اند."
        try:
            # ۱. ساخت دیتافریم خام از ورودی کاربر
            input_data = pd.DataFrame([[brand, category]], columns=[BRAND_COL, CATEGORY_COL])

            # ۲. اضافه کردن ستون‌های عددی با مقادیر پیش‌فرض (میانگین)
            for col, value in default_numeric_values.items():
                input_data[col] = value

            # ۳. اعمال پیش‌پردازش (One-Hot Encoding)
            processed_input = pd.get_dummies(input_data)

            # ۴. هماهنگ کردن ستون‌ها با ستون‌های مدل آموزشی
            final_input = processed_input.reindex(columns=model_columns, fill_value=0)

            # ۵. مقیاس‌بندی داده‌های ورودی
            scaled_input = scaler.transform(final_input)
            
            # ۶. انجام پیش‌بینی
            predicted_price_log = model.predict(scaled_input)
            predicted_price_original = np.expm1(predicted_price_log)
            
            return f"قیمت پیش‌بینی شده: {predicted_price_original[0]:,.0f} تومان"
        except Exception as e:
            return f"خطا در هنگام پیش‌بینی: {e}"
    return ""

