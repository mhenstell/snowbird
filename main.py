import os

from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty
from kivy.uix.image import Image, AsyncImage
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.uix.button import Button
from kivy.config import Config
Config.set('graphics', 'width', '720')
Config.set('graphics', 'height', '480')

from functools import partial
import requests
import snowbird

UPDATE_FREQUENCY = 300 # seconds

class RootWidget(FloatLayout):
	def __init__(self, **kwargs):
		super(RootWidget, self).__init__(**kwargs)

		self.webcam_mode = False
		self.current_cam = 0
		self.weather_output = None
		
		sdw = SnowDepthsWidget()
		iw = IconWidget()
		tw = TimestampWidget()
		nb = NextButton()
		self.ww = WebcamWidget()

		self.add_widget(LogoWidget())
		self.add_widget(tw)
		self.add_widget(sdw)
		self.add_widget(iw)
		self.add_widget(self.ww)
		self.add_widget(nb)

		nb.bind(on_press=self.button_press)

		Clock.schedule_once(partial(self.update_weather, sdw, iw, tw))
		Clock.schedule_interval(partial(self.update_weather, sdw, iw, tw), UPDATE_FREQUENCY)

		Clock.schedule_once(self.fetch_webcams, 5)
		Clock.schedule_interval(self.fetch_webcams, UPDATE_FREQUENCY)

	def update_weather(self, sdw, iw, tw, dt):
		html = snowbird.fetch_weather()
		self.weather_output = snowbird.parse_weather(html)
		print("Weather: %s" % self.weather_output)

		try:
			icon_basename = snowbird.fetch_icon(self.weather_output["icon_url"])

			sdw.update(self.weather_output)
			iw.update("/tmp/" + icon_basename)
			tw.update(self.weather_output["timestamp"])
		except KeyError:
			print("Unable to update weather")

	def fetch_webcams(self, dt):
		try:
			snowbird.fetch_webcams(self.weather_output['cams'])
		except requests.exceptions.ConnectionError as e:
			print("Error fetching webcams: %s" % e)
		except (TypeError, KeyError):
			print("Can't fetch cams until weather info has been downloaded")

	def show_image(self, widget, show):
		if show is True:
			widget.ids.cam.color = [1,1,1,1]
			widget.ids.cam.bg_color = [0,0,0,1]
			widget.ids.cam_label.color = [1,1,1,1]
		else:
			widget.ids.cam.color = [0,0,0,0]
			widget.ids.cam.bg_color = [0,0,0,0]
			widget.ids.cam_label.color = [0,0,0,0]

	def button_press(self, instance):
		
		if not self.webcam_mode:
			self.webcam_mode = True

		if self.webcam_mode:
			print("Webcam mode. Current cam: %s" % self.current_cam)
			self.show_image(self.ww, True)
			cam_pictures = os.listdir(snowbird.CAMS_FOLDER)
			# print(cam_pictures)
			if self.current_cam == len(cam_pictures):
				self.show_image(self.ww, False)
				self.webcam_mode = False
				self.current_cam = 0
				print("Hiding webcams")
			else:
				self.ww.ids.cam.source = os.path.join(snowbird.CAMS_FOLDER, cam_pictures[self.current_cam])
				# self.ww.ids.cam_label.text = snowbird.CAM_NAMES[cam_pictures[self.current_cam]]
				self.ww.ids.cam_label.text = cam_pictures[self.current_cam].replace("_", " ").replace(".jpg", "")
				self.current_cam += 1

class SnowDepthsWidget(BoxLayout):
	twelve_hr = StringProperty()
	twentyfour_hr = StringProperty()
	fourtyeight_hr = StringProperty()
	depth = StringProperty()

	def __init__(self, **kwargs):
		super(SnowDepthsWidget, self).__init__(**kwargs)

	def update(self, output):
		try:
			self.twelve_hr = output["twelve-hour"] + '"'
			self.twentyfour_hr = output["twenty-four-hour"] + '"'
			self.fourtyeight_hr = output["forty-eight-hour"] + '"'
			self.depth = output["current-depth"] + '"'
		except Exception as e:
			print("Error getting weather: %s" % e)

class IconWidget(FloatLayout):
	icon_source = StringProperty("/home/pi/snowbird/wifi.png")

	def __init__(self, **kwargs):
		super(IconWidget, self).__init__(**kwargs)

	def update(self, icon):
		self.icon_source = icon

class LogoWidget(FloatLayout):
	pass

class TimestampWidget(FloatLayout):
	timestamp = StringProperty()

	def __init__(self, **kwargs):
		super(TimestampWidget, self).__init__(**kwargs)

	def update(self, timestamp):
		self.timestamp = timestamp

class NextButton(Button):
	pass

class WebcamWidget(FloatLayout):
	pass

class SnowbirdApp(App):
	def build(self):
		return RootWidget()

if __name__ == "__main__":
	SnowbirdApp().run()