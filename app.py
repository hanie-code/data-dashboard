# app.py

from dash import Dash

# نمونه اصلی اپلیکیشن را تعریف می‌کنیم
# suppress_callback_exceptions=True برای اپلیکیشن‌های چندصفحه‌ای لازم است
app = Dash(__name__, suppress_callback_exceptions=True)
server = app.server