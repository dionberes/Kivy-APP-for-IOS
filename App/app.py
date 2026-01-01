import requests
from bs4 import BeautifulSoup
import json
import os
import re
import threading
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.config import Config
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.graphics import Color, RoundedRectangle
from kivy.properties import BooleanProperty



class HoverBehavior:
    hovered = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Window.bind(mouse_pos=self._on_mouse_move)
        self.register_event_type('on_enter')
        self.register_event_type('on_leave')

    def _on_mouse_move(self, window, pos):
        if not self.get_root_window():
            return
        inside = self.collide_point(*self.to_widget(*pos))
        if inside and not self.hovered:
            self.hovered = True
            Window.set_system_cursor("hand")
            self.dispatch('on_enter')
        elif not inside and self.hovered:
            self.hovered = False
            Window.set_system_cursor("arrow")
            self.dispatch('on_leave')

    def on_enter(self, *args):
        pass

    def on_leave(self, *args):
        pass

class RoundedBox(BoxLayout):
    def __init__(self, color, **kwargs):
        super().__init__(**kwargs)
        self.bg_color = color
        with self.canvas.before:
            Color(*self.bg_color)
            self.rect = RoundedRectangle(radius=[25])
        self.bind(pos=self._update_rect, size=self._update_rect)

    def _update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size


class CustomLabel(Label):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.font_name = "Roboto"

class RoundedButton(Button, HoverBehavior):
    def __init__(self, bg_color=(0.2, 0.6, 0.8, 1), **kwargs):
        super().__init__(**kwargs)
        self.background_color = (0, 0, 0, 0)
        self.foreground_color = (1, 1, 1, 1)
        self.hint_text_color = (1, 1, 1, 1)
        self.background_normal = ""
        self.padding = [10, 10]

        with self.canvas.before:
            self._bg_color = Color(0.67, 0.67, 0.8, 0.3)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[10])
        self.bind(pos=self._update_rect, size=self._update_rect)

    def on_enter(self, *args):
        self._bg_color.rgba = (0.67, 0.67, 0.8, 0.2)
    def on_leave(self, *args):
        self._bg_color.rgba = (0.67, 0.67, 0.8, 0.3)
    def _update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size


class CircleButton(Button, HoverBehavior):
    def __init__(self, bg_color=(0.2, 0.6, 0.8, 1), **kwargs):
        super().__init__(**kwargs)
        self.background_color = (0, 0, 0, 0)
        self.foreground_color = (1, 1, 1, 1)
        self.hint_text_color = (1, 1, 1, 1)
        self.background_normal = ""
        self.padding = [10, 10]

        with self.canvas.before:
            self._bg_color = Color(0.67, 0.67, 0.8, 0.3)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[30])
            self.bind(pos=self._update_rect, size=self._update_rect)

    def on_enter(self, *args):
        self._bg_color.rgba = (0.67, 0.67, 0.8, 0.2)
    def on_leave(self, *args):
        self._bg_color.rgba = (0.67, 0.67, 0.8, 0.3)
    def _update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size







Window.size = (393 , 852)
APPNAME = "Dashboard"
CURRENTMATERIAL = "gold"



