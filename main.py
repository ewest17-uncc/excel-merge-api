import pandas as pd
from googletrans import Translator
from yandex.Translater import Translater
from flask import Flask, request, jsonify, send_file, render_template
import os
from io import BytesIO
from flask_cors import CORS, cross_origin

app = Flask(__name__)
CORS(app, support_credentials=True)
app.config['CORS_HEADERS'] = 'Content-Type'

def translate_to_russian(text, service='google'):
    if service == 'google':
        try:
            translator = Translator()
            print('CURRENTLY TRANSLATING: ', text, ' INTO RUSSIAN')
            translation = translator.translate(text, dest='ru')
            return translation.text
        except Exception as e:
            print('FAILED WITH ERROR: ', e)
    elif service == 'yandex':
        translater = Translater()
        # print('CURRENTLY TRANSLATING: ', text, ' INTO RUSSIAN')
        api_key = os.environ['YANDEX_API_KEY']
        # print('API KEY: ', api_key)
        translater.set_text(text)
        translater.set_key(api_key)
        translater.set_from_lang('en')
        translater.set_to_lang('ru')
        return translater.translate()
        # return 'Placeholder'
    else:
        raise ValueError("Invalid translation service. Use 'google' or 'yandex'.")

def merge_and_translate_excel_files(files, translation_service='google', selected_indicator='', vpr=''):
    dfs = []
    first_file_name = list(files.values())[0].filename

    for key in files.keys():
        # Read the relevant data from the file, skipping the first 4 rows
        df = pd.read_excel(files[key], skiprows=4, usecols=["CAS Registry Number", "CAS Index Name"])

        # Append the dataframe to the list
        dfs.append(df)

    # Concatenate all dataframes in the list
    combined_df = pd.concat(dfs, ignore_index=True)

    total_rows = len(combined_df)
    rows_processed = 0

    # Translate the "CAS Index Name" column to Russian (API CALL FOR EACH LINE)
    combined_df['CAS Index Name (Russian)'] = combined_df['CAS Index Name'].apply(lambda x: translate_to_russian(x, translation_service))
    combined_df['Indicator'] = selected_indicator
    combined_df['ВПР'] = vpr
    combined_df = combined_df.drop(columns=['CAS Index Name'])
    combined_df = combined_df[['CAS Index Name (Russian)', 'CAS Registry Number', 'Indicator', 'ВПР']]

    # Write the translated dataframe to a new Excel file
    return combined_df, first_file_name

@app.route('/')
@cross_origin()
def home():
    return render_template('index.html')

@app.route('/test', methods=['GET'])
@cross_origin()
def test():
    return 'Test Successful', 200

# @app.after_request
# def after_request(response):
#   response.headers.add('Access-Control-Allow-Origin', '*')
#   response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
#   response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
#   return response

@app.route('/merge_excel', methods=['POST'])
@cross_origin()
def merge_excel_api():
    try:
        files = request.files
        translation_service = os.environ['TRANSLATION_SERVICE']
        selected_indicator = request.form.get('selectedIndicator', '')
        vpr = request.form.get('VPR', '')

        # Perform the merge and translation
        result_df, first_file_name = merge_and_translate_excel_files(files, translation_service=translation_service, selected_indicator=selected_indicator, vpr=vpr)

        # Save the result to a BytesIO object
        output_buffer = BytesIO()
        with pd.ExcelWriter(output_buffer, engine='xlsxwriter') as writer:
            result_df.to_excel(writer, index=False, sheet_name='Sheet1')
            workbook = writer.book
            worksheet = writer.sheets['Sheet1']

            for i, col in enumerate(result_df.columns):
                max_len = max(result_df[col].astype(str).apply(len).max(), len(col)) + 2
                worksheet.set_column(i, i, max_len)

        output_buffer.seek(0)

        combined_file_name = f"{first_file_name.replace('.xlsx', '')}_combined.xlsx"

        response = send_file(
            output_buffer,
            download_name=combined_file_name,
            as_attachment=True,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response.headers["Access-Control-Expose-Headers"] = "Content-Disposition"
        response.headers["Content-Disposition"] = f"attachment;filename={combined_file_name}"

        return response
    except Exception as e:
        # return jsonify({'success': False, 'error_message': str(e)})
        print('ERROR: ', str(e))
        return "Merge Failed", 400

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)