import os, re
import time, base64
import requests, json

from io import BytesIO
from typing import Union

class OCRSolverError(Exception):
	def __init__(self, err_message):
		super().__init__(f"{err_message}")


class OCRSolver:
	def __init__(self, *, image_path=None, image_base64=None):
		self.token = None
		self.img_b64 = image_base64
		self.img_path = image_path
		self.session = requests.Session()
		self.headers = {
			"Accept": "*/*",
			"origin": "https://imgtotext.net",
			"referer": "https://imgtotext.net",
			"accept-language": "vi-VN,vi;q=0.9,fr-FR;q=0.8,fr;q=0.7,en-US;q=0.6,en;q=0.5",
			"User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36"
		}
		
		self.setup()
	
	
	def setup(self) -> None:
		site = self.session.get('https://imgtotext.net/')
		comp = re.compile(r'"_token" value=\s*"([^"]+)"')
		token_found = comp.findall(site.text)
		if not token_found:
			raise OCRSolverError("API token not found.")
		
		self.token = token_found[0]
		self.session.cookies = site.cookies
	
	
	def upload_image(self) -> str:
		time_upload = f"{int(time.time() * 1000)}"
		
		payload = {
			"_token": self.token,
			"fiLes": "",
			"url_upload": "",
			"url_upload": "",
			"time": time_upload,
			"from": "png, jpg, jpeg, gif, jfif, pdf, webp, bmp, heif, heic, JPEG",
			"upload": "upload"
		}
		
		if self.img_path:
			files = [("file", ("image.png", open(self.img_path, "rb")))]
		
		elif self.img_b64:
			image_base = BytesIO(base64.b64decode(self.img_b64))
			files = [("file", ("image.png", image_base))]
		
		upload = self.session.post("https://imgtotext.net/upload", data=payload, files=files)
		
		if upload.status_code != 200 or upload.text != "true":
			raise OCRSolverError("Image upload failed.")
		
		return time_upload
	
	
	def convert_image(self) -> None:
		payload = {
			"_token": self.token,
			"url_upload": "",
			"url_upload": "",
			"fileNames[]": "image.png",
			"convert": ""
		}
		
		if self.img_path:
			files = [("fiLes", ("image.png", open(self.img_path, "rb")))]
		
		elif self.img_b64:
			image_base = BytesIO(base64.b64decode(self.img_b64))
			files = [("fiLes", ("image.png", image_base))]
		
		convert = self.session.post("https://imgtotext.net/", data=payload, files=files)
		
		if convert.status_code != 200:
			raise OCRSolverError("Image convert failed.")
	
	
	def extract(self) -> Union[str, None]:
		if not self.img_path and not self.img_b64:
			raise OCRSolverError("Image data is missing...")
		
		uploaded_time = self.upload_image()
		self.convert_image()
		
		fileName = f"imgtotext.net-{uploaded_time}-image.png"
		payload = {
			"_token": self.token,
			"fileName": fileName,
			"zipFileName": fileName,
			"fromExt": "png, jpg, jpeg, gif, jfif, pdf, webp, bmp, heif, heic, JPEG",
			"toExt": ".txt"
		}
		
		solve = self.session.post("https://imgtotext.net/image-to-text", data=payload)
		try:
			solve_data = solve.json()
		except:
			solve_data = {}
		
		if not solve_data.get("text"):
			return None
		
		return "".join(solve_data["text"].strip().split())