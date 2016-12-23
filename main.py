import os
from functools import partial

from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty
from kivy.clock import Clock
from kivy.uix.button import Button
from kivy.config import Config

import requests
import snowbird

# I don't think this is right but it seems to be
# what kivy thinks the resolution of the screen is
Config.set('graphics', 'width', '720')
Config.set('graphics', 'height', '480')

# Update the weather and webcams this often
UPDATE_FREQUENCY = 300 # seconds

class RootWidget(FloatLayout):
	""" The root widget contains all our other widgets."""

	def __init__(self, **kwargs):
		super(RootWidget, self).__init__(**kwargs)

		self.webcam_mode = False
		self.current_cam = 0
		self.weather_output = None
		
		# Initialize our widgets
		sdw = SnowDepthsWidget()
		iw = IconWidget()
		tw = TimestampWidget()
		nb = NextButton()
		self.ww = WebcamWidget()

		# and add them to our RootWidget so they show up
		self.add_widget(LogoWidget())
		self.add_widget(tw)
		self.add_widget(sdw)
		self.add_widget(iw)
		self.add_widget(self.ww)
		self.add_widget(nb)

		# Bind our button press to a function
		nb.bind(on_press=self.button_press)

		# Schedule our weather update
		# Note: we're passing our initialized widgets into the update_weather function
		# so that update_weather can populate them directly with new information
		Clock.schedule_once(partial(self.update_weather, sdw, iw, tw))
		Clock.schedule_interval(partial(self.update_weather, sdw, iw, tw), UPDATE_FREQUENCY)

		# Schedule our webcam update
		Clock.schedule_once(self.fetch_webcams, 5)
		Clock.schedule_interval(self.fetch_webcams, UPDATE_FREQUENCY)

	def update_weather(self, sdw, iw, tw, dt):
		""" Call snowbird.py to update the weather, and update the passed-in
		widgets directly."""

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
		""" Update our webcam images."""

		try:
			snowbird.fetch_webcams(self.weather_output['cams'])
		except requests.exceptions.ConnectionError as e:
			print("Error fetching webcams: %s" % e)
		except (TypeError, KeyError):
			print("Can't fetch cams until weather info has been downloaded")

	def show_image(self, widget, show):
		""" Just hides or shows the WebcamWidget. Colors are [R,G,B,A] where
		A is the alpha (transparancy)."""

		if show is True:
			widget.ids.cam.color = [1,1,1,1]
			widget.ids.cam.bg_color = [0,0,0,1]
			widget.ids.cam_label.color = [1,1,1,1]
		else:
			widget.ids.cam.color = [0,0,0,0]
			widget.ids.cam.bg_color = [0,0,0,0]
			widget.ids.cam_label.color = [0,0,0,0]

	def button_press(self, instance):
		""" Handle hiding and iterating through the webcam images when the button is pressed."""
		
		if not self.webcam_mode:
			self.webcam_mode = True

		if self.webcam_mode:
			print("Webcam mode. Current cam: %s" % self.current_cam)
			self.show_image(self.ww, True)
			cam_pictures = os.listdir(snowbird.CAMS_FOLDER)
			if self.current_cam == len(cam_pictures):
				self.show_image(self.ww, False)
				self.webcam_mode = False
				self.current_cam = 0
				print("Hiding webcams")
			else:
				self.ww.ids.cam.source = os.path.join(snowbird.CAMS_FOLDER, cam_pictures[self.current_cam])
				self.ww.ids.cam_label.text = cam_pictures[self.current_cam].replace("_", " ").replace(".jpg", "")
				self.current_cam += 1

class SnowDepthsWidget(BoxLayout):
	""" Handles showing the snow depth labels and numbers at the bottom of the screen."""

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
	""" Shows the current weather icon in the center of the screen.
	Will default to a No Wifi symbol if there is no internet connection on boot."""
	# TODO: Should show No Wifi if internet is lost after boot

	icon_source = StringProperty("/home/pi/snowbird/wifi.png")

	def __init__(self, **kwargs):
		super(IconWidget, self).__init__(**kwargs)

	def update(self, icon):
		self.icon_source = icon

class TimestampWidget(FloatLayout):
	""" Show the last-updated timestamp at the top of the screen."""

	timestamp = StringProperty()

	def __init__(self, **kwargs):
		super(TimestampWidget, self).__init__(**kwargs)

	def update(self, timestamp):
		self.timestamp = timestamp

class LogoWidget(FloatLayout):
	""" Snowbird logo."""
	pass

class NextButton(Button):
	""" Webcam button (whole screen)"""
	pass

class WebcamWidget(FloatLayout):
	""" Webcam image viewer."""
	pass

class SnowbirdApp(App):
	""" Kivy app class. Just returns a RootWidget."""
	def build(self):
		return RootWidget()

if __name__ == "__main__":
	SnowbirdApp().run()