import os
from flask import Flask, render_template, request
from .models.A_convert_pdf_to_text import clean_up
from .models.B_preprocess_and_glue_text import preprocess_text, glue_text
from .models.C_predict_R2M import extract_predictions

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(APP_ROOT) + '/static/uploads/'
ALLOWED_EXTENSIONS = set(['pdf'])

app = Flask(__name__)



def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_result(path):

    # predict new paper
    cleaned_text = clean_up(path)
    preprocessed_text = preprocess_text(cleaned_text)
    text = glue_text(preprocessed_text)
    entropy_score_quantile = extract_predictions(text)

    return entropy_score_quantile


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            return render_template('upload.html', msg='No file selected')
        file = request.files['file']
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            return render_template('upload.html', msg='No file selected')

        if file and allowed_file(file.filename):
            path = UPLOAD_FOLDER + file.filename
            file.save(path)
            # predict
            entropy_score_quantile = get_result(path)
            return render_template('upload.html',
                                   file_name=file.filename,
                                   score=entropy_score_quantile
                                   # tables=[df_prediction_top_three.to_html(classes='data')],
                                   # titles=['na']
                                   )
    elif request.method == 'GET':
        return render_template('upload.html')


if __name__ == '__main__':
    app.run(debug=True)
