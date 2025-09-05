# index.py

from dash import dcc, html
from dash.dependencies import Input, Output

# اپلیکیشن اصلی را از فایل app وارد می‌کنیم
from app import app, server

# ماژول‌های مربوط به هر صفحه را وارد می‌کنیم
# فعلاً فقط رگرسیون را داریم
from apps import regression

# چیدمان اصلی و کلی برنامه
app.layout = html.Div([
    html.H1('Digikala Analysis Dashboard'),
    
    # تعریف تب‌ها
    dcc.Tabs(id='tabs-main', value='tab-regression', children=[
        dcc.Tab(label='Price Prediction Analysis', value='tab-regression'),
        # در آینده می‌توانید تب‌های دیگر را اینجا اضافه کنید
        # dcc.Tab(label='Fake Data Detection', value='tab-fake-data'),
    ]),
    
    # محتوای تب‌ها در این بخش نمایش داده می‌شود
    html.Div(id='tabs-content')
])

# این callback بر اساس تب انتخاب شده، محتوای مربوطه را نمایش می‌دهد
@app.callback(
    Output('tabs-content', 'children'),
    Input('tabs-main', 'value')
)
def render_content(tab):
    if tab == 'tab-regression':
        return regression.layout
    # elif tab == 'tab-fake-data':
    #     return fake_data.layout

# این بخش برای اجرای برنامه ضروری است
if __name__ == '__main__':
  app.run(debug=True)