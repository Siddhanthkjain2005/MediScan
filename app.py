from flask import Flask, request, render_template, jsonify
import os
from werkzeug.utils import secure_filename
from medicine_extractor import MediScanExtractor
import time
from medicine_safety import MedicineSafetyChecker

# Instantiate ONCE globally (so it loads the CSV just once)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, 'medicine_safety.csv')

print("Loading medicine safety DB from:", CSV_PATH)
safety_checker = MedicineSafetyChecker(CSV_PATH)

app = Flask(__name__)

# Configuration
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}

# Initialize extractor (load model once)
print("=" * 60)
print("🏥 MediScan - AI Medicine Name Extractor")
print("=" * 60)
extractor = MediScanExtractor()
print("=" * 60)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Render main page"""
    return render_template('index.html')

@app.route('/api/extract', methods=['POST'])
def extract_medicine():
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'success': False, 'error': 'Invalid file type.  Please upload an image.'}), 400

    try:
        filename = secure_filename(file.filename)
        timestamp = str(int(time.time()))
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        print(f"\n📥 New image uploaded: {filename}")

        # Process image to extract medicine name etc
        result = extractor.process_image(filepath)

        # ------ SAFETY CHECK ------
        if result.get('success') and result.get('best_match'):
            extracted_name = result['best_match']['name']
            safety_result = safety_checker.check_safety(extracted_name)
        else:
            safety_result = {'found': False, 'message': "No medicine name recognized, safety check skipped."}

        result['safety'] = safety_result
        # Include image for preview if you want
        result['image_url'] = f"/static/uploads/{filename}"

        if result['success']:
            print(f"✅ Processing complete!")
            if result['best_match']:
                print(f"🏆 Best Match: {result['best_match']['name']} ({result['best_match']['confidence']}%)")
        else:
            print(f"❌ Error: {result.get('error', 'Unknown error')}")

        return jsonify(result)

    except Exception as e:
        print(f"❌ Server Error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'model':  'loaded'})

if __name__ == '__main__':
    # Create upload folder if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    print("\n🌐 Starting web server...")
    print("📱 Open your browser and go to: http://localhost:8080")
    print("=" * 60 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=8080)