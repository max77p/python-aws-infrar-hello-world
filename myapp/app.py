from flask import Flask, render_template
import logging

# Flask is the constructor which accepts the name of the current module
app = Flask(__name__)

# defining route decorator
# Calls the associate function
@app.route("/")
def home():
    # rendering home.html from templates directory
    return render_template("home.html", value='200')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)