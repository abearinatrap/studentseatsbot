@echo off
rem really shouldn't be compiling this to use outside of computers with libraries already installed... 
rem its takes so much storage. this can be written much smaller in c++
pyinstaller --onefile --icon=sanchold.ico ticketprice.py 