import os
from tokenize import String
from pythermalcomfort.models import pmv_ppd
from pythermalcomfort.models import adaptive_ashrae
from pythermalcomfort.utilities import running_mean_outdoor_temperature

import json
import time
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, send_from_directory


app = Flask(__name__)


@app.route('/')
def index():
    print('Request for index page received')
    return render_template('index.html')


@app.route('/cal/', methods=['GET'])
def home_page():
    data_set = {'page': 'Home', 'Time': time.time()}
    user_query = str(request.args.get('temp'))
    temp = float(user_query)
    result = pmv_ppd(tdb=temp, tr=temp, vr=0.1, rh=50,
                     met=1.1, clo=0.5, standard="ASHRAE")

    json_dump = json.dumps(result)
    return json_dump


dailyTemperature = [20, 27, 28, 22]
currentIndex: int = 0


def ex1(temp):
    global currentIndex
    dailyTemperature[currentIndex] = temp
    if (currentIndex == 3):
        currentIndex = 0
    else:
        currentIndex = currentIndex + 1


@app.route('/adaptivecal/', methods=['GET'])
def adaptive_cal():

    user_query_temp = str(request.args.get('temp'))
    user_query_humid = str(request.args.get('humid'))
    temp = float(user_query_temp)
    humid = float(user_query_humid)
    ex1(temp)
    mean_out_temp = running_mean_outdoor_temperature(
        dailyTemperature, alpha=0.8, units='SI')
    print('-----> ' + str(mean_out_temp) + '---- temp = ' + str(temp) + '---- humid = ' + str(humid))
    result_adaptive = adaptive_ashrae(
        tdb=temp + 1, tr=temp, t_running_mean=mean_out_temp, v=0.1)

    result_pmv_ppd = pmv_ppd(tdb=temp, tr=temp, vr=0.1, rh=humid,
                             met=1.1, clo=0.5, standard="ASHRAE")

    lowval = result_adaptive["tmp_cmf_90_low"]
    upval = result_adaptive["tmp_cmf_90_up"]
    pmv = result_pmv_ppd['pmv']
    ppd = result_pmv_ppd['ppd']

    print(str(lowval) + "  " + str(upval))

    json_obj = {
        "tmp_low": lowval,
        "tmp_up": upval,
        "pmv": pmv,
        "ppd": ppd
    }

    json_dump = json.dumps(json_obj)
    return json_dump


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


@app.route('/hello', methods=['POST'])
def hello():
    name = request.form.get('name')

    if name:
        print('Request for hello page received with name=%s' % name)
        return render_template('hello.html', name=name)
    else:
        print('Request for hello page received with no name or blank name -- redirecting')
        return redirect(url_for('index'))


if __name__ == '__main__':
    app.run()
