from flask import Flask, render_template, request, jsonify, session
import mysql.connector
import json
import pandas as pd
import plotly
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import numpy as np
from functools import wraps
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-here')

# Конфигурация базы данных
DB_CONFIG = {
    'host': 'solatalogi.beget.app',
    'port': 3306,
    'database': 'productivity_bot',
    'user': 'productivity_bot',
    'password': '10012003Dd.',
    'charset': 'utf8mb4'
}


class ProductivityDB:
    def __init__(self, config=DB_CONFIG):
        self.config = config

    def get_connection(self):
        """Создает соединение с MySQL"""
        try:
            conn = mysql.connector.connect(**self.config)
            return conn
        except mysql.connector.Error as e:
            print(f"Ошибка подключения к БД: {e}")
            return None

    def get_all_users(self):
        """Получает список всех пользователей"""
        conn = self.get_connection()
        if not conn:
            return []

        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT user_id, data_json FROM users ORDER BY created_at DESC")
            users = cursor.fetchall()

            # Парсим JSON данные
            for user in users:
                if user['data_json']:
                    try:
                        data = json.loads(user['data_json'])
                        user.update(data)
                    except:
                        pass

            cursor.close()
            conn.close()
            return users
        except mysql.connector.Error as e:
            print(f"Ошибка получения пользователей: {e}")
            return []

    def get_user_stats(self, user_id):
        """Получает статистику конкретного пользователя"""
        conn = self.get_connection()
        if not conn:
            return []

        try:
            cursor = conn.cursor(dictionary=True)
            query = """
                    SELECT
                        date, sleep_duration, planned_tasks, completed_tasks, productive_hours_planned, productive_hours_used, ROUND(completed_tasks * 100.0 / NULLIF (planned_tasks, 0), 2) as task_completion_rate, ROUND(productive_hours_used * 100.0 / NULLIF (productive_hours_planned, 0), 2) as productivity_rate
                    FROM stats
                    WHERE user_id = %s
                    ORDER BY date DESC
                        LIMIT 100 \
                    """
            cursor.execute(query, (user_id,))
            stats = cursor.fetchall()

            cursor.close()
            conn.close()
            return stats
        except mysql.connector.Error as e:
            print(f"Ошибка получения статистики: {e}")
            return []

    def get_all_stats(self, limit=1000):
        """Получает всю статистику для анализа"""
        conn = self.get_connection()
        if not conn:
            return []

        try:
            cursor = conn.cursor(dictionary=True)
            query = """
                    SELECT s.*, \
                           u.data_json, \
                           ROUND(s.completed_tasks * 100.0 / NULLIF(s.planned_tasks, 0), 2)                           as task_completion_rate, \
                           ROUND(s.productive_hours_used * 100.0 / NULLIF(s.productive_hours_planned, 0), \
                                 2)                                                                                   as productivity_rate, \
                           ROUND((0.5 * (s.sleep_duration / 8.0) + \
                                  0.3 * (s.completed_tasks / NULLIF(s.planned_tasks, 1.0)) + \
                                  0.2 * (s.productive_hours_used / NULLIF(s.productive_hours_planned, 1.0))) * 10, \
                                 2)                                                                                   as productivity_score
                    FROM stats s
                             LEFT JOIN users u ON s.user_id = u.user_id
                    ORDER BY s.date DESC
                        LIMIT %s \
                    """
            cursor.execute(query, (limit,))
            stats = cursor.fetchall()

            # Парсим JSON данные пользователей
            for stat in stats:
                if stat['data_json']:
                    try:
                        user_data = json.loads(stat['data_json'])
                        stat.update(user_data)
                    except:
                        pass

            cursor.close()
            conn.close()
            return stats
        except mysql.connector.Error as e:
            print(f"Ошибка получения всей статистики: {e}")
            return []

    def get_daily_averages(self, days=30):
        """Получает средние значения за последние N дней"""
        conn = self.get_connection()
        if not conn:
            return {}

        try:
            cursor = conn.cursor(dictionary=True)
            query = """
                    SELECT AVG(sleep_duration)                                                      as avg_sleep, \
                           AVG(planned_tasks)                                                       as avg_planned_tasks, \
                           AVG(completed_tasks)                                                     as avg_completed_tasks, \
                           AVG(productive_hours_planned)                                            as avg_prod_planned, \
                           AVG(productive_hours_used)                                               as avg_prod_used, \
                           AVG(completed_tasks * 100.0 / NULLIF(planned_tasks, 0))                  as avg_task_completion_rate, \
                           AVG(productive_hours_used * 100.0 / NULLIF(productive_hours_planned, 0)) as avg_productivity_rate, \
                           COUNT(DISTINCT user_id)                                                  as unique_users, \
                           COUNT(*)                                                                 as total_records
                    FROM stats
                    WHERE date >= DATE_SUB(CURDATE(), INTERVAL %s DAY) \
                    """
            cursor.execute(query, (days,))
            result = cursor.fetchone()

            cursor.close()
            conn.close()
            return result
        except mysql.connector.Error as e:
            print(f"Ошибка получения средних значений: {e}")
            return {}

    def get_min_max_stats(self):
        """Получает минимальные и максимальные значения"""
        conn = self.get_connection()
        if not conn:
            return {}

        try:
            cursor = conn.cursor(dictionary=True)
            query = """
                    SELECT MIN(sleep_duration)           as min_sleep, \
                           MAX(sleep_duration)           as max_sleep, \
                           MIN(planned_tasks)            as min_planned_tasks, \
                           MAX(planned_tasks)            as max_planned_tasks, \
                           MIN(completed_tasks)          as min_completed_tasks, \
                           MAX(completed_tasks)          as max_completed_tasks, \
                           MIN(productive_hours_planned) as min_prod_planned, \
                           MAX(productive_hours_planned) as max_prod_planned, \
                           MIN(productive_hours_used)    as min_prod_used, \
                           MAX(productive_hours_used)    as max_prod_used
                    FROM stats \
                    """
            cursor.execute(query)
            result = cursor.fetchone()

            cursor.close()
            conn.close()
            return result
        except mysql.connector.Error as e:
            print(f"Ошибка получения min/max: {e}")
            return {}

    def get_user_comparison(self, user_id):
        """Сравнивает пользователя со средними показателями"""
        conn = self.get_connection()
        if not conn:
            return {}

        try:
            cursor = conn.cursor(dictionary=True)

            # Получаем статистику пользователя
            user_query = """
                         SELECT AVG(sleep_duration)                                                      as user_avg_sleep, \
                                AVG(planned_tasks)                                                       as user_avg_planned_tasks, \
                                AVG(completed_tasks)                                                     as user_avg_completed_tasks, \
                                AVG(productive_hours_planned)                                            as user_avg_prod_planned, \
                                AVG(productive_hours_used)                                               as user_avg_prod_used, \
                                AVG(completed_tasks * 100.0 / NULLIF(planned_tasks, 0))                  as user_task_completion_rate, \
                                AVG(productive_hours_used * 100.0 / NULLIF(productive_hours_planned, 0)) as user_productivity_rate, \
                                COUNT(*)                                                                 as user_records
                         FROM stats
                         WHERE user_id = %s \
                         """
            cursor.execute(user_query, (user_id,))
            user_stats = cursor.fetchone()

            # Получаем общую статистику
            total_query = """
                          SELECT AVG(sleep_duration)                                                      as total_avg_sleep, \
                                 AVG(planned_tasks)                                                       as total_avg_planned_tasks, \
                                 AVG(completed_tasks)                                                     as total_avg_completed_tasks, \
                                 AVG(productive_hours_planned)                                            as total_avg_prod_planned, \
                                 AVG(productive_hours_used)                                               as total_avg_prod_used, \
                                 AVG(completed_tasks * 100.0 / NULLIF(planned_tasks, 0))                  as total_task_completion_rate, \
                                 AVG(productive_hours_used * 100.0 / NULLIF(productive_hours_planned, 0)) as total_productivity_rate, \
                                 COUNT(DISTINCT user_id)                                                  as total_users, \
                                 COUNT(*)                                                                 as total_records
                          FROM stats \
                          """
            cursor.execute(total_query)
            total_stats = cursor.fetchone()

            cursor.close()
            conn.close()

            # Рассчитываем разницу в процентах
            comparison = {}
            if user_stats and total_stats:
                for key in ['avg_sleep', 'avg_planned_tasks', 'avg_completed_tasks',
                            'avg_prod_planned', 'avg_prod_used', 'task_completion_rate',
                            'productivity_rate']:
                    user_key = f'user_{key}'
                    total_key = f'total_{key}'

                    if user_stats.get(user_key) is not None and total_stats.get(total_key) is not None:
                        user_val = user_stats[user_key] or 0
                        total_val = total_stats[total_key] or 0

                        if total_val != 0:
                            diff_percent = ((user_val - total_val) / total_val) * 100
                        else:
                            diff_percent = 0

                        comparison[key] = {
                            'user': round(user_val, 2),
                            'average': round(total_val, 2),
                            'difference': round(diff_percent, 2),
                            'status': 'above' if diff_percent > 0 else 'below' if diff_percent < 0 else 'equal'
                        }

            return {
                'user_stats': user_stats,
                'total_stats': total_stats,
                'comparison': comparison
            }

        except mysql.connector.Error as e:
            print(f"Ошибка сравнения пользователя: {e}")
            return {}

    def get_recommendations(self, user_id):
        """Генерирует рекомендации для пользователя"""
        comparison = self.get_user_comparison(user_id)

        if not comparison or 'comparison' not in comparison:
            return []

        recommendations = []
        comp = comparison['comparison']

        # Рекомендации по сну
        if 'avg_sleep' in comp:
            sleep_data = comp['avg_sleep']
            if sleep_data['user'] < 6:
                recommendations.append({
                    'category': 'сон',
                    'message': 'Рекомендуется увеличить продолжительность сна. Цель: 7-9 часов в сутки.',
                    'priority': 'высокий'
                })
            elif sleep_data['user'] > 10:
                recommendations.append({
                    'category': 'сон',
                    'message': 'Возможно, слишком много сна. Оптимально 7-9 часов.',
                    'priority': 'низкий'
                })

        # Рекомендации по продуктивности
        if 'productivity_rate' in comp:
            prod_data = comp['productivity_rate']
            if prod_data['user'] < 60:
                recommendations.append({
                    'category': 'продуктивность',
                    'message': 'Попробуйте метод Pomodoro (25 минут работы / 5 минут отдыха).',
                    'priority': 'высокий'
                })

        # Рекомендации по задачам
        if 'task_completion_rate' in comp:
            task_data = comp['task_completion_rate']
            if task_data['user'] < 70:
                recommendations.append({
                    'category': 'задачи',
                    'message': 'Ставьте реалистичные цели. Разбивайте большие задачи на подзадачи.',
                    'priority': 'средний'
                })

        return recommendations