class Scrapper:
    def __init__(self):
        self.urlGold = 'https://www.gold.de/kurse/goldpreis/'
        self.urlSilver = 'https://www.gold.de/kurse/silberpreis/'
        self.headers = {'User-Agent': 'Mozilla/5.0'}
        self.data = {}


    def timetablefix(self, text):
        text = text.replace('| |', '|')
        
        text = text.replace('USD', ' USD | ')
        text = text.replace('EUR', ' EUR | ')
        text = text.replace(':', ': ')
        text = text.replace('USD | ', 'USD | \n')
        text = text.replace(' %', '% | ')

        text = text.replace('Aktuell', '\nAktuell')
        text = text.replace('Performance', '\nPerformance')
        text = text.replace('Allzeit', '\nAllzeit')
        text = text.replace('Vortag', '\nVortag')
        text = text.replace('Veränderung', '\nVeränderung')
        text = text.replace('Tageshoch', '\nTageshoch')
        text = text.replace('Tagestief', '\nTagestief')
        text = text.replace('Allzeithoch', '\nAllzeithoch')

        text = re.sub(r'[0-9.,\s]+CHF', '', text)   
        text = re.sub(r'(\|\s*[0-9.,\s]+%)\s*\|', '|', text)
        
        lines = []
        for line in text.split('\n'):
            clean_line = line.strip().rstrip('|').strip()
            if clean_line:
                lines.append(clean_line)
        
        return '\n\n\n'.join(lines)

    def scrape_and_save(self):
        try:
            # --- Gold Scraping ---
            resG = requests.get(self.urlGold, headers=self.headers, timeout=10)
            soupG = BeautifulSoup(resG.text, 'html.parser')
            
            # --- Silver Scraping ---
            resS = requests.get(self.urlSilver, headers=self.headers, timeout=10)
            soupS = BeautifulSoup(resS.text, 'html.parser')


            timetable_section = soupG.find('section', class_='kurstable')
            timetableSilver = soupS.find('section', class_='kurstable')
            if timetable_section:
                raw_text = timetable_section.get_text(strip=True)
                cleaned_timetable = self.timetablefix(raw_text)
            else:
                cleaned_timetable = "Error"
            if timetableSilver:
                raw_text_s = timetableSilver.get_text(strip=True)
                cleaned_timetableS = self.timetablefix(raw_text_s)
            else:
                cleaned_timetableS = "Error"

            def _get_text(elem, default="N/A"):
                return elem.text.strip() if elem else default

            # --- Data Saver ---
            self.data['gold'] = {
                'price': _get_text(soupG.find('div', class_='em_preis_ml au_gold_eur')),
                'change': _get_text(soupG.find('div', class_='em_preis_ulur')),
                'timetable': cleaned_timetable,
                'update': _get_text(soupG.find('span', class_='fz12 cdgrau'))
            }

            self.data['silver'] = {
                'price': _get_text(soupS.find('div', class_='em_preis_ml au_silber_eur')),
                'change': _get_text(soupS.find('div', class_='em_preis_ulur')),
                'timetableSilver': cleaned_timetableS,
                'timetable': cleaned_timetableS,
                'update': self.data['gold']['update']
            }

            # --- JSON ---
            if not os.path.exists('assets'):
                os.makedirs('assets')

            with open('assets/data.json', 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=4)
            
            print("Daten erfolgreich in assets/data.json gespeichert!")

        except Exception as e:
            print(f"Fehler beim Scraping: {e}")

        print("Scrappy finished.")


class BasicLayoutGOLD(FloatLayout):

    def __init__(self, **kwargs):
        super(BasicLayoutGOLD, self).__init__(**kwargs)


        with open('assets/data.json', 'r', encoding='utf-8') as f:
            self.data = json.load(f)

        main_container = BoxLayout(
                    orientation='vertical', 
                    spacing=30, 
                    padding=[40, 100, 40, 40],
                    size_hint=(1, 2),
                    pos_hint={'center_x': 0.5, 'center_y': 0.02}
                )
            
        self.price_box = RoundedBox(color=(0.67, 0.67, 0.8, 0.3), size_hint=(1, 0.15), pos_hint={'center_x': 0.5})
        self.timetable_box = RoundedBox(color=(0.67, 0.67, 0.8, 0.3), size_hint=(1, 0.5), pos_hint={'center_x': 0.5})

        self.price_box.add_widget(Image(source='assets/Images/golddot.png', size_hint=(0.5, 0.5), pos_hint={'center_x': 1, 'center_y': 0.5}))
        self.price_box.add_widget(Label(text = self.data['gold']['price'], font_size=24, bold=True, pos_hint={'center_x': 1, 'center_y': 0.5}))

        self.timetable_box.add_widget(Label(text = self.data['gold']['timetable'], font_size=12,bold=True, pos_hint={'center_x': 0.5, 'center_y': 0.5}))

        self.add_widget(RoundedButton(text="Switch", size_hint=(0.3, 0.05), pos_hint={'center_x': 0.425, 'center_y': 0.1},background_color=(0.2,0.4,0.8,0.5), on_release=self.change_to_silver))

        ReloadBtn = CircleButton(
            size_hint=(None, None), 
            size=(45, 45),          
            pos_hint={'center_x': 0.65, 'center_y': 0.1},
            background_color=(0.2, 0.4, 0.8, 0.5),
            on_release=lambda inst: App.get_running_app().ScrapperThreading(inst)
        )

        icon = Image(
            source='assets/Images/reload.png',
            size=(15,15),
            size_hint=(None, None),
            pos_hint={'center_x': 0.65, 'center_y': 0.1}
        )

        self.add_widget(icon)
        self.add_widget(ReloadBtn)
        

        main_container.add_widget(self.price_box)
        main_container.add_widget(self.timetable_box)
        main_container.add_widget(BoxLayout()) 
        self.add_widget(main_container)

    def change_to_silver(self, instance):
        if self.parent and self.parent.manager:
            self.parent.manager.current = "silver"
            self.parent.manager.transition.direction = "left"


