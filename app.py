from flask import Flask, request, jsonify, render_template
from analyzers import analyze_text, analyze_url, analyze_image

app = Flask(__name__, template_folder='templates')

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/analyze', methods=['POST'])
def analyze():
    mode = request.form.get('mode')
    verdict, explanation = '', ''
    print(mode)
    if mode == 'text':
        text = request.form.get('text')
        if not text:
            return jsonify({'error': 'Text input is required'}), 400
        verdict, explanation = analyze_text(text)

    elif mode == 'url':
        url = request.form.get('url')
        if not url:
            return jsonify({'error': 'URL input is required'}), 400
        verdict, explanation = analyze_url(url)

    elif mode == 'image':
        image = request.files.get('image')
        print(request)
        if not image:
            return jsonify({'error': 'Image file is required'}), 400
        verdict, explanation = analyze_image(image)

    else:
        return jsonify({'error': 'Invalid mode'}), 400

    return jsonify({'result': verdict, 'explanation': explanation})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

