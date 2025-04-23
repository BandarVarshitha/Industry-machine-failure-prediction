from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
@app.route('/home')
def home():
    return render_template('index.html')

@app.route('/trends')
def trends():
    return render_template('Trends.html')

@app.route('/maintenance')
def maintenance():
    return render_template('Maintenance.html')

@app.route('/failure')
def failure():
    return render_template('Failure.html')

@app.route('/equipment_status')
def equipment_status():
    return render_template('Equipment_status.html')

if __name__ == '__main__':
    app.run(debug=True)
