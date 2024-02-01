serve:
	flask run

monitor:
	npx nodemon -e html,py,css --exec "make serve"