# Создаем экземпляр базы данных
db = ProductivityDB()


# Маршруты Flask
@app.route('/')
def index():
    """Главная страница"""
    return render_template('index.html')


@app.route('/stats')
def stats():
    """Страница статистики"""
    # Получаем средние значения
    averages = db.get_daily_averages(30)

    # Получаем min/max значения
    min_max = db.get_min_max_stats()

    # Получаем последние записи для графика
    all_stats = db.get_all_stats(100)

    # Создаем графики с помощью Plotly
    graphs = []

    if all_stats:
        df = pd.DataFrame(all_stats)

        # График распределения сна


        # График выполнения задач
        if 'task_completion_rate' in df.columns:
            fig2 = px.scatter(df, x='date', y='task_completion_rate',
                              title='Процент выполнения задач по дням',
                              labels={'date': 'Дата', 'task_completion_rate': '% выполнения'},
                              color_discrete_sequence=['#2ecc71'])
            fig2.update_layout(
                template='plotly_white',
                height=500,
                showlegend=False,
                xaxis_title="Дата",
                yaxis_title="% выполнения задач",
                font=dict(size=12),
                hovermode='x unified'
            )
            fig2.update_traces(mode='markers+lines', marker=dict(size=8))
            graphs.append(plotly.io.to_json(fig2))

        # График сравнения пользователей
        if 'user_id' in df.columns:
            user_avg = df.groupby('user_id').agg({
                'sleep_duration': 'mean',
                'task_completion_rate': 'mean',
                'productivity_rate': 'mean'
            }).reset_index()

            fig3 = go.Figure()
            fig3.add_trace(go.Bar(
                name='Средний сон',
                x=user_avg['user_id'].astype(str),
                y=user_avg['sleep_duration'],
                marker_color='#3498db'
            ))
            fig3.add_trace(go.Bar(
                name='% выполнения задач',
                x=user_avg['user_id'].astype(str),
                y=user_avg['task_completion_rate'],
                marker_color='#2ecc71'
            ))
            fig3.add_trace(go.Bar(
                name='% продуктивности',
                x=user_avg['user_id'].astype(str),
                y=user_avg['productivity_rate'],
                marker_color='#e74c3c'
            ))

            fig3.update_layout(
                title='Сравнение пользователей',
                barmode='group',
                template='plotly_white',
                height=500,
                xaxis_title="ID пользователя",
                yaxis_title="Значение",
                font=dict(size=12),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            graphs.append(plotly.io.to_json(fig3))

    return render_template('stats.html',
                           averages=averages,
                           min_max=min_max,
                           graphs=graphs,
                           total_stats=len(all_stats))

@app.route('/user_stats', methods=['GET', 'POST'])
def user_stats():
    """Персональная статистика пользователя"""
    user_id = None
    user_data = None
    comparison = None
    recommendations = []
    user_stats_data = []

    if request.method == 'POST':
        user_id = request.form.get('user_id')
        if user_id and user_id.isdigit():
            user_id = int(user_id)
            session['user_id'] = user_id
        else:
            user_id = session.get('user_id')
    else:
        user_id = session.get('user_id')

    if user_id:
        # Получаем данные пользователя
        users = db.get_all_users()
        user_data = next((u for u in users if u.get('user_id') == user_id), None)

        # Получаем статистику
        user_stats_data = db.get_user_stats(user_id)

        # Получаем сравнение
        comparison = db.get_user_comparison(user_id)

        # Получаем рекомендации
        recommendations = db.get_recommendations(user_id)

    # Получаем список всех пользователей для выпадающего списка
    all_users = db.get_all_users()

    return render_template('user_stats.html',
                           user_id=user_id,
                           user_data=user_data,
                           user_stats=user_stats_data,
                           comparison=comparison,
                           recommendations=recommendations,
                           all_users=all_users)


@app.route('/api/user_stats/<int:user_id>')
def api_user_stats(user_id):
    """API для получения статистики пользователя"""
    stats_data = db.get_user_stats(user_id)
    return jsonify(stats_data)


@app.route('/recommendations')
def recommendations():
    """Страница с рекомендациями"""
    user_id = session.get('user_id')
    user_recommendations = []
    general_recommendations = []

    if user_id:
        user_recommendations = db.get_recommendations(user_id)

    # Общие рекомендации
    general_recommendations = [
        {
            'category': 'сон',
            'message': 'Спите 7-9 часов в сутки для оптимальной продуктивности',
            'priority': 'высокий'
        },
        {
            'category': 'продуктивность',
            'message': 'Используйте технику Pomodoro: 25 минут работы, 5 минут отдыха',
            'priority': 'средний'
        },
        {
            'category': 'задачи',
            'message': 'Планируйте не более 3 важных задач в день',
            'priority': 'средний'
        },
        {
            'category': 'перерывы',
            'message': 'Делайте перерыв каждые 90 минут для поддержания концентрации',
            'priority': 'низкий'
        }
    ]

    return render_template('recommendations.html',
                           user_recommendations=user_recommendations,
                           general_recommendations=general_recommendations,
                           user_id=user_id)


@app.route('/personal_data')
def personal_data():
    """Персональные данные пользователя"""
    user_id = session.get('user_id')
    user_data = None
    stats_summary = None

    if user_id:
        users = db.get_all_users()
        user_data = next((u for u in users if u.get('user_id') == user_id), None)

        # Получаем статистику для сводки
        stats = db.get_user_stats(user_id)
        if stats:
            df = pd.DataFrame(stats)
            stats_summary = {
                'total_days': len(df),
                'avg_sleep': df['sleep_duration'].mean() if 'sleep_duration' in df.columns else 0,
                'avg_task_completion': df['task_completion_rate'].mean() if 'task_completion_rate' in df.columns else 0,
                'avg_productivity': df['productivity_rate'].mean() if 'productivity_rate' in df.columns else 0,
                'last_update': df['date'].max() if 'date' in df.columns else None
            }

    return render_template('personal_data.html',
                           user_data=user_data,
                           stats_summary=stats_summary,
                           user_id=user_id)


@app.route('/api/global_averages')
def api_global_averages():
    """API для получения глобальных средних значений"""
    averages = db.get_daily_averages(30)
    return jsonify(averages)


@app.route('/api/min_max_stats')
def api_min_max_stats():
    """API для получения min/max значений"""
    min_max = db.get_min_max_stats()
    return jsonify(min_max)


@app.route('/api/all_users')
def api_all_users():
    """API для получения списка пользователей"""
    users = db.get_all_users()
    return jsonify(users)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)