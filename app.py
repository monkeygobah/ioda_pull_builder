from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
import os
import io
import uuid

app = Flask(__name__)

CSV_FILE_PATH = 'de_images_diagnosis_joined.csv'  
df = pd.read_csv(CSV_FILE_PATH, on_bad_lines='skip', delimiter='\\t', engine='python')

filtered_data_storage = {}

@app.route('/')
def index():
    imaging_types = get_imaging_types(df)  
    print(imaging_types)
    return render_template('index.html', imaging_types=imaging_types)  

def get_disease_list(df):
    disease_set = set()
    for diseases in df['DiagnosisCodeDesc'].dropna():
        disease_set.update(disease.strip() for disease in diseases.split('|'))
    return sorted(disease_set)

def get_imaging_types(df):
    return df['img_type_abrv'].dropna().unique().tolist()

disease_list = get_disease_list(df)
imaging_types = get_imaging_types(df)

@app.route('/autocomplete')
def autocomplete():
    search = request.args.get('q', '').lower()
    results = [disease for disease in disease_list if search in disease.lower()]
    return jsonify(results)

# Filter the DataFrame based on user selections and generate statistics
@app.route('/filter', methods=['POST'])
def filter():
    selected_diseases = request.form.getlist('diseases[]')
    selected_img_types = request.form.getlist('img_types[]')

    filtered_df = df.copy()

    def match_diseases(row):
        row_diseases = [d.strip() for d in str(row['DiagnosisCodeDesc']).split('|')]
        return any(disease in row_diseases for disease in selected_diseases)

    def match_img_types(row):
        return row['img_type_abrv'] in selected_img_types

    # Apply filtering conditions
    if selected_diseases:
        filtered_df = filtered_df[filtered_df.apply(match_diseases, axis=1)]
    if selected_img_types:
        filtered_df = filtered_df[filtered_df.apply(match_img_types, axis=1)]

    if filtered_df.empty:
        return "No records found for the selected criteria.", 404


    # Calculate statistics
    stats = calculate_statistics(filtered_df, selected_diseases)

    # Generate a session ID to store the filtered data temporarily
    session_id = str(uuid.uuid4())
    filtered_data_storage[session_id] = filtered_df

    # Create a CSV file for download preview
    csv_buffer = io.StringIO()
    filtered_df.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)

    response = {
        'session_id': session_id,
        'csv_data': csv_buffer.getvalue(),
        'stats': stats
    }

    return jsonify(response)

@app.route('/download_filtered', methods=['POST'])
def download_filtered():
    session_id = request.form.get('session_id')

    if session_id not in filtered_data_storage:
        return "Session expired or invalid.", 400

    # Retrieve the filtered data
    filtered_df = filtered_data_storage.pop(session_id)

    # Prepare CSV data for download
    csv_buffer = io.StringIO()
    filtered_df.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)

    return send_file(io.BytesIO(csv_buffer.getvalue().encode('utf-8')),
                     mimetype='text/csv',
                     download_name='filtered_data.csv',
                     as_attachment=True)


def calculate_statistics(filtered_df, selected_diseases):
    stats = {}

    # Number of images for each disease (with and without comorbidities)
    for disease in selected_diseases:
        # Set regex=False to avoid interpreting special characters in disease names
        disease_images = filtered_df[filtered_df['DiagnosisCodeDesc'].str.contains(disease, na=False, regex=False)]
        unique_mrns = disease_images['MRN'].nunique()
        stats[disease] = {
            'num_images': len(disease_images),
            'num_unique_mrn': unique_mrns,
            'percentage_unique_mrn': (unique_mrns / len(disease_images)) * 100 if len(disease_images) > 0 else 0
        }

    # Number of images that contain all selected diseases (with comorbidities)
    all_disease_images = filtered_df[filtered_df['DiagnosisCodeDesc'].fillna('').apply(
        lambda x: all(d in x for d in selected_diseases) if isinstance(x, str) else False
    )]
    all_unique_mrns = all_disease_images['MRN'].nunique()
    stats['all_diseases'] = {
        'num_images': len(all_disease_images),
        'num_unique_mrn': all_unique_mrns,
        'percentage_unique_mrn': (all_unique_mrns / len(all_disease_images)) * 100 if len(all_disease_images) > 0 else 0
    }

    # Number of images with only the selected diseases (no comorbidities)
    only_selected_diseases_images = filtered_df[filtered_df['DiagnosisCodeDesc'].fillna('').apply(
        lambda x: set(x.split('|')) == set(selected_diseases) if isinstance(x, str) else False
    )]
    only_selected_unique_mrns = only_selected_diseases_images['MRN'].nunique()
    stats['only_selected_diseases'] = {
        'num_images': len(only_selected_diseases_images),
        'num_unique_mrn': only_selected_unique_mrns,
        'percentage_unique_mrn': (only_selected_unique_mrns / len(only_selected_diseases_images)) * 100 if len(only_selected_diseases_images) > 0 else 0
    }

    # For each disease, the percentage of different imaging modalities
    imaging_modality_stats = {}
    for disease in selected_diseases:
        # Again, set regex=False for str.contains() to avoid regex interpretation
        disease_images = filtered_df[filtered_df['DiagnosisCodeDesc'].str.contains(disease, na=False, regex=False)]
        modality_counts = disease_images['img_type_abrv'].value_counts(normalize=True) * 100
        imaging_modality_stats[disease] = modality_counts.to_dict()

    stats['imaging_modality_stats'] = imaging_modality_stats

    return stats



if __name__ == '__main__':
    app.run(debug=True)
