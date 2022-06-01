import pickle, bz2
from flask import Flask, request, jsonify, url_for, render_template
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from app_logger import log
from mongodb import mongodbconnection
import warnings
warnings.filterwarnings("ignore")


app = Flask(__name__)

# Import Classification and Regression model file
pickle_in = bz2.BZ2File('classification.pkl', 'rb')
R_pickle_in = bz2.BZ2File('regression.pkl', 'rb')
model_C = pickle.load(pickle_in)
model_R = pickle.load(R_pickle_in)

# Data retrieved from DB using mongoconnection module
try:
    dbcon = mongodbconnection(username='mongodb', password='12345')
    list_cursor = dbcon.getdata(dbName='FireDataML', collectionName='ml_task')
except Exception as e:
    log.error('Error in Connection to Mongo DB', e)

# Data From MongoDB is used for Standardization
try:
    df = pd.DataFrame(list_cursor)
    df.drop('_id', axis=1, inplace=True)
    log.info('DataFrame created')
    scaler = StandardScaler()
    X = df.drop(['FWI', 'Classes'], axis=1)
    # Standardize
    X_reg_scaled = scaler.fit_transform(X)
    log.info('Standardization done')
except Exception as e:
    log.error('Error in Data Preprocessing Operations', e)


# Route for homepage
@app.route('/')
def home():
    log.info('Home page loaded successfully')
    return render_template('index.html')


# Route for API Testing
@app.route('/predict_api', methods=['POST'])
def predict_api():
    try:
        data = request.json['data']
        print(data)
        log.info('Input from Api testing', data)
        new_data = [list(data.values())]
        final_data = scaler.transform(new_data)
        output = int(model_C.predict(final_data)[0])
        if output == 1:
            text = 'The Forest in Danger'
        else:
            text = 'Forest is Safe'
        return jsonify(text, output)
    except Exception as e:
        output = 'Check the in input again!'
        log.error('error in input from Postman',e)
        return jsonify(output)


# Route for Classification Model
@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = [float(x) for x in request.form.values()]
        final_features = [np.array(data)]
        final_features = scaler.transform(final_features)
        output = model_C.predict(final_features)[0]
        if output == 0:
            text = 'Forest is Safe!'
        else:
            text = 'Forest is in Danger!'
        return render_template('index.html', prediction_text1="{} , Chance of Fire is {}".format(text, output))
    except Exception as e:
        log.error('Input error, check input', e)
        return render_template('index.html', prediction_text1="Check the Input again!!!")


# Route for Regression Model
@app.route('/predictR', methods=['POST'])
def predictR():
    try:
        data = [float(x) for x in request.form.values()]
        data = [np.array(data)]
        data = scaler.transform(data)
        output = model_R.predict(data)[0]
        return render_template('index.html', prediction_text2="Fuel Moisture Code index is {:.4f}, Above 15 is consider High hazard rating".format(output))
    except Exception as e:
        log.error('Input error, check input', e)
        return render_template('index.html', prediction_text2="Check the Input again!!!")


# Run APP in Debug mode
if __name__ == "__main__":
    app.run(debug=True)