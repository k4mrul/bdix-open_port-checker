import os
import sys

###Kivy main library###
from kivy.app import App
from kivy.lang import Builder
from kivy.clock import Clock

###Kivy material design library###
from kivymd.dialog import MDInputDialog, MDDialog
from kivymd.theming import ThemeManager
from kivymd.toast.kivytoast import toast

from kivymd.navigationdrawer import NavigationDrawerIconButton
###Importing library required for IP info###
import requests

###Importing library required for ping test###
import pythonping
from random import random

###Importing library required for port scan###
import socket

###Import threading###
import threading

####Main script start####
main_kv = """
#:import MDToolbar kivymd.toolbar.MDToolbar
#:import MDRectangleFlatButton kivymd.button.MDRectangleFlatButton

#:import MDSeparator kivymd.cards.MDSeparator
##:import NavigationLayout kivymd.navigationdrawer.NavigationLayout
#:import MDNavigationDrawer kivymd.navigationdrawer.MDNavigationDrawer
#:import NavigationDrawerSubheader kivymd.navigationdrawer.NavigationDrawerSubheader

<ContentNavigationDrawer@MDNavigationDrawer>:
    drawer_logo: app.resource_path("logo.png")

    NavigationDrawerSubheader:
        # text: "Menu:"
        
NavigationLayout:

    ContentNavigationDrawer:
        NavigationDrawerIconButton:
            icon: 'help-circle-outline'
            text: 'Help'
            on_release: app.how_to_use()
        
        NavigationDrawerIconButton:
            icon: 'update'
            text: 'Check update'
            on_release: app.updateChecker()
        
        NavigationDrawerIconButton:
            icon: 'account'
            text: 'About'
            on_release: app.aboutThisApp()
  
    BoxLayout: 
        orientation: 'vertical'
        spacing: dp(5)

        MDToolbar:
            id: toolbar
            title: app.title
            md_bg_color: app.theme_cls.primary_color
            background_palette: 'Primary'
            background_hue: '500'
            elevation: 10
            left_action_items:
                [['dots-vertical', lambda x: app.root.toggle_nav_drawer()]]

        FloatLayout:
            MDRectangleFlatButton:
                text: "BDIX Check"
                pos_hint: {'center_x': .5, 'center_y': .6}
                opposite_colors: True
                on_release: app.check_bdix()

            MDRectangleFlatButton:
                text: "Port forward check"
                pos_hint: {'center_x': .5, 'center_y': .5}
                opposite_colors: True
                # on_release: app.check_port_status()
                on_release: app.confirm_lan_connectivity()      

            Label:
                text: "Check whether you have BDIX connectivity and port forwarding capability"
                font_size: 21
                pos_hint: {'center_x': .5, 'center_y': .8}
                color: 1,0,0,1

            Widget:
"""
class Bdix(App):
    theme_cls = ThemeManager()
    theme_cls.primary_palette = 'Teal'
    title = "BDIX & Open Port Checker"

    port_addr = 16031 

    get_ip_address = ''
    get_isp_name = ''

    bdix_support = ''
  
    def build(self):
        self.icon = self.resource_path("logo.png")
        return Builder.load_string(main_kv)

    def callback_for_empty_call(self, *args):
        pass

    def resource_path(self, relative_path):
        if hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS, relative_path)
        return os.path.join(os.path.abspath("."), relative_path)

    # Test internet connectivity
    def is_connected(self):
        try:
            socket.create_connection(("www.google.com", 80))
            return True
        except OSError:
            pass
        return False

    def no_internet_dialog(self):
        dialog = MDDialog(
            title='Info', size_hint=(.8, .35), 
            text_button_ok='Ok',
            text="No internet connectivity.",
            events_callback=self.callback_for_empty_call
            )
        dialog.open()

    # Get socket info
    def getsock(self):
        try:
            s1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s1.bind(('', self.port_addr))
            s1.listen()
            accept_return = s1.accept()
            return accept_return
        except:
            pass

    # Threading
    def socket_thread(self):
        thr = threading.Thread(target=self.getsock)
        thr.start()

    def update_thread(self):
        thr = threading.Thread(target=self.get_update_result)
        thr.start()

    # Gather IP info
    def get_ip_info(self):
        if not (self.get_ip_address and self.get_isp_name):
            client_ip = requests.get('https://api.ipify.org').text
            ip_info = requests.get('https://api.ip.sb/geoip/%s' % client_ip).json()
            self.get_ip_address = ip_info['ip']
            self.get_isp_name = ip_info['organization']

    def wait_for_ip_info(self):
        toast("Checking... Please wait")
        Clock.schedule_once(self.check_port_status, 2)

    # Confirm whether directly connected with LAN or not
    def confirm_lan_connectivity(self):
        dialog = MDDialog(
            title='Info', size_hint=(.8, .35), text_button_ok='Continue',
            text="Please [color=#FF0000]connect directly to internet without router[/color] (ignore this if you already connected directly) and press 'Continue'.\nAlso, if you run this app for the first time, press 'Continue' and allow the firewall first. Then run the test again.",
            text_button_cancel='Help',
            events_callback=self.callback_for_confirm_lan_connectivity)
        dialog.open()

    def callback_for_confirm_lan_connectivity(self, *args):
        if 'Continue' == args[0]:
            self.wait_for_ip_info()
        else:
            self.how_to_use()

    #Initialize port scanning
    def pscan(self):
        s2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s2.settimeout(0.5)
        try:
            s2.connect((self.get_ip_address, self.port_addr))
            return True
        except: 
            return False

    def check_port_status(self, dt):
        if self.is_connected():
            self.get_ip_info()
            self.socket_thread()
            dialog = MDDialog(
                title='Port info', size_hint=(.8, .35), 
                text_button_ok='Ok',
                text=f"Your IP address: {self.get_ip_address}\nYour ISP name: {self.get_isp_name}\nCan forward port? {'[b][color=#0b6623]YES.[/color][/b] You can open any port. Your IP appears to be real/static IP ' if self.pscan() else '[b][color=#FF0000]NO.[/color][/b] Unable to forward. It seems your IP is not real/static or does not have port forwarding capability.'}",
                events_callback=self.callback_for_empty_call
                )
            dialog.open()

        else:
            self.no_internet_dialog()

    # BDIX check

    def get_avg_ping_result(self):
        get_response = pythonping.ping('mirror.xeonbd.com', size=40, count=10).rtt_avg_ms   #sending 40 bytes 10 times
        avg_ping = [get_response for x in range(10)]

        totalSum = 0
        for ping in avg_ping:
            totalSum = totalSum+ping 
            
        div_totalSum = totalSum / 10

        if int(div_totalSum) > 15:
            self.bdix_support = False
        else:
            self.bdix_support = True

    def check_bdix(self):
        if self.is_connected():
            if not self.bdix_support:
                self.get_avg_ping_result()

            dialog = MDDialog(
                title='Info', size_hint=(.8, .35), 
                text_button_ok='Ok',
                text=f"{'BDIX Supports' if self.bdix_support else 'BDIX does not support'}",
                events_callback=self.callback_for_empty_call
                )
            dialog.open()
        else:
            self.no_internet_dialog()

    # How to use this app
    def how_to_use(self):
        dialog = MDDialog(
            title='How to use', size_hint=(.8, .4), 
            text_button_ok="Ok",
            text="""For accurate result, you need to make sure the following things: 
            1. Your internet is idle (no one is using but you)
            2. You are directly connected to internet without router
            3. Allow this application through firewall (when prompt) & test again
            4. You are not connected with VPN
            """,
            events_callback=self.callback_for_empty_call
            )
        dialog.open()

    # Check for update
    def updateChecker(self):
        toast("Checking... Please wait")
        Clock.schedule_once(self.updateCheckerDialog, 2)
    
    def get_update_result(self):
        response = requests.get('https://raw.githubusercontent.com/k4mrul/bdix-open_port-checker/master/update.txt').text
        return response

    def updateCheckerDialog(self, dt):
        self.update_thread()
        dialog = MDDialog(
            title='Update info', size_hint=(.8, .4), 
            text_button_ok='Ok',
            text=self.get_update_result(),
            events_callback=self.callback_for_empty_call
            )
        dialog.open()

    # About this app
    def aboutThisApp(self):
        dialog = MDDialog(
            title='About', size_hint=(.8, .4), 
            text_button_ok='Ok',
            text="""Hello, Thank you for using this app. If you found a bug, feel free to contact with me at [color=#0b6623]contact@kamrul.dev[/color]
            """,
            events_callback=self.callback_for_empty_call
            )
        dialog.open()

Bdix().run()
