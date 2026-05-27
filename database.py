"""
Модуль базы данных SQLite для управления списком покупок
Database module for managing shopping list items
"""

import sqlite3
from typing import List, Dict, Any


class Database:
    """Класс для работы с базой данных SQLite"""

    def __init__(self, db_path: str = "shopping.db"):
        """
        Инициализация базы данных

        Args:
            db_path: путь к файлу базы данных
        """
        self.db_path = db_path
        self._create_table()

    def _create_table(self) -> None:
        """
        Создание таблицы items, если она не существует
        Create items table if it doesn't exist
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    bought INTEGER DEFAULT 0
                )
            """)
            conn.commit()

    def get_all_items(self) -> List[Dict[str, Any]]:
        """
        Получение всех товаров из базы данных
        Get all items from database

        Returns:
            List[Dict]: список словарей с полями id, name, bought
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, bought FROM items ORDER BY bought ASC, id DESC")
            rows = cursor.fetchall()

        return [{"id": row[0], "name": row[1], "bought": bool(row[2])} for row in rows]

    def add_item(self, name: str) -> int:
        """
        Добавление нового товара
        Add new item

        Args:
            name: название товара

        Returns:
            int: ID добавленного товара
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO items (name, bought) VALUES (?, ?)", (name, 0))
            conn.commit()
            return cursor.lastrowid

    def update_item_status(self, item_id: int, bought: bool) -> None:
        """
        Обновление статуса покупки товара
        Update item bought status

        Args:
            item_id: ID товара
            bought: куплен (True) или нет (False)
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE items SET bought = ? WHERE id = ?", (int(bought), item_id))
            conn.commit()

    def delete_item(self, item_id: int) -> None:
        """
        Удаление товара по ID
        Delete item by ID

        Args:
            item_id: ID товара
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM items WHERE id = ?", (item_id,))
            conn.commit()

    def delete_bought_items(self) -> int:
        """
        Удаление всех купленных товаров
        Delete all bought items

        Returns:
            int: количество удаленных товаров
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM items WHERE bought = 1")
            deleted_count = cursor.rowcount
            conn.commit()
            return deleted_count