# from app import create_app
#
# app = create_app()
#
# if __name__ == '__main__':
#     app.run()


from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "Hello, Flask!"

if __name__ == "__main__":
    app.run()
