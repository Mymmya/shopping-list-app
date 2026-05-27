"""
Главный модуль приложения "Список покупок"
Main module for "Shopping List" application
"""

from kivy.lang import Builder
from kivy.properties import StringProperty, BooleanProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.metrics import dp
from kivy.clock import Clock

from kivymd.app import MDApp
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton, MDRaisedButton, MDIconButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.list import OneLineAvatarIconListItem, ILeftBodyTouch, IRightBodyTouch
from kivymd.uix.selectioncontrol import MDCheckbox
from kivymd.uix.label import MDLabel

from database import Database

# KV-разметка с красивым интерфейсом
KV = '''
<CustomListItem@OneLineAvatarIconListItem>:
    IconLeftWidget:
        icon: "checkbox-blank-outline" if not root.active else "checkbox-marked-outline"
        on_release: root.toggle()
    
    IconRightWidget:
        icon: "trash-can-outline"
        theme_icon_color: "Custom"
        icon_color: "red"
        on_release: root.delete()
    
    MDLabel:
        id: label
        text: root.text
        font_style: "Body1"
        color: [0.5, 0.5, 0.5, 1] if root.active else [0, 0, 0, 1]
        markup: True

MDScreen:
    name: "main"
    
    MDTopAppBar:
        title: "Список покупок"
        elevation: 4
        md_bg_color: app.theme_cls.primary_color
        specific_text_color: "white"
        
        MDIconButton:
            icon: "filter-variant"
            on_release: app.open_filter_dialog()
            pos_hint: {"center_y": 0.5}
    
    MDScrollView:
        pos_hint: {"top": 0.95}
        size_hint: (1, 0.9)
        do_scroll_x: False
        
        MDList:
            id: container
            padding: dp(8)
            spacing: dp(8)
    
    MDFloatingActionButton:
        icon: "plus"
        pos_hint: {"right": 0.95, "bottom": 0.05}
        size_hint: None, None
        size: dp(56), dp(56)
        elevation: 8
        on_release: app.show_add_dialog()
    
    MDCard:
        id: filter_card
        orientation: "vertical"
        size_hint: (0.9, None)
        height: dp(200)
        pos_hint: {"center_x": 0.5, "center_y": 0.5}
        elevation: 6
        opacity: 0
        disabled: True
        radius: [dp(12), dp(12), dp(12), dp(12)]
        padding: dp(16)
        spacing: dp(12)
        
        MDLabel:
            text: "Фильтр товаров"
            font_style: "H6"
            halign: "center"
        
        MDSegmentedButton:
            id: filter_segmented
            size_hint_x: 1
            MDSegmentedButtonItem:
                text: "Все"
                on_press: app.apply_filter("all")
            MDSegmentedButtonItem:
                text: "Не куп."
                on_press: app.apply_filter("unbought")
            MDSegmentedButtonItem:
                text: "Куп."
                on_press: app.apply_filter("bought")
        
        MDRaisedButton:
            text: "Очистить купленные"
            md_bg_color: [0.9, 0.2, 0.2, 1]
            text_color: [1, 1, 1, 1]
            size_hint_x: 1
            on_release: app.clear_bought()
        
        MDIconButton:
            icon: "close"
            pos_hint: {"right": 1, "top": 1}
            size_hint: None, None
            size: dp(32), dp(32)
            on_release: app.close_filter_card()
'''


class CustomListItem(OneLineAvatarIconListItem):
    """Элемент списка с чекбоксом и иконкой удаления"""
    text = StringProperty("")
    active = BooleanProperty(False)
    item_id = None
    app = None

    def __init__(self, **kwargs):
        self.item_id = kwargs.pop('item_id', None)
        self.app = kwargs.pop('app', None)
        super().__init__(**kwargs)

    def toggle(self):
        """Переключение статуса товара"""
        self.active = not self.active
        if self.app and self.item_id:
            self.app.toggle_item_status(self.item_id, self.active)

    def delete(self):
        """Удаление товара"""
        if self.app and self.item_id:
            self.app.delete_item(self.item_id)


class MainApp(MDApp):
    """Главный класс приложения"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db = Database()
        self.current_filter = "all"
        self.dialog = None
        self.items_cache = []

    def build(self):
        """Сборка интерфейса приложения"""
        self.theme_cls.primary_palette = "Teal"
        self.theme_cls.theme_style = "Light"

        return Builder.load_string(KV)

    def on_start(self):
        """Действия при запуске приложения"""
        self.refresh_list()

    def refresh_list(self):
        """Обновление списка покупок на экране"""
        # Загружаем все товары из БД
        self.items_cache = self.db.get_all_items()

        # Применяем фильтр
        filtered_items = self._apply_filter()

        # Очищаем контейнер
        container = self.root.ids.container
        container.clear_widgets()

        # Добавляем товары в список
        for item in filtered_items:
            item_widget = CustomListItem(
                text=item['name'],
                active=item['bought'],
                item_id=item['id'],
                app=self
            )
            container.add_widget(item_widget)

    def _apply_filter(self):
        """Применение текущего фильтра к списку товаров"""
        if self.current_filter == "all":
            return self.items_cache
        elif self.current_filter == "bought":
            return [item for item in self.items_cache if item['bought']]
        elif self.current_filter == "unbought":
            return [item for item in self.items_cache if not item['bought']]
        return self.items_cache

    def toggle_item_status(self, item_id, is_bought):
        """Переключение статуса товара"""
        self.db.update_item_status(item_id, is_bought)
        self.refresh_list()

    def delete_item(self, item_id):
        """Удаление товара"""
        self.db.delete_item(item_id)
        self.refresh_list()

    def show_add_dialog(self):
        """Отображение диалогового окна для добавления нового товара"""
        if not self.dialog:
            text_field = MDTextField(
                hint_text="Введите название товара",
                helper_text="Например: Молоко",
                helper_text_mode="on_focus",
                required=True,
                size_hint_x=0.9
            )

            self.dialog = MDDialog(
                title="➕ Добавить товар",
                type="custom",
                content_cls=text_field,
                buttons=[
                    MDFlatButton(
                        text="ОТМЕНА",
                        text_color=self.theme_cls.primary_color,
                        on_release=lambda x: self.dialog.dismiss()
                    ),
                    MDRaisedButton(
                        text="ДОБАВИТЬ",
                        on_release=self.add_item_from_dialog
                    ),
                ],
            )

        # Очищаем поле ввода
        self.dialog.content_cls.text = ""
        self.dialog.open()

    def add_item_from_dialog(self, instance):
        """Добавление товара из диалогового окна"""
        item_name = self.dialog.content_cls.text.strip()

        if item_name:
            self.db.add_item(item_name)
            self.refresh_list()
            self.dialog.dismiss()

    def open_filter_dialog(self):
        """Открытие панели фильтрации"""
        filter_card = self.root.ids.filter_card
        filter_card.opacity = 1
        filter_card.disabled = False

    def close_filter_card(self):
        """Закрытие панели фильтрации"""
        filter_card = self.root.ids.filter_card
        filter_card.opacity = 0
        filter_card.disabled = True

    def apply_filter(self, filter_type):
        """Применение фильтра"""
        self.current_filter = filter_type
        self.refresh_list()
        self.close_filter_card()

    def clear_bought(self):
        """Очистка купленных товаров"""
        self.db.delete_bought_items()
        self.refresh_list()
        self.close_filter_card()


if __name__ == "__main__":
    MainApp().run()