import sqlite3
from config import DATABASE_PATH


class Database:
    """Класс для работы с базой данных SQLite"""
    
    def __init__(self, db_path: str = DATABASE_PATH):
        """Инициализация подключения к базе данных"""
        self.conn = sqlite3.connect(db_path, check_same_thread=False, timeout=10.0)
        self.cursor = self.conn.cursor()
        self.create_tables()
        self.create_generations_table()
        self.update_users_table_for_referrals()
        self.update_users_table_for_generations()
        self.create_referral_earnings_table()
        self.create_payments_table()
        self.create_generation_purchases_table()
    
    def create_tables(self):
        """Создаёт необходимые таблицы, если они не существуют"""
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                agreed_to_terms INTEGER DEFAULT 0,
                balance REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                referrer_id INTEGER,
                referral_balance REAL DEFAULT 0.0,
                referral_code TEXT UNIQUE,
                generations INTEGER DEFAULT 0
            )
        ''')
    
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS pending_actions (
                user_id INTEGER PRIMARY KEY,
                action_type TEXT,
                action_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
    
        self.conn.commit()
    
    def update_users_table_for_generations(self):
        """Добавляет поле generations в таблицу users (для старых БД)"""
        self.cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in self.cursor.fetchall()]
    
        if 'generations' not in columns:
            try:
                self.cursor.execute('ALTER TABLE users ADD COLUMN generations INTEGER DEFAULT 0')
                self.conn.commit()
                print("✅ Добавлено поле generations в таблицу users")
            except Exception as e:
                print(f"⚠️ Ошибка добавления поля generations: {e}")
    
    def create_generation_purchases_table(self):
        """Создаёт таблицу для хранения покупок генераций"""
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS generation_purchases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                payment_id TEXT UNIQUE NOT NULL,
                user_id INTEGER NOT NULL,
                package_size INTEGER NOT NULL,
                amount REAL NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        self.conn.commit()
    
    def save_generation_purchase(self, payment_id: str, user_id: int, package_size: int, amount: float):
        """Сохраняет покупку генераций в БД"""
        self.cursor.execute('''
            INSERT INTO generation_purchases (payment_id, user_id, package_size, amount, status)
            VALUES (?, ?, ?, ?, 'pending')
        ''', (payment_id, user_id, package_size, amount))
        self.conn.commit()
        print(f"💾 Покупка генераций сохранена: payment_id={payment_id}, user_id={user_id}, package={package_size}, amount={amount}")
    
    def get_generation_purchase(self, payment_id: str):
        """Получает покупку генераций по payment_id"""
        self.cursor.execute('SELECT * FROM generation_purchases WHERE payment_id = ?', (payment_id,))
        row = self.cursor.fetchone()
        if row:
            return {
                'id': row[0],
                'payment_id': row[1],
                'user_id': row[2],
                'package_size': row[3],
                'amount': row[4],
                'status': row[5],
                'created_at': row[6],
                'completed_at': row[7]
            }
        return None
    
    def update_generation_purchase_status(self, payment_id: str, status: str):
        """Обновляет статус покупки генераций"""
        self.cursor.execute('''
            UPDATE generation_purchases 
            SET status = ?, completed_at = CURRENT_TIMESTAMP 
            WHERE payment_id = ?
        ''', (status, payment_id))
        self.conn.commit()
        print(f"✅ Статус покупки генераций обновлён: payment_id={payment_id}, status={status}")
    
    def add_generations(self, user_id: int, amount: int):
        """Добавляет генерации пользователю"""
        user = self.get_user(user_id)
        if user:
            current_generations = user.get('generations', 0)
            new_generations = current_generations + amount
            print(f"⚡ Пополнение генераций: User {user_id}, Old: {current_generations}, Add: {amount}, New: {new_generations}")
            
            self.cursor.execute('''
                UPDATE users SET generations = ? WHERE user_id = ?
            ''', (new_generations, user_id))
            self.conn.commit()
            
            updated_user = self.get_user(user_id)
            print(f"✅ Генерации после обновления: {updated_user.get('generations', 0)}")
    
    def subtract_generations(self, user_id: int, amount: int = 1):
        """Списывает генерации у пользователя"""
        user = self.get_user(user_id)
        if user:
            current_generations = user.get('generations', 0)
            new_generations = max(0, current_generations - amount)
            print(f"⚡ Списание генераций: User {user_id}, Old: {current_generations}, Subtract: {amount}, New: {new_generations}")
            
            self.cursor.execute('''
                UPDATE users SET generations = ? WHERE user_id = ?
            ''', (new_generations, user_id))
            self.conn.commit()
            
            return True
        return False
    
    def get_user_generations(self, user_id: int):
        """Получает количество генераций пользователя"""
        user = self.get_user(user_id)
        return user.get('generations', 0) if user else 0
    

    def has_purchased_generations(self, user_id: int) -> bool:
        """Проверяет, покупал ли пользователь генерации"""
        self.cursor.execute('''
            SELECT COUNT(*) FROM generation_purchases 
            WHERE user_id = ? AND status = 'succeeded'
        ''', (user_id,))
        count = self.cursor.fetchone()[0]
        return count > 0

    def create_payments_table(self):
        """Создаёт таблицу для хранения платежей"""
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                payment_id TEXT UNIQUE NOT NULL,
                user_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                paid_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        self.conn.commit()
    
    def save_payment(self, payment_id: str, user_id: int, amount: float):
        """Сохраняет платёж в БД"""
        self.cursor.execute('''
            INSERT INTO payments (payment_id, user_id, amount, status)
            VALUES (?, ?, ?, 'pending')
        ''', (payment_id, user_id, amount))
        self.conn.commit()
        print(f"💾 Платёж сохранён: payment_id={payment_id}, user_id={user_id}, amount={amount}")
    
    def get_payment(self, payment_id: str):
        """Получает платёж по ID"""
        self.cursor.execute('SELECT * FROM payments WHERE payment_id = ?', (payment_id,))
        row = self.cursor.fetchone()
        if row:
            return {
                'id': row[0],
                'payment_id': row[1],
                'user_id': row[2],
                'amount': row[3],
                'status': row[4],
                'created_at': row[5],
                'paid_at': row[6]
            }
        return None
    
    def update_payment_status(self, payment_id: str, status: str):
        """Обновляет статус платежа"""
        self.cursor.execute('''
            UPDATE payments 
            SET status = ?, paid_at = CURRENT_TIMESTAMP 
            WHERE payment_id = ?
        ''', (status, payment_id))
        self.conn.commit()
        print(f"✅ Статус платежа обновлён: payment_id={payment_id}, status={status}")
        
    
    def create_generations_table(self):
        """Создаёт таблицу для хранения генераций"""
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS generations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                type TEXT NOT NULL,
                file_url TEXT NOT NULL,
                prompt TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        self.conn.commit()
    
    def update_users_table_for_referrals(self):
        """Добавляет поля для реферальной системы в таблицу users (для старых БД)"""
        self.cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in self.cursor.fetchall()]
    
        if 'referral_code' not in columns:
            try:
                self.cursor.execute('ALTER TABLE users ADD COLUMN referrer_id INTEGER')
                self.cursor.execute('ALTER TABLE users ADD COLUMN referral_balance REAL DEFAULT 0.0')
                self.cursor.execute('ALTER TABLE users ADD COLUMN referral_code TEXT UNIQUE')
                self.conn.commit()
                print("✅ Добавлены поля для реферальной системы")
            except Exception as e:
                print(f"⚠️ Ошибка добавления полей: {e}")
    
    def create_referral_earnings_table(self):
        """Создаёт таблицу для истории реферальных начислений"""
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS referral_earnings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                from_user_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                payment_amount REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                FOREIGN KEY (from_user_id) REFERENCES users (user_id)
            )
        ''')
        self.conn.commit()
    
    def generate_referral_code(self, user_id: int):
        """Генерирует уникальный реферальный код для пользователя"""
        import random
        import string
        
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            self.cursor.execute('SELECT user_id FROM users WHERE referral_code = ?', (code,))
            if not self.cursor.fetchone():
                self.cursor.execute('UPDATE users SET referral_code = ? WHERE user_id = ?', (code, user_id))
                self.conn.commit()
                return code
    
    def get_referral_code(self, user_id: int):
        """Получает реферальный код пользователя"""
        self.cursor.execute('SELECT referral_code FROM users WHERE user_id = ?', (user_id,))
        result = self.cursor.fetchone()
        return result[0] if result and result[0] else None
    
    def set_referrer(self, user_id: int, referrer_id: int):
        """Устанавливает реферера для пользователя"""
        self.cursor.execute('UPDATE users SET referrer_id = ? WHERE user_id = ?', (referrer_id, user_id))
        self.conn.commit()
    
    def get_user_by_referral_code(self, referral_code: str):
        """Получает пользователя по реферальному коду"""
        self.cursor.execute('SELECT user_id FROM users WHERE referral_code = ?', (referral_code,))
        result = self.cursor.fetchone()
        return result[0] if result else None
    
    def add_referral_earning(self, user_id: int, from_user_id: int, amount: float, payment_amount: float):
        """Добавляет реферальное начисление"""
        self.cursor.execute('''
            INSERT INTO referral_earnings (user_id, from_user_id, amount, payment_amount)
            VALUES (?, ?, ?, ?)
        ''', (user_id, from_user_id, amount, payment_amount))
    
        self.conn.commit()
        
        self.cursor.execute('''
            UPDATE users SET referral_balance = referral_balance + ? WHERE user_id = ?
        ''', (amount, user_id))
        
        self.conn.commit()
    
    def get_referral_stats(self, user_id: int):
        """Получает статистику по рефералам"""
        self.cursor.execute('SELECT COUNT(*) FROM users WHERE referrer_id = ?', (user_id,))
        referrals_count = self.cursor.fetchone()[0]
        
        self.cursor.execute('SELECT COALESCE(SUM(amount), 0.0) FROM referral_earnings WHERE user_id = ?', (user_id,))
        total_earned = self.cursor.fetchone()[0]
        
        return {
            'referrals_count': referrals_count,
            'total_earned': total_earned
        }
    
    def save_generation(self, user_id: int, generation_type: str, file_url: str, prompt: str = ""):
        """Сохраняет генерацию в базу данных"""
        self.cursor.execute('''
            INSERT INTO generations (user_id, type, file_url, prompt)
            VALUES (?, ?, ?, ?)
        ''', (user_id, generation_type, file_url, prompt))
        self.conn.commit()
    
    def get_user_photos(self, user_id: int):
        """Получает все оживлённые фото пользователя"""
        self.cursor.execute('''
            SELECT file_url, prompt, created_at FROM generations
            WHERE user_id = ? AND type = 'photo_animation'
            ORDER BY created_at DESC
        ''', (user_id,))
        return self.cursor.fetchall()
    
    def get_user_videos(self, user_id: int):
        """Получает все видео пользователя"""
        self.cursor.execute('''
            SELECT file_url, prompt, created_at FROM generations
            WHERE user_id = ? AND type = 'video_generation'
            ORDER BY created_at DESC
        ''', (user_id,))
        return self.cursor.fetchall()
    
    def get_user_edited_images(self, user_id: int):
        """Получает все отредактированные изображения пользователя"""
        self.cursor.execute('''
            SELECT file_url, prompt, created_at FROM generations
            WHERE user_id = ? AND type = 'image_editing'
            ORDER BY created_at DESC
        ''', (user_id,))
        return self.cursor.fetchall()
    
    def add_user(self, user_id: int, username: str = None, first_name: str = None, 
                 last_name: str = None):
        """Добавляет нового пользователя в базу данных"""
        self.cursor.execute('''
            INSERT OR IGNORE INTO users (user_id, username, first_name, last_name, balance, generations)
            VALUES (?, ?, ?, ?, 0.0, 1)
        ''', (user_id, username, first_name, last_name))
        self.conn.commit()
    
    def get_user(self, user_id: int):
        """Получает информацию о пользователе"""
        self.cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        row = self.cursor.fetchone()
        if row:
            return {
                'user_id': row[0],
                'username': row[1],
                'first_name': row[2],
                'last_name': row[3],
                'agreed_to_terms': row[4],
                'balance': row[5],
                'created_at': row[6],
                'referrer_id': row[7] if len(row) > 7 else None,
                'referral_balance': row[8] if len(row) > 8 else 0.0,
                'referral_code': row[9] if len(row) > 9 else None,
                'generations': row[10] if len(row) > 10 else 0
            }
        return None
    
    def update_user_agreement(self, user_id: int):
        """Обновляет статус согласия пользователя с условиями"""
        self.cursor.execute('''
            UPDATE users SET agreed_to_terms = 1 WHERE user_id = ?
        ''', (user_id,))
        self.conn.commit()
    
    def user_agreed_to_terms(self, user_id: int) -> bool:
        """Проверяет, согласился ли пользователь с условиями"""
        self.cursor.execute('SELECT agreed_to_terms FROM users WHERE user_id = ?', (user_id,))
        result = self.cursor.fetchone()
        return result[0] == 1 if result else False
    
    def add_to_balance(self, user_id: int, amount: float):
        """Добавляет средства к балансу пользователя"""
        user = self.get_user(user_id)
        if user:
            new_balance = user['balance'] + amount
            print(f"💰 Пополнение баланса: User {user_id}, Old: {user['balance']}, Add: {amount}, New: {new_balance}")
            self.update_user_balance(user_id, new_balance)
            updated_user = self.get_user(user_id)
            print(f"✅ Баланс после обновления: {updated_user['balance']}")
    
    def update_user_balance(self, user_id: int, new_balance: float):
        """Обновляет баланс пользователя"""
        print(f"📝 Обновление баланса в БД: User {user_id}, New Balance: {new_balance}")
        self.cursor.execute('''
            UPDATE users SET balance = ? WHERE user_id = ?
        ''', (new_balance, user_id))
        self.conn.commit()

    
    def save_pending_action(self, user_id: int, action_type: str, action_data: str):
        """Сохраняет незавершённое действие пользователя"""
        self.cursor.execute('''
            INSERT OR REPLACE INTO pending_actions (user_id, action_type, action_data)
            VALUES (?, ?, ?)
        ''', (user_id, action_type, action_data))
        self.conn.commit()
    
    def get_pending_action(self, user_id: int):
        """Получает незавершённое действие пользователя"""
        self.cursor.execute('SELECT action_type, action_data FROM pending_actions WHERE user_id = ?', (user_id,))
        result = self.cursor.fetchone()
        if result:
            pending = {'action_type': result[0], 'action_data': result[1]}
            print(f"📥 Получен pending action для user {user_id}: {pending['action_type']}")
            return pending
        print(f"⚠️ Pending action не найден для user {user_id}")
        return None
    
    def clear_pending_action(self, user_id: int):
        """Удаляет незавершённое действие после выполнения"""
        self.cursor.execute('DELETE FROM pending_actions WHERE user_id = ?', (user_id,))
        self.conn.commit()
        
    def get_total_users_count(self):
        """Получает общее количество пользователей"""
        self.cursor.execute("SELECT COUNT(*) FROM users")
        count = self.cursor.fetchone()[0]
        return count
    
    def get_new_users_count(self, days=7):
        """Получает количество новых пользователей за последние N дней"""
        self.cursor.execute("""
            SELECT COUNT(*) 
            FROM users 
            WHERE created_at >= datetime('now', '-' || ? || ' days')
        """, (days,))
        return self.cursor.fetchone()[0]
    
    def get_total_generations_count(self):
        """Получает общее количество генераций"""
        self.cursor.execute("SELECT COUNT(*) FROM generations")
        count = self.cursor.fetchone()[0]
        return count
    
    def get_generations_by_type(self):
        """Получает количество генераций по типам"""
        self.cursor.execute("""
            SELECT type, COUNT(*) 
            FROM generations 
            GROUP BY type
        """)
        results = self.cursor.fetchall()
        return {row[0]: row[1] for row in results}
    
    def get_total_payments_sum(self):
        """Получает общую сумму успешных платежей"""
        self.cursor.execute("""
            SELECT COALESCE(SUM(amount), 0.0) 
            FROM payments 
            WHERE status = 'succeeded'
        """)
        result = self.cursor.fetchone()[0]
        return result if result else 0.0
    
    def get_payments_count(self):
        """Получает количество успешных платежей"""
        self.cursor.execute("""
            SELECT COUNT(*) 
            FROM payments 
            WHERE status = 'succeeded'
        """)
        return self.cursor.fetchone()[0]
    
    def get_recent_payments_sum(self, days=7):
        """Получает сумму платежей за последние N дней"""
        self.cursor.execute("""
            SELECT COALESCE(SUM(amount), 0.0)
            FROM payments 
            WHERE status = 'succeeded' 
            AND paid_at >= datetime('now', '-' || ? || ' days')
        """, (days,))
        result = self.cursor.fetchone()[0]
        return result if result else 0.0
    
    def get_active_users_count(self, days=7):
        """Получает количество активных пользователей (сделавших хотя бы 1 генерацию)"""
        self.cursor.execute("""
            SELECT COUNT(DISTINCT user_id) 
            FROM generations 
            WHERE created_at >= datetime('now', '-' || ? || ' days')
        """, (days,))
        return self.cursor.fetchone()[0]
    
    def get_top_users_by_generations(self, limit=10):
        """Получает топ пользователей по количеству генераций"""
        self.cursor.execute("""
            SELECT u.user_id, u.username, u.first_name, COUNT(g.id) as gen_count
            FROM users u
            JOIN generations g ON u.user_id = g.user_id
            GROUP BY u.user_id
            ORDER BY gen_count DESC
            LIMIT ?
        """, (limit,))
        return self.cursor.fetchall()
    
    def get_referral_stats_total(self):
        """Получает общую статистику по рефералам"""
        self.cursor.execute("SELECT COUNT(*) FROM users WHERE referrer_id IS NOT NULL")
        total_referrals = self.cursor.fetchone()[0]
        
        self.cursor.execute("SELECT COALESCE(SUM(amount), 0.0) FROM referral_earnings")
        total_referral_earnings = self.cursor.fetchone()[0]
        
        return {
            'total_referrals': total_referrals,
            'total_earnings': total_referral_earnings
        }

    def __del__(self):
        """Закрывает соединение при удалении объекта"""
        if hasattr(self, 'conn'):
            self.conn.close()