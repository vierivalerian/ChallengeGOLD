import re
import pandas as pd
from flask import Flask, jsonify, json

from flask import request
from flasgger import Swagger, LazyString, LazyJSONEncoder
from flasgger import swag_from
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory

col_names = ["Tweet","HS","Abusive","HS_Individual","HS_Group","HS_Religion","HS_Race","HS_Physical","HS_Gender","HS_Other","HS_Weak","HS_Moderate","HS_Strong"]
data = pd.read_csv('./data/data.csv', sep='|', names = col_names, encoding='latin-1')

kamus_alay = pd.read_csv('./data/new_kamusalay.csv', encoding='latin-1',header=None)
kamus_alay_list_0 = kamus_alay[0].tolist()
kamus_alay_list_1 = kamus_alay[1].tolist()

abusive = pd.read_csv('./data/abusive.csv', encoding='latin-1')
abusive_list = abusive['ABUSIVE'].tolist()

factory = StemmerFactory()
stemmer = factory.create_stemmer()

def lowercase(text):
    return text.lower()

def remove_char(text):
    text = re.sub('\n',' ',text)
    text = re.sub('rt',' ',text)
    text = re.sub('user',' ',text)
    text = re.sub('  +',' ',text)
    return text


def remove_numbers(text):
    text = re.sub(r'\b\d+\b', ' ', text)
    text = re.sub(r'\s\d+\s', ' ', text)
    text = re.sub(r'\s\d+', ' ', text)
    text = re.sub(r'\d\s', ' ', text)
    return text

def remove_alphanumeric(text):
    text = re.sub('[^0-9a-zA-Z]+',' ', text)
    text = re.sub(r'[\\x]+[a-z0-9]{2}','', text)
    return text

alay_dict_map = dict(zip(kamus_alay[0], kamus_alay[1]))
def normalize_alay(text):
    return ' '.join([alay_dict_map[word] if word in alay_dict_map else word for word in text.split(' ')])

def remove_abusive(text):
    text = ' '.join(['' if word in abusive.ABUSIVE.values else word for word in text.split(' ')])
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    return text

def stemming(text):
    return stemmer.stem(text)

def preprocess(text):
    text = lowercase(text)
    text = remove_alphanumeric(text)
    text = remove_numbers(text)
    text = remove_char(text)
    text = normalize_alay(text)
    text = remove_abusive(text)
    text = stemming(text)
    return text

data['Tweet'] = data['Tweet'].apply(preprocess)
app = Flask(__name__)
app.json_encoder = LazyJSONEncoder
swagger_template = {
    'info' : {
        'title': 'API for Data Cleansing',
        'version': '1.0.0',
        'description': 'Dokumentasi API for Data Cleansing',
        },
    'host' : '127.0.0.1:5000'
}

swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'docs',
            "route": '/docs.json',
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/docs/"
}
swagger = Swagger(app, template=swagger_template,
                  config=swagger_config)


@swag_from("docs/text_processing.yml", methods=['POST'])
@app.route('/text-processing', methods=['POST'])
def text_processing():

    text = request.form.get('text')

    json_response = {
        'status_code': 200,
        'description': "Teks yang sudah diproses",
        'data': re.sub(r'[^a-zA-Z0-9]', ' ', text),
    }

    response_data = jsonify(json_response)
    return response_data


@swag_from("docs/text_processing_file.yml", methods=['POST'])
@app.route('/text-processing-file', methods=['POST'])
def text_processing_file():

    file = request.files.getlist('file')[0]
    df = pd.read_csv(file)
    texts = df.text.to_list()

    cleaned_text = []
    for text in texts:
        cleaned_text.append(re.sub(r'[^a-zA-Z0-9]', ' ', text))

    json_response = {
        'status_code': 200,
        'description': "Teks yang sudah diproses",
        'data': cleaned_text,
    }

    response_data = jsonify(json_response)
    return response_data


if __name__ == '__main__':
   app.run()