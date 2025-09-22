# OCR-AITranslate-Overlay-Realtime
I am developing a real-time screen translation tool using Tesseract OCR, translation AI models and Overlays.
# pip install pytesseract
Add to Windows PATH:
1.Go to Start → type Environment Variables → open Edit the system environment variables.
2.On the Advanced tab, click Environment Variables….
3.In the System variables section, select Path → Edit.
4.Add the path to the Tesseract installation folder, for example:
C:\Program Files\Tesseract-OCR
5.Click OK → OK → open a new terminal → try typing:
tesseract --version
If the version appears → success