class GoldScreen(Screen):
    def __init__(self, **kwargs):
        super(GoldScreen, self).__init__(**kwargs)
        self.scrapper = Scrapper()
        self.scrapper.scrape_and_save()
        self.data = self.scrapper.data

        self.add_widget(Image(source='assets/Images/bg1.jpg', size_hint=(1.3, 1.3), pos_hint={'center_x': 0.5, 'center_y': 0.5}))

        self.add_widget(BasicLayoutGOLD())

class BasicLayoutSILVER(FloatLayout):
    def __init__(self, **kwargs):
        super(BasicLayoutSILVER, self).__init__(**kwargs)


        with open('assets/data.json', 'r', encoding='utf-8') as f:
            self.data = json.load(f)

        main_container = BoxLayout(
                    orientation='vertical', 
                    spacing=30, 
                    padding=[40, 100, 40, 40],
                    size_hint=(1, 2),
                    pos_hint={'center_x': 0.5, 'center_y': 0.02}
                )
            
        self.price_box = RoundedBox(color=(0.67, 0.67, 0.8, 0.3), size_hint=(1, 0.15), pos_hint={'center_x': 0.5})
        self.timetable_box = RoundedBox(color=(0.67, 0.67, 0.8, 0.3), size_hint=(1, 0.5), pos_hint={'center_x': 0.5})


        self.price_box.add_widget(Image(source='assets/Images/silverdot.png', size_hint=(0.5, 0.5), pos_hint={'center_x': 1, 'center_y': 0.5}))
        self.price_box.add_widget(Label(text = self.data['silver']['price'], font_size=24, bold=True, pos_hint={'center_x': 1, 'center_y': 0.5}))

        self.timetable_box.add_widget(Label(text = self.data['silver'].get('timetable', self.data['silver'].get('timetableSilver', 'N/A')), font_size=12,bold=True, pos_hint={'center_x': 0.5, 'center_y': 0.5}))

        self.add_widget(RoundedButton(text="Switch", size_hint=(0.3, 0.05), pos_hint={'center_x': 0.425, 'center_y': 0.1},background_color=(0.2,0.4,0.8,0.5), on_release=self.change_to_silver))

        ReloadBtn = CircleButton(
            size_hint=(None, None), 
            size=(45, 45),          
            pos_hint={'center_x': 0.65, 'center_y': 0.1},
            background_color=(0.2, 0.4, 0.8, 0.5),
            on_release=lambda inst: App.get_running_app().ScrapperThreading(inst)
        )

        icon = Image(
            source='assets/Images/reload.png',
            size=(15,15),
            size_hint=(None, None),
            pos_hint={'center_x': 0.65, 'center_y': 0.1}
        )

        self.add_widget(icon)
        self.add_widget(ReloadBtn)
        

        main_container.add_widget(self.price_box)
        main_container.add_widget(self.timetable_box)
        main_container.add_widget(BoxLayout()) 
        self.add_widget(main_container)

    def change_to_silver(self, instance):
        if self.parent and self.parent.manager:
            self.parent.manager.current = "gold"
            self.parent.manager.transition.direction = "right"

class SilverScreen(Screen):
    def __init__(self, **kwargs):
        super(SilverScreen, self).__init__(**kwargs)
        self.scrapper = Scrapper()
        self.scrapper.scrape_and_save()
        self.data = self.scrapper.data

        self.add_widget(Image(source='assets/Images/bg1.jpg', size_hint=(1.3, 1.3), pos_hint={'center_x': 0.5, 'center_y': 0.5}))

        self.add_widget(BasicLayoutSILVER())



class MyApp(App):
    def build(self):
        scraper = Scrapper()
        scraper.scrape_and_save()

        if os.path.exists('assets/Images/icon.ico'):
            self.icon = 'assets/Images/icon.ico'

        self.title = APPNAME

        CURRENT = ScreenManager()
        CURRENT.add_widget(GoldScreen(name="gold"))
        CURRENT.add_widget(SilverScreen(name="silver"))

        CURRENT.current = "gold"

        return CURRENT
    
    def ScrapperThreading(self, instance):
        instance.disabled = True 

        thread = threading.Thread(target=self.run_scrapper_logic, args=(instance,))
        thread.daemon = True
        thread.start()

    def run_scrapper_logic(self, btn_instance):
        try:
            scraper_obj = Scrapper()
            scraper_obj.scrape_and_save()
            
            Clock.schedule_once(lambda dt: self.update_finished(btn_instance))
        except Exception as e:
            print(f"Error: {e}")
            Clock.schedule_once(lambda dt: self.update_finished(btn_instance))

    def update_finished(self, btn_instance):
        btn_instance.disabled = False
        print("DONE")

if __name__ == '__main__':
    MyApp().run